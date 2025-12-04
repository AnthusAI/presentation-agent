import re
import yaml
import cssutils
import logging
import io

# Configure cssutils to be quiet by default
cssutils.log.setLevel(logging.CRITICAL)

class DeckValidator:
    @staticmethod
    def validate_css(css_content: str) -> list:
        """
        Validates CSS content and returns a list of error messages.
        Returns empty list if valid.
        """
        if not css_content or not css_content.strip():
            return []

        # Capture cssutils logs
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        
        # Create a dedicated logger
        logger = logging.getLogger('CSSVALIDATOR')
        logger.setLevel(logging.ERROR)
        # Clear existing handlers
        logger.handlers = []
        logger.addHandler(handler)
        
        # Redirect cssutils log
        # cssutils uses a global log object, we need to swap it or configure it
        # The safest way with cssutils is to inject our logger
        if hasattr(cssutils.log, 'getLog'):
            old_log = cssutils.log.getLog()
        else:
            # Fallback for newer cssutils versions where getLog is removed
            old_log = cssutils.log._log
            
        cssutils.log.setLog(logger)
        
        try:
            parser = cssutils.CSSParser(loglevel=logging.ERROR)
            parser.parseString(css_content)
        except Exception as e:
            return [str(e)]
        finally:
            # Restore log
            cssutils.log.setLog(old_log)
            
        output = log_capture.getvalue().strip()
        if not output:
            return []
            
        # Filter errors
        errors = []
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Ignore "Property: Invalid value..." errors which often happen for modern CSS (grid, variables, etc)
            if "Property: Invalid value" in line:
                continue
            errors.append(line)
            
        return errors

    @staticmethod
    def validate_and_summarize(content: str) -> dict:
        """
        Validates the deck content and returns a summary if valid.
        Returns a dictionary with keys:
        - valid: bool
        - error: str (if invalid)
        - summary: str (if valid)
        """
        
        # 1. Validate Frontmatter
        lines = content.split('\n')
        if not lines:
            return {'valid': True, 'summary': "Empty file", 'error': None}
            
        has_frontmatter = lines[0].strip() == '---'
        frontmatter_end_index = -1
        
        if has_frontmatter:
            # Look for closing ---
            # We start looking from line 1
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == '---':
                    frontmatter_end_index = i
                    break
            
            if frontmatter_end_index == -1:
                return {
                    'valid': False, 
                    'error': "Frontmatter not closed. The file starts with '---' but does not have a closing '---'. This will cause the configuration to be visible in the presentation.",
                    'summary': None
                }

            # 1.5 Validate CSS if present in frontmatter
            fm_text = '\n'.join(lines[1:frontmatter_end_index])
            try:
                frontmatter = yaml.safe_load(fm_text)
                if frontmatter and isinstance(frontmatter, dict) and 'style' in frontmatter:
                    css_errors = DeckValidator.validate_css(str(frontmatter['style']))
                    if css_errors:
                         return {
                            'valid': False,
                            'error': "CSS Error in frontmatter:\n" + "\n".join(css_errors),
                            'summary': None
                         }
            except yaml.YAMLError as e:
                return {
                    'valid': False,
                    'error': f"Invalid YAML frontmatter: {e}",
                    'summary': None
                }
        
        # 2. Generate Summary
        # We need to split slides. 
        # Marp slides are separated by '---' on a line by itself.
        # We need to handle the frontmatter case so we don't split there.
        
        slide_content_start = 0
        if has_frontmatter:
            slide_content_start = frontmatter_end_index + 1
            
        # Reconstruct the body to split by slides
        # Note: '---' is both frontmatter delimiter and slide separator.
        # If we have frontmatter, the first slide starts after it.
        # If we don't, the first slide starts at the beginning.
        # Subsequent slides are separated by '\n---\n' (roughly).
        
        body_lines = lines[slide_content_start:]
        
        # A robust way is to iterate lines and look for '---'.
        slides = []
        current_slide_lines = []
        
        for line in body_lines:
            if line.strip() == '---':
                # End of current slide, start of new one
                slides.append('\n'.join(current_slide_lines))
                current_slide_lines = []
            else:
                current_slide_lines.append(line)
        
        # Append the last slide
        slides.append('\n'.join(current_slide_lines))
        
        summary_lines = []
        summary_lines.append(f"Total Slides: {len(slides)}")
        
        for i, slide_text in enumerate(slides):
            # Find H1
            h1_match = re.search(r'^#\s+(.+)$', slide_text, re.MULTILINE)
            title = h1_match.group(1).strip() if h1_match else "No Title"
            
            # Count images
            # Markdown images: ![alt](src)
            # HTML images: <img src="...">
            md_images = len(re.findall(r'!\[.*?\]\(.*?\)', slide_text))
            html_images = len(re.findall(r'<img\s+[^>]*src=[\'"].*?[\'"]', slide_text, re.IGNORECASE))
            image_count = md_images + html_images
            
            summary_lines.append(f"Slide {i+1}: Title='{title}', Images={image_count}")
            
        return {
            'valid': True,
            'error': None,
            'summary': "Summary:\n" + "\n".join(summary_lines)
        }

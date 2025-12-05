import os
import json
import time
import re
import yaml
from datetime import datetime

class PresentationManager:
    def __init__(self, root_dir=None):
        if root_dir:
            self.root_dir = root_dir
        else:
            # Priority order: VIBE_PRESENTATION_ROOT env var, local presentations/ folder, ~/.vibe_presentation
            env_root = os.environ.get('VIBE_PRESENTATION_ROOT')
            if env_root:
                self.root_dir = env_root
            else:
                local_presentations = os.path.abspath("presentations")
                if os.path.exists(local_presentations):
                    self.root_dir = local_presentations
                else:
                    self.root_dir = os.path.expanduser("~/.vibe_presentation")
        
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)
        
        # Templates directory
        # 1. Check inside root_dir (useful for tests or self-contained storage)
        internal_templates = os.path.join(self.root_dir, "templates")
        if os.path.exists(internal_templates):
             self.templates_dir = internal_templates
        else:
             # 2. Check local templates folder (useful for repo usage)
             local_templates = os.path.abspath("templates")
             if os.path.exists(local_templates):
                 self.templates_dir = local_templates
             else:
                 # Default back to internal
                 self.templates_dir = internal_templates

    def create_presentation(self, name, description="", template=None):
        presentation_dir = os.path.join(self.root_dir, name)
        if os.path.exists(presentation_dir):
            raise ValueError(f"Presentation '{name}' already exists.")
        
        # Default aspect ratio
        aspect_ratio = "4:3"
        
        if template:
            # Create from template
            template_path = os.path.join(self.templates_dir, template)
            if not os.path.exists(template_path):
                raise ValueError(f"Template '{template}' not found.")
            
            import shutil
            shutil.copytree(template_path, presentation_dir)
            
            # Update metadata - preserve ALL template fields
            metadata_path = os.path.join(presentation_dir, "metadata.json")
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
            
            # Preserve existing aspect ratio if present in template metadata
            if "aspect_ratio" in metadata:
                aspect_ratio = metadata["aspect_ratio"]
            
            # Preserve important template fields before updating
            preserved_instructions = metadata.get("instructions", "")
            preserved_image_style = metadata.get("image_style", {})
            preserved_typography = metadata.get("typography", {})
            preserved_colors = metadata.get("colors", {})
            preserved_design_opinions = metadata.get("design_opinions", {})
            
            # Update only specific fields, preserving all others
            metadata.update({
                "name": name,
                "description": description,
                "aspect_ratio": aspect_ratio,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            
            # Explicitly restore preserved fields (defensive programming)
            if preserved_instructions:
                metadata["instructions"] = preserved_instructions
            if preserved_image_style:
                metadata["image_style"] = preserved_image_style
            if preserved_typography:
                metadata["typography"] = preserved_typography
            if preserved_colors:
                metadata["colors"] = preserved_colors
            if preserved_design_opinions:
                metadata["design_opinions"] = preserved_design_opinions
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Explicitly ensure template-specific images are copied (style.png, background.png, etc.)
            # copytree should have copied them, but we verify and copy if missing (defensive)
            template_images_dir = os.path.join(template_path, "images")
            presentation_images_dir = os.path.join(presentation_dir, "images")
            os.makedirs(presentation_images_dir, exist_ok=True)
            
            # Copy style.png if it exists (convention-based style reference)
            # Always copy to ensure it's present (copytree should have copied it, but be defensive)
            template_style_png = os.path.join(template_images_dir, "style.png")
            presentation_style_png = os.path.join(presentation_images_dir, "style.png")
            if os.path.exists(template_style_png):
                shutil.copy2(template_style_png, presentation_style_png)
            
            # Copy background.png if it exists (for slide backgrounds)
            # Always copy to ensure it's present (copytree should have copied it, but be defensive)
            template_background_png = os.path.join(template_images_dir, "background.png")
            presentation_background_png = os.path.join(presentation_images_dir, "background.png")
            if os.path.exists(template_background_png):
                shutil.copy2(template_background_png, presentation_background_png)
            
            # Copy default layouts if template doesn't have layouts.md
            # NOTE: We should NOT modify the deck file if the template already has a complete deck
            # The template's deck.marp.md should be used as-is
            layouts_path = os.path.join(presentation_dir, "layouts.md")
            if not os.path.exists(layouts_path):
                # Only copy default layouts if template doesn't have its own layouts
                # But DON'T merge CSS into the deck - the template's deck is already complete
                default_layouts_path = os.path.join(self.templates_dir, "default-layouts.md")
                if not os.path.exists(default_layouts_path):
                    local_templates = os.path.abspath("templates")
                    default_layouts_path = os.path.join(local_templates, "default-layouts.md")
                if os.path.exists(default_layouts_path):
                    dest_path = os.path.join(presentation_dir, "layouts.md")
                    shutil.copy2(default_layouts_path, dest_path)
                    # DO NOT merge CSS - template deck is already complete
            else:
                # Template has layouts, but don't merge - template deck is already complete
                pass
            
            # Copy system images based on template metadata
            include_system_images = metadata.get('include_system_images', None)
            self._copy_system_images(presentation_dir, include_system_images)
                
            return metadata
        else:
            # Create default
            os.makedirs(presentation_dir)
            
            metadata = {
                "name": name,
                "description": description,
                "aspect_ratio": aspect_ratio,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(os.path.join(presentation_dir, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
                
            # Create a default Marp deck
            with open(os.path.join(presentation_dir, "deck.marp.md"), "w") as f:
                f.write(f"""---
marp: true
theme: default
size: {aspect_ratio}
paginate: true
---

# {name}

{description}

---

# Slide 1

- Bullet 1
- Bullet 2
""")
            
            # Copy default layouts
            self._copy_default_layouts(presentation_dir)
            
            # Copy system placeholder images
            self._copy_system_images(presentation_dir)
            
            return metadata

    def _copy_default_layouts(self, presentation_dir):
        """Copy default layouts to a presentation directory."""
        import shutil
        
        # Look for default layouts in templates directory
        default_layouts_path = os.path.join(self.templates_dir, "default-layouts.md")
        
        # Fallback to repo templates folder if not in templates_dir
        if not os.path.exists(default_layouts_path):
            # Try local templates folder
            local_templates = os.path.abspath("templates")
            default_layouts_path = os.path.join(local_templates, "default-layouts.md")
        
        if os.path.exists(default_layouts_path):
            dest_path = os.path.join(presentation_dir, "layouts.md")
            shutil.copy2(default_layouts_path, dest_path)
            
            # Merge layouts CSS into deck.marp.md
            self._merge_layouts_css(presentation_dir, default_layouts_path)
    
    def _copy_system_images(self, presentation_dir, include_system_images=None):
        """Copy system placeholder images to presentation directory.
        
        Args:
            presentation_dir: Destination presentation directory
            include_system_images: Override from template metadata (True/False/None)
                - True: Always copy system images (even if template has images)
                - False: Never copy system images
                - None: Copy only if no images folder exists
        """
        import shutil
        
        # Determine images destination
        images_dir = os.path.join(presentation_dir, "images")
        
        # Check if presentation already has images
        has_images = os.path.exists(images_dir) and os.listdir(images_dir)
        
        # Decide whether to copy based on include_system_images parameter
        if include_system_images is False:
            return  # Explicitly don't want system images
        elif include_system_images is True:
            should_copy = True  # Explicitly want system images
        else:
            should_copy = not has_images  # Copy only if no images exist
        
        if not should_copy:
            return
        
        # Find system images directory
        system_images_path = os.path.join(self.templates_dir, "system-images")
        
        # Fallback to repo templates folder if not in templates_dir
        if not os.path.exists(system_images_path):
            local_templates = os.path.abspath("templates")
            system_images_path = os.path.join(local_templates, "system-images")
        
        if not os.path.exists(system_images_path):
            return  # No system images available
        
        # Create images directory if it doesn't exist
        os.makedirs(images_dir, exist_ok=True)
        
        # Copy all placeholder images
        for filename in os.listdir(system_images_path):
            if filename.startswith('placeholder-') and filename.endswith('.png'):
                src = os.path.join(system_images_path, filename)
                dst = os.path.join(images_dir, filename)
                if not os.path.exists(dst):  # Don't overwrite existing files
                    shutil.copy2(src, dst)
    
    def _extract_layouts_css(self, layouts_path):
        """Extract CSS from layouts.md front matter."""
        if not os.path.exists(layouts_path):
            return None
        
        try:
            with open(layouts_path, "r") as f:
                lines = f.readlines()
            
            # Check if file starts with front matter
            if not lines or not lines[0].strip() == '---':
                return None
            
            # Find the closing --- of front matter
            front_matter_end = -1
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    front_matter_end = i
                    break
            
            if front_matter_end == -1:
                return None
            
            # Extract front matter lines
            front_matter_lines = lines[1:front_matter_end]
            
            # Find and extract style block
            css_lines = []
            in_style_block = False
            
            for line in front_matter_lines:
                if line.startswith('style:'):
                    in_style_block = True
                    continue
                elif in_style_block:
                    # Check if this is the start of a new top-level key
                    if line and not line[0].isspace() and ':' in line:
                        break
                    # This is part of the style block - remove 2-space indentation
                    if line.startswith('  '):
                        css_lines.append(line[2:].rstrip())
                    elif not line.strip():  # Empty line
                        css_lines.append('')
            
            if css_lines:
                css = '\n'.join(css_lines).strip()
                return css
            
            return None
        except Exception as e:
            print(f"Error extracting layouts CSS: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _merge_layouts_css(self, presentation_dir, layouts_path):
        """Merge layouts CSS into deck.marp.md."""
        deck_path = os.path.join(presentation_dir, "deck.marp.md")
        
        if not os.path.exists(deck_path):
            return
        
        # Extract CSS from layouts
        layouts_css = self._extract_layouts_css(layouts_path)
        if not layouts_css:
            return
        
        try:
            with open(deck_path, "r") as f:
                lines = f.readlines()
            
            # Check if deck has front matter
            if not lines or not lines[0].strip() == '---':
                # No front matter, add one with the layouts CSS
                new_lines = ['---\n', 'marp: true\n', 'style: |\n']
                for css_line in layouts_css.split('\n'):
                    new_lines.append(f'  {css_line}\n')
                new_lines.append('---\n\n')
                new_lines.extend(lines)
                
                with open(deck_path, "w") as f:
                    f.writelines(new_lines)
                return
            
            # Find the end of front matter
            front_matter_end = -1
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    front_matter_end = i
                    break
            
            if front_matter_end == -1:
                return
            
            # Check if there's already a style block in front matter
            has_style = False
            style_line_idx = -1
            for i in range(1, front_matter_end):
                if lines[i].startswith('style:'):
                    has_style = True
                    style_line_idx = i
                    break
            
            if has_style:
                # Merge layouts CSS with existing styles
                # Find the end of the existing style block
                style_end_idx = front_matter_end
                for i in range(style_line_idx + 1, front_matter_end):
                    # Check if this line starts a new top-level key (not indented)
                    if lines[i].strip() and not lines[i][0].isspace() and ':' in lines[i]:
                        style_end_idx = i
                        break
                
                # Insert layouts CSS before the style block ends
                style_lines = []
                for css_line in layouts_css.split('\n'):
                    style_lines.append(f'  {css_line}\n')
                
                # Insert the new CSS lines
                new_lines = lines[:style_end_idx] + style_lines + lines[style_end_idx:]
            else:
                # Add style block before the closing ---
                style_lines = ['style: |\n']
                for css_line in layouts_css.split('\n'):
                    style_lines.append(f'  {css_line}\n')
                
                # Insert style lines before the closing ---
                new_lines = lines[:front_matter_end] + style_lines + lines[front_matter_end:]
            
            with open(deck_path, "w") as f:
                f.writelines(new_lines)
                
        except Exception as e:
            print(f"Error merging layouts CSS: {e}")
            import traceback
            traceback.print_exc()
    
    def list_templates(self):
        templates = []
        if not os.path.exists(self.templates_dir):
            return []
        
        # Directories to exclude from template list
        excluded_dirs = {'system-images', 'default-layouts.md'}
            
        for name in sorted(os.listdir(self.templates_dir)):
            # Skip excluded directories and files
            if name in excluded_dirs or name.startswith('.'):
                continue
                
            path = os.path.join(self.templates_dir, name)
            if os.path.isdir(path):
                metadata_path = os.path.join(path, "metadata.json")
                # Only include directories that have metadata.json (actual templates)
                if os.path.exists(metadata_path):
                    desc = ""
                    try:
                        with open(metadata_path, "r") as f:
                            data = json.load(f)
                            desc = data.get('description', '')
                    except: 
                        pass
                    templates.append({"name": name, "description": desc})
        return templates

    def list_presentations(self):
        presentations = []
        if not os.path.exists(self.root_dir):
            return []
            
        for name in os.listdir(self.root_dir):
            path = os.path.join(self.root_dir, name)
            if os.path.isdir(path):
                metadata_path = os.path.join(path, "metadata.json")
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                            # Ensure name matches directory name to avoid deletion issues
                            metadata['name'] = name
                            presentations.append(metadata)
                    except json.JSONDecodeError:
                        continue
        
        # Sort by created_at desc
        presentations.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return presentations

    def get_presentation(self, name):
        path = os.path.join(self.root_dir, name)
        if not os.path.exists(path):
            return None
        
        metadata_path = os.path.join(path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                return json.load(f)
        return None

    def delete_presentation(self, name):
        path = os.path.join(self.root_dir, name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Presentation '{name}' not found.")
        
        import shutil
        shutil.rmtree(path)
        return True

    def delete_template(self, name):
        """Delete a template by name."""
        path = os.path.join(self.templates_dir, name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template '{name}' not found.")
        
        import shutil
        shutil.rmtree(path)
        return True

    def get_presentation_aspect_ratio(self, name):
        pres = self.get_presentation(name)
        if pres:
            return pres.get('aspect_ratio', '4:3')
        return '4:3'

    def set_presentation_aspect_ratio(self, name, aspect_ratio):
        path = os.path.join(self.root_dir, name)
        if not os.path.exists(path):
            raise ValueError(f"Presentation '{name}' not found.")
            
        # Update metadata
        metadata_path = os.path.join(path, "metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        
        metadata['aspect_ratio'] = aspect_ratio
        metadata['updated_at'] = datetime.now().isoformat()
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Update Marp file
        marp_path = os.path.join(path, "deck.marp.md")
        if os.path.exists(marp_path):
            with open(marp_path, "r") as f:
                content = f.read()
            
            # Regex to replace size: ... in front matter
            # Front matter is between first two ---
            
            # Check if size exists
            if re.search(r'^size:\s*.*$', content, re.MULTILINE):
                new_content = re.sub(r'^size:\s*.*$', f'size: {aspect_ratio}', content, flags=re.MULTILINE)
            else:
                # Insert size after theme or marp: true
                if 'theme:' in content:
                    new_content = re.sub(r'(^theme:\s*.*$)', f'\\1\nsize: {aspect_ratio}', content, flags=re.MULTILINE, count=1)
                elif 'marp: true' in content:
                    new_content = re.sub(r'(^marp: true)', f'\\1\nsize: {aspect_ratio}', content, flags=re.MULTILINE, count=1)
                else:
                    # Just add it at start of front matter?
                    new_content = content.replace('---\n', f'---\nsize: {aspect_ratio}\n', 1)
            
            with open(marp_path, "w") as f:
                f.write(new_content)
                
        return metadata
    
    def set_presentation_title(self, name, title):
        """Update the presentation title in both metadata.json and deck.marp.md front matter."""
        path = os.path.join(self.root_dir, name)
        if not os.path.exists(path):
            raise ValueError(f"Presentation '{name}' not found.")
        
        # Update metadata
        metadata_path = os.path.join(path, "metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        
        metadata['name'] = title  # Update name in metadata
        metadata['updated_at'] = datetime.now().isoformat()
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Update Marp file front matter
        marp_path = os.path.join(path, "deck.marp.md")
        if os.path.exists(marp_path):
            with open(marp_path, "r") as f:
                content = f.read()
            
            # Parse front matter
            if content.startswith('---'):
                # Find the end of front matter
                parts = content.split('\n---\n', 2)
                if len(parts) >= 2:
                    front_matter = parts[0][3:]  # Remove leading ---
                    body = '\n---\n'.join(parts[1:])
                    
                    # Parse YAML front matter
                    try:
                        fm_data = yaml.safe_load(front_matter) or {}
                    except:
                        fm_data = {}
                    
                    # Update title
                    fm_data['title'] = title
                    
                    # Reconstruct front matter
                    new_front_matter = yaml.dump(fm_data, default_flow_style=False, sort_keys=False, allow_unicode=True).strip()
                    new_content = '---\n' + new_front_matter + '\n---\n' + body
                    
                    with open(marp_path, "w") as f:
                        f.write(new_content)
        
        return self.get_presentation(name)
    
    def set_presentation_description(self, name, description):
        """Update the presentation description in both metadata.json and deck.marp.md front matter."""
        path = os.path.join(self.root_dir, name)
        if not os.path.exists(path):
            raise ValueError(f"Presentation '{name}' not found.")
        
        # Update metadata
        metadata_path = os.path.join(path, "metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        
        metadata['description'] = description
        metadata['updated_at'] = datetime.now().isoformat()
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Update Marp file front matter
        marp_path = os.path.join(path, "deck.marp.md")
        if os.path.exists(marp_path):
            with open(marp_path, "r") as f:
                content = f.read()
            
            # Parse front matter
            if content.startswith('---'):
                # Find the end of front matter
                parts = content.split('\n---\n', 2)
                if len(parts) >= 2:
                    front_matter = parts[0][3:]  # Remove leading ---
                    body = '\n---\n'.join(parts[1:])
                    
                    # Parse YAML front matter
                    try:
                        fm_data = yaml.safe_load(front_matter) or {}
                    except:
                        fm_data = {}
                    
                    # Update description
                    fm_data['description'] = description
                    
                    # Reconstruct front matter
                    new_front_matter = yaml.dump(fm_data, default_flow_style=False, sort_keys=False, allow_unicode=True).strip()
                    new_content = '---\n' + new_front_matter + '\n---\n' + body
                    
                    with open(marp_path, "w") as f:
                        f.write(new_content)
        
        return self.get_presentation(name)
    
    def duplicate_presentation(self, source_name, new_name, description=None, copy_images=True):
        source_path = os.path.join(self.root_dir, source_name)
        
        if not os.path.exists(source_path):
            raise ValueError(f"Source presentation '{source_name}' not found.")
        
        # Auto-increment folder name if it already exists
        # The folder name can differ from the metadata name
        folder_name = new_name
        counter = 2
        while os.path.exists(os.path.join(self.root_dir, folder_name)):
            folder_name = f"{new_name} {counter}"
            counter += 1
        
        new_path = os.path.join(self.root_dir, folder_name)
            
        import shutil
        
        # Copy directory
        # shutil.copytree requires destination to NOT exist
        # We might want to exclude images if copy_images is False
        
        def ignore_patterns(path, names):
            if not copy_images and path == source_path and "images" in names:
                return ["images"]
            return []
            
        shutil.copytree(source_path, new_path, ignore=ignore_patterns)
        
        # Update metadata
        metadata_path = os.path.join(new_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                
            # Store user's exact specified name in metadata, not the auto-incremented folder name
            metadata.update({
                "name": new_name,  # User's specified name, not folder_name
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            
            # Update description if provided
            if description is not None:
                metadata["description"] = description
            
            # Keep aspect_ratio, style, etc. from source
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
        
        # Update title in Marp file?
        marp_path = os.path.join(new_path, "deck.marp.md")
        if os.path.exists(marp_path):
            with open(marp_path, "r") as f:
                content = f.read()
            
            # Simple replace of title if it matches source name exactly in # Title
            # This is a bit risky, maybe just leave it?
            # Let's try to replace the first # Title if it matches
            
            # Construct regex for title
            # # Source Name
            pattern = re.compile(f"^# {re.escape(source_name)}$", re.MULTILINE)
            if pattern.search(content):
                content = pattern.sub(f"# {new_name}", content, count=1)
                with open(marp_path, "w") as f:
                    f.write(content)
        
        # Get the presentation metadata and add the folder name for reference
        result = self.get_presentation(folder_name)
        if result:
            result["_folder_name"] = folder_name
                    
        return result

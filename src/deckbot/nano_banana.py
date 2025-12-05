import os
import shutil
import time
import subprocess
import json
import base64
from io import BytesIO
import PIL.Image
from google import genai
from google.genai import types
from datetime import datetime
from rich.console import Console
from google.api_core.exceptions import ResourceExhausted

console = Console()

def generate_batch_slug(prompt, max_length=40):
    """Generate a unique slug for an image batch based on prompt and timestamp."""
    import re
    # Clean the prompt: lowercase, replace spaces/special chars with dashes
    slug = prompt.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    
    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    # Add timestamp for uniqueness
    timestamp = int(time.time() * 1000) % 100000  # Last 5 digits of ms timestamp
    slug = f"{slug}-{timestamp}"
    
    return slug

class NanoBananaClient:
    def __init__(self, presentation_context, root_dir=None):
        self.context = presentation_context
        
        if root_dir:
            root = root_dir
        else:
            env_root = os.environ.get('VIBE_PRESENTATION_ROOT')
            if env_root:
                root = env_root
            elif os.path.exists("presentations"):
                root = os.path.abspath("presentations")
            else:
                root = os.path.expanduser("~/.vibe_presentation")
            
        self.presentation_dir = os.path.join(root, presentation_context['name'])
        self.images_dir = os.path.join(self.presentation_dir, "images")
        # New drafts directory
        self.drafts_dir = os.path.join(self.presentation_dir, "drafts")
        
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        if not os.path.exists(self.drafts_dir):
            os.makedirs(self.drafts_dir)

        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        # Check for deprecated GEMINI_API_KEY
        if not self.api_key and os.getenv("GEMINI_API_KEY"):
            # Silently fall back for image generation (warning already shown by Agent)
            self.api_key = os.getenv("GEMINI_API_KEY")
        
        self.client = None
        if self.api_key:
             self.client = genai.Client(api_key=self.api_key)
             # Gemini 3 Pro Image Preview (Nano Banana Pro) - supports image generation
             self.model_name = 'gemini-3-pro-image-preview'
        
    def generate_candidates(self, prompt, status_spinner=None, progress_callback=None, aspect_ratio="1:1", resolution="2K", remix_reference_image=None, batch_metadata=None):
        """
        Generate 4 image candidates.
        
        Args:
            prompt: The image generation prompt
            status_spinner: Rich spinner for CLI mode
            progress_callback: Function(current, total, status) for web mode progress updates
            aspect_ratio: Aspect ratio for the image (e.g., "1:1", "16:9")
            resolution: Image resolution ("1K", "2K", "4K")
            remix_reference_image: Optional PIL.Image to use as remix reference (for remixing slides/images)
        """
        if status_spinner:
            status_spinner.stop() # Pause spinner for logs
            
        console.print(f"[yellow]Generating 4 candidates for: '{prompt}'...[/yellow]")
        
        # Load style from metadata and extract theme/CSS info from deck.marp.md
        metadata_path = os.path.join(self.presentation_dir, "metadata.json")
        deck_path = os.path.join(self.presentation_dir, "deck.marp.md")
        style_prompt = ""
        style_reference_path = None
        style_reference_image = None
        theme_info = ""
        design_opinions = {}
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r") as f:
                    data = json.load(f)
                    style = data.get("image_style", {})
                    design_opinions = data.get("design_opinions", {})
                    if style.get("prompt"):
                        style_prompt = style["prompt"]
            except Exception:
                pass
        
        # Load style reference image using convention-based style.png
        style_png_path = os.path.join(self.presentation_dir, "images", "style.png")
        if os.path.exists(style_png_path):
            try:
                style_reference_image = PIL.Image.open(style_png_path)
                style_reference_path = style_png_path
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load style.png: {e}[/yellow]")
        
        # Extract theme and styling information from deck.marp.md
        if os.path.exists(deck_path):
            try:
                with open(deck_path, "r") as f:
                    content = f.read()
                    # Extract front matter (between first two ---)
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 2:
                            front_matter = parts[1]
                            
                            # Extract theme
                            import re
                            theme_match = re.search(r'^theme:\s*(\w+)', front_matter, re.MULTILINE)
                            if theme_match:
                                # theme_name = theme_match.group(1)
                                # theme_info = f"Marp theme: {theme_name}. " # Removed as per user request
                                pass
                            
                            # Extract custom CSS style block
                            style_match = re.search(r'^style:\s*\|(.+?)(?=^[a-z]+:|\Z)', front_matter, re.MULTILINE | re.DOTALL)
                            if style_match:
                                css_block = style_match.group(1).strip()
                                # Extract key style info (fonts, colors)
                                font_matches = re.findall(r'font-family:\s*[\'"]?([^;\'"]+)', css_block)
                                color_matches = re.findall(r'color:\s*(#[0-9a-fA-F]{3,6})', css_block)
                                
                                if font_matches:
                                    theme_info += f"Fonts: {', '.join(font_matches)}. "
                                if color_matches:
                                    theme_info += f"Colors: {', '.join(color_matches)}. "
            except Exception:
                pass

        final_prompt = prompt
        if theme_info:
            final_prompt = f"{prompt}. {theme_info}"
        if style_prompt:
            final_prompt = f"{final_prompt} Style instructions: {style_prompt}"
        
        # Add style reference indication to prompt if we have one
        if style_reference_image:
            final_prompt = f"Using the provided style reference image as a visual style guide, generate: {final_prompt}"
        
        # Add remix reference indication to prompt if we have one
        if remix_reference_image:
            final_prompt = f"Remix the provided reference image according to: {final_prompt}"
        
        # Add aspect ratio instruction to prompt for Gemini native image generation
        aspect_ratio_instruction = {
            "1:1": "square image (1:1 aspect ratio)",
            "16:9": "wide landscape image (16:9 aspect ratio)",
            "9:16": "tall portrait image (9:16 aspect ratio)",
            "4:3": "landscape image (4:3 aspect ratio)",
            "3:4": "portrait image (3:4 aspect ratio)",
            "3:2": "landscape image (3:2 aspect ratio)",
            "2:3": "portrait image (2:3 aspect ratio)",
            "4:5": "portrait image (4:5 aspect ratio)",
            "5:4": "landscape image (5:4 aspect ratio)",
            "21:9": "ultra-wide image (21:9 aspect ratio)"
        }.get(aspect_ratio, f"image with {aspect_ratio} aspect ratio")
        
        # Construct System Instructions (Context & Style)
        system_instructions = []
        system_instructions.append(f"Generate a {aspect_ratio_instruction}.")
        
        if style_reference_image:
             system_instructions.append("Using the provided style reference image ONLY as a style reference. Ignore the content of the reference image; copy only its visual style, color palette, and vibe.")
        
        if remix_reference_image:
            system_instructions.append("Remix the provided reference image according to the user's prompt. Transform the reference image while maintaining its core composition and structure.")
             
        if theme_info:
            system_instructions.append(theme_info)
            
        if style_prompt:
             system_instructions.append(f"Style instructions: {style_prompt}")
             
        if design_opinions:
            opinions_text = []
            for key, value in design_opinions.items():
                val_str = ", ".join(value) if isinstance(value, list) else str(value)
                opinions_text.append(f"{key}: {val_str}")
            if opinions_text:
                system_instructions.append("Design opinions: " + "; ".join(opinions_text))
             
        system_message = " ".join(system_instructions)
        user_message = prompt
        
        # Log the separated prompts nicely
        from rich.rule import Rule
        console.print(Rule(title="IMAGE GENERATION REQUEST", style="bold cyan"))
        console.print(f"[bold yellow]User Message:[/bold yellow] {user_message}")
        console.print(f"[bold blue]System Instructions:[/bold blue] {system_message}")
        console.print(Rule(style="bold cyan"))
        
        # Prepare Prompt Details for UI
        prompt_details = {
            "user_message": user_message,
            "system_message": system_message,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        }
            
        if status_spinner:
            status_spinner.start() # Resume
            
        if progress_callback:
            # Send initial update with prompt details
            progress_callback(0, 4, "Initializing generation...", [], prompt_details=prompt_details)

        candidates = []
        
        # Create isolated folder for this request
        # Generate unique batch slug for this image generation request
        batch_slug = generate_batch_slug(prompt)
        request_folder = os.path.join(self.drafts_dir, batch_slug)
        os.makedirs(request_folder, exist_ok=True)
        
        # Store batch_slug for later reference
        self.last_batch_slug = batch_slug
        
        # Save batch metadata to JSON file
        metadata = {
            "batch_slug": batch_slug,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "created_at": datetime.now().isoformat(),
            "is_remix": remix_reference_image is not None
        }
        # Merge in any additional batch metadata (e.g., remix_slide_number, remix_image_path)
        if batch_metadata:
            metadata.update(batch_metadata)
        metadata_path = os.path.join(request_folder, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        if not self.client:
            console.print("[red]Error: API Key not found.[/red]")
            return self._fallback_generation(request_folder, progress_callback)

        for i in range(4):
            if progress_callback:
                progress_callback(i+1, 4, f"Generating image {i+1}/4...", candidates)
            console.print(f"  Generating candidate {i+1}/4...")
            try:
                # Build contents list - include style reference image and remix reference image if available
                contents = []
                if style_reference_image:
                    contents.append(style_reference_image)
                    import sys
                    if 'behave' not in sys.modules:
                        console.print(f"  [dim]Including style reference image (size: {style_reference_image.size})[/dim]")
                
                if remix_reference_image:
                    contents.append(remix_reference_image)
                    import sys
                    if 'behave' not in sys.modules:
                        console.print(f"  [dim]Including remix reference image (size: {remix_reference_image.size})[/dim]")
                
                if system_message:
                    contents.append(system_message)
                contents.append(user_message)
                
                import sys
                if 'behave' not in sys.modules:
                    console.print(f"  [dim]API Call - Model: {self.model_name}, Response Modality: IMAGE[/dim]")
                
                # Use generate_content for Gemini native image generation
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=['IMAGE']
                    )
                )
                
                image_saved = False
                
                # The v1beta SDK returns data in candidates -> content -> parts
                candidate_parts = []
                if hasattr(response, 'candidates') and response.candidates:
                    console.print(f"  [dim]Response has {len(response.candidates)} candidate(s)[/dim]")
                    for c_idx, candidate in enumerate(response.candidates):
                        parts = []
                        content = getattr(candidate, 'content', None)
                        if content is not None:
                            parts = getattr(content, 'parts', []) or []
                        console.print(f"    Candidate {c_idx}: parts={len(parts)}")
                        candidate_parts.extend(parts)
                elif hasattr(response, 'parts') and response.parts:
                    console.print(f"  [dim]Response has {len(response.parts)} part(s)[/dim]")
                    candidate_parts = response.parts
                else:
                    console.print(f"  [red]Response has neither parts nor candidates[/red]")
                
                if not candidate_parts:
                    console.print("  [red]No inline parts returned in response[/red]")
                
                # Process Gemini native image generation response
                for part in candidate_parts:
                    # Check for inline_data (Gemini format)
                    if hasattr(part, 'inline_data') and part.inline_data:
                        output_path = os.path.join(request_folder, f"candidate_{i+1}.png")
                        image_bytes = getattr(part.inline_data, 'data', None)
                        if isinstance(image_bytes, str):
                            image_bytes = base64.b64decode(image_bytes)
                        if not image_bytes:
                            continue
                        image = PIL.Image.open(BytesIO(image_bytes))
                        image.save(output_path, format="PNG")
                        candidates.append(output_path)
                        image_saved = True
                        console.print(f"  [green]✓ Saved image to candidate_{i+1}.png (size: {image.size})[/green]")
                        if progress_callback:
                            progress_callback(i+1, 4, f"Generated image {i+1}/4", candidates)
                        break

                if not image_saved:
                    console.print(f"  [red]✗ No image found in response for candidate {i+1}[/red]")
                    candidates.append(self._create_dummy(request_folder, i+1))
                    if progress_callback:
                        progress_callback(i+1, 4, f"Generated image {i+1}/4 (fallback)", candidates)

            except ResourceExhausted:
                import sys
                if 'behave' not in sys.modules:
                    console.print(f"  [red]Quota exceeded for candidate {i+1}. Please try again later.[/red]")
                candidates.append(self._create_dummy(request_folder, i+1))
                if progress_callback:
                    progress_callback(i+1, 4, f"Generated image {i+1}/4 (quota exceeded)", candidates)
            except Exception as e:
                # Always show errors, even in tests
                console.print(f"  [red]Error generating candidate {i+1}: {type(e).__name__}: {e}[/red]")
                candidates.append(self._create_dummy(request_folder, i+1))
                if progress_callback:
                    progress_callback(i+1, 4, f"Generated image {i+1}/4 (error)", candidates)
            
            time.sleep(1)

        # Count actual vs fallback images
        actual_images = sum(1 for c in candidates if os.path.exists(c) and os.path.getsize(c) > 100)
        import sys
        if 'behave' not in sys.modules:
            if actual_images < 4:
                console.print(f"\n[yellow]Warning: Only {actual_images}/4 images generated successfully. {4-actual_images} fallback(s) created.[/yellow]")
            else:
                console.print(f"\n[green]Successfully generated all 4 images![/green]")
        
        # Only open folder in CLI mode (when no progress callback provided and not in tests)
        import sys
        if not progress_callback and 'behave' not in sys.modules:
            self._open_folder(request_folder)
        
        # Return both candidates and batch_slug
        return {
            'candidates': candidates,
            'batch_slug': batch_slug,
            'batch_folder': request_folder
        }

    def _create_dummy(self, folder, index):
        path = os.path.join(folder, f"candidate_{index}.png")
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(b"dummy_image_data_placeholder")
        return path

    def _fallback_generation(self, folder, progress_callback=None):
        console.print("[yellow]Falling back to dummy generation...[/yellow]")
        candidates = []
        for i in range(4):
            if progress_callback:
                progress_callback(i+1, 4, f"Generating image {i+1}/4...")
            candidates.append(self._create_dummy(folder, i+1))
        import sys
        if not progress_callback and 'behave' not in sys.modules:
            self._open_folder(folder)
        
        # Extract batch_slug from folder path
        batch_slug = os.path.basename(folder)
        return {
            'candidates': candidates,
            'batch_slug': batch_slug,
            'batch_folder': folder
        }

    def _open_folder(self, path):
        # Try opening in VS Code first using direct execution to bypass shell/path issues
        try:
            console.print(f"[dim]Opening drafts in VS Code: {path}[/dim]")
            subprocess.run(["code", path], check=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            # VS Code not found or failed to open
            pass

        try:
            if os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                if subprocess.call(["which", "open"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
                    subprocess.run(["open", path])
                else:
                    subprocess.run(["xdg-open", path])
        except Exception as e:
            console.print(f"[dim]Could not auto-open folder: {e}[/dim]")

    def save_selection(self, candidates, index, filename):
        if index < 0 or index >= len(candidates):
            raise ValueError("Invalid selection index")
            
        selected_path = candidates[index]
        final_path = os.path.join(self.images_dir, filename)
        
        shutil.copy2(selected_path, final_path)
        return final_path

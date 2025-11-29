import os
import shutil
import time
import subprocess
import json
import PIL.Image
import google.generativeai as genai
from datetime import datetime
from rich.console import Console
from google.api_core.exceptions import ResourceExhausted

console = Console()

class NanoBananaClient:
    def __init__(self, presentation_context):
        self.context = presentation_context
        
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

        self.api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
             genai.configure(api_key=self.api_key)
             # Use 'models/nano-banana-pro-preview' as requested
             self.model_name = 'models/nano-banana-pro-preview' 
        
    def generate_candidates(self, prompt, status_spinner=None, progress_callback=None):
        """
        Generate 4 image candidates.
        
        Args:
            prompt: The image generation prompt
            status_spinner: Rich spinner for CLI mode
            progress_callback: Function(current, total, status) for web mode progress updates
        """
        if status_spinner:
            status_spinner.stop() # Pause spinner for logs
            
        console.print(f"[yellow]Generating 4 candidates for: '{prompt}'...[/yellow]")
        
        # Load style from metadata
        metadata_path = os.path.join(self.presentation_dir, "metadata.json")
        style_prompt = ""
        reference_images = []
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r") as f:
                    data = json.load(f)
                    style = data.get("image_style", {})
                    if style.get("prompt"):
                        style_prompt = style["prompt"]
                    if style.get("reference_images"):
                        for ref_name in style["reference_images"]:
                            # Check presentation root then images dir
                            ref_path = os.path.join(self.presentation_dir, ref_name)
                            if not os.path.exists(ref_path):
                                ref_path = os.path.join(self.images_dir, ref_name)
                            
                            if os.path.exists(ref_path):
                                try:
                                    img = PIL.Image.open(ref_path)
                                    reference_images.append(img)
                                    console.print(f"[dim]Using reference image: {ref_name}[/dim]")
                                except Exception as e:
                                    console.print(f"[red]Error loading reference image {ref_name}: {e}[/red]")
            except Exception:
                pass

        final_prompt = prompt
        if style_prompt:
            final_prompt = f"{prompt}. Style instructions: {style_prompt}"
            
        generation_input = [final_prompt]
        generation_input.extend(reference_images)
        
        if status_spinner:
            status_spinner.start() # Resume

        candidates = []
        
        # Create isolated folder for this request
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_prompt = "".join([c if c.isalnum() else "_" for c in prompt[:30]]).strip("_")
        request_folder = os.path.join(self.drafts_dir, f"{timestamp}_{safe_prompt}")
        os.makedirs(request_folder, exist_ok=True)
        
        if not self.api_key:
            console.print("[red]Error: API Key not found.[/red]")
            return self._fallback_generation(request_folder, progress_callback)

        # Try the specific image generation model first if it exists in the mental map of the SDK
        # otherwise fallback to the main multimodal model.
        # For this fix, we switch to the one we saw in the list: 'models/gemini-2.0-flash-exp'
        model = genai.GenerativeModel(self.model_name)

        for i in range(4):
            if progress_callback:
                progress_callback(i+1, 4, f"Generating image {i+1}/4...", candidates)
            console.print(f"  Generating candidate {i+1}/4...")
            try:
                # Gemini 2.0 Flash Exp supports generating images via text prompt
                response = model.generate_content(generation_input)
                
                image_saved = False
                if response.parts:
                    for part in response.parts:
                        # Check for executable code (image generation often returns python code to plot)
                        # OR check for inline data (actual image bytes)
                        if hasattr(part, 'inline_data') and part.inline_data:
                            output_path = os.path.join(request_folder, f"candidate_{i+1}.png")
                            with open(output_path, 'wb') as f:
                                f.write(part.inline_data.data)
                            candidates.append(output_path)
                            image_saved = True
                            
                            # Notify progress callback immediately after each image is generated
                            if progress_callback:
                                progress_callback(i+1, 4, f"Generated image {i+1}/4", candidates)
                            break
                        # Some models return a URI or executable code to render.
                        # If it's just text, it failed to generate an image.
                
                if not image_saved:
                    # If the main model didn't return an image, it might just be chatting.
                    # Let's try the specific image model from the list we saw earlier if this fails:
                    # 'models/imagen-3.0-generate-001' was missing, but 'models/gemini-2.0-flash-exp' was there.
                    # If this fails, we might need to use the REST API directly if the SDK is hiding the image capability.
                    console.print(f"  [red]No image found in response for candidate {i+1}[/red]")
                    candidates.append(self._create_dummy(request_folder, i+1))
                    if progress_callback:
                        progress_callback(i+1, 4, f"Generated image {i+1}/4 (fallback)", candidates)

            except ResourceExhausted:
                console.print(f"  [red]Quota exceeded for candidate {i+1}. Please try again later.[/red]")
                candidates.append(self._create_dummy(request_folder, i+1))
                if progress_callback:
                    progress_callback(i+1, 4, f"Generated image {i+1}/4 (quota exceeded)", candidates)
            except Exception as e:
                console.print(f"  [red]Error generating candidate {i+1}: {e}[/red]")
                candidates.append(self._create_dummy(request_folder, i+1))
                if progress_callback:
                    progress_callback(i+1, 4, f"Generated image {i+1}/4 (error)", candidates)
            
            time.sleep(1)

        # Only open folder in CLI mode (when no progress callback provided)
        if not progress_callback:
            self._open_folder(request_folder)
        return candidates

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
        if not progress_callback:
            self._open_folder(folder)
        return candidates

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

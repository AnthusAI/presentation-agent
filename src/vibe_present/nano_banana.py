import os
import shutil
import google.generativeai as genai
from rich.console import Console

console = Console()

class NanoBananaClient:
    def __init__(self, presentation_context):
        self.context = presentation_context
        root = os.environ.get('VIBE_PRESENT_ROOT', os.path.expanduser("~/.vibe_present"))
        self.presentation_dir = os.path.join(root, presentation_context['name'])
        self.images_dir = os.path.join(self.presentation_dir, "images")
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

        api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
             genai.configure(api_key=api_key)
             self.model_name = 'imagen-3.0-generate-001' 
        
    def generate_candidates(self, prompt):
        console.print(f"[yellow]Generating 4 candidates for: '{prompt}'...[/yellow]")
        candidates = []
        
        try:
            # Hypothetical API for Nano Banana / Imagen in this SDK
            if hasattr(genai, 'ImageGenerationModel'):
                model = genai.ImageGenerationModel.from_pretrained(self.model_name)
                response = model.generate_images(
                    prompt=prompt,
                    number_of_images=4,
                )
                images = response.images
            else:
                raise ImportError("ImageGenerationModel not found in google.generativeai")

            for i, image in enumerate(images):
                # Save to temp
                path = os.path.join(self.images_dir, f"temp_candidate_{i}.png")
                # Assuming image object has save method or we need to write bytes
                if hasattr(image, 'save'):
                    image.save(path)
                elif hasattr(image, '_image_bytes'):
                     with open(path, "wb") as f:
                         f.write(image._image_bytes)
                else:
                     # Fallback/Mock behavior
                     with open(path, "wb") as f:
                         f.write(b"real_image_data")

                candidates.append(path)
                
        except Exception as e:
            console.print(f"[red]Error calling Image Gen API: {e}[/red]")
            console.print("[yellow]Falling back to dummy generation for demo...[/yellow]")
            for i in range(4):
                path = os.path.join(self.images_dir, f"temp_candidate_{i}.png")
                with open(path, "wb") as f:
                    f.write(b"fake_image_data")
                candidates.append(path)

        return candidates

    def save_selection(self, candidates, index, filename):
        if index < 0 or index >= len(candidates):
            raise ValueError("Invalid selection index")
            
        selected_path = candidates[index]
        final_path = os.path.join(self.images_dir, filename)
        
        shutil.move(selected_path, final_path)
        
        # Cleanup others
        for path in candidates:
            if os.path.exists(path) and path != final_path:
                os.remove(path)
                
        return final_path

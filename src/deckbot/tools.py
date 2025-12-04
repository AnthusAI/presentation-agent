import os
import subprocess
import shutil
import re
import inspect
import uuid
from functools import wraps
from rich.console import Console
from rich.prompt import IntPrompt
from deckbot.nano_banana import NanoBananaClient
from deckbot.manager import PresentationManager
from deckbot.deck_validator import DeckValidator
from deckbot.visual_qa import VisualQA

console = Console()

class PresentationTools:
    def __init__(self, presentation_context, nano_client: NanoBananaClient, root_dir=None, api_key: str = None):
        self.context = presentation_context
        self.nano_client = nano_client
        self.status_spinner = None # To be set by Agent/REPL
        self.waiting_for_user_input = False  # Flag to indicate we're waiting for external input
        self.api_key = api_key
        self.current_slide = 1
        self.visual_qa = VisualQA(api_key)
        
        # Hook for notifying updates (e.g., presentation compiled)
        self.on_presentation_updated = None
        
        # Hook for tool call events (start, end, error)
        self.tool_listeners = []
        
        # Resolve presentation root
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
        self.manager = PresentationManager(root_dir=root)

    def _try_auto_compile(self):
        """Automatically recompile the presentation and return status string."""
        try:
            # We don't want to force a specific slide, just general update
            result = self.compile_presentation()
            if "successful" in result:
                return "\n\nPresentation automatically compiled. The preview is updated."
            else:
                return f"\n\nWarning: Auto-compilation failed: {result}"
        except Exception as e:
            return f"\n\nWarning: Auto-compilation failed: {str(e)}"

    def add_tool_listener(self, listener):
        self.tool_listeners.append(listener)

    def _notify_tool_listeners(self, event, data):
        for listener in self.tool_listeners:
            try:
                listener(event, data)
            except Exception as e:
                print(f"Error in tool listener: {e}")

    @property
    def on_tool_call(self):
        return self._notify_tool_listeners
        
    @on_tool_call.setter
    def on_tool_call(self, callback):
        if callback:
            self.tool_listeners.append(callback)

    def _wrap_tool(self, tool_name, func):
        """Wrapper that notifies before/after tool execution."""
        @wraps(func)
        def wrapped(*args, **kwargs):
            # Normalize arguments: bind positional args to parameter names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            normalized_args = bound_args.arguments
            
            # Generate a unique call ID for this tool invocation
            call_id = str(uuid.uuid4())
            
            if self.on_tool_call:
                # Include normalized args and call_id
                self.on_tool_call("tool_start", {
                    "tool": tool_name, 
                    "args": normalized_args,
                    "call_id": call_id
                })
            try:
                result = func(*args, **kwargs)
                if self.on_tool_call:
                    self.on_tool_call("tool_end", {
                        "tool": tool_name, 
                        "result": str(result),
                        "args": normalized_args,
                        "call_id": call_id
                    })
                return result
            except Exception as e:
                if self.on_tool_call:
                    self.on_tool_call("tool_error", {
                        "tool": tool_name, 
                        "error": str(e),
                        "args": normalized_args,
                        "call_id": call_id
                    })
                raise e # Re-raise to let Gemini handle it
        
        # wrapped.__name__ = tool_name # Handled by @wraps
        return wrapped

    def list_presentations(self):
        """Lists all available presentations."""
        presentations = self.manager.list_presentations()
        if not presentations:
            return "No presentations found."
        
        result = []
        for p in presentations:
            result.append(f"- Name: {p['name']}")
            result.append(f"  Created: {p.get('created_at', 'Unknown')}")
            result.append(f"  Description: {p.get('description', '')}")
            result.append("")
        return "\n".join(result)

    def list_templates(self):
        """Lists all available templates."""
        templates = self.manager.list_templates()
        if not templates:
            return "No templates found."
        result = []
        for t in templates:
            result.append(f"- {t['name']}: {t['description']}")
        return "\n".join(result)

    def create_presentation(self, name: str, description: str = "", template: str = None):
        """Creates a new presentation."""
        try:
            self.manager.create_presentation(name, description, template=template)
            return f"Successfully created presentation '{name}'"
        except ValueError as e:
            return f"Error creating presentation: {str(e)}"

    def preview_template(self, template_name: str):
        """Previews a template by compiling it to HTML and opening it."""
        template_path = os.path.join(self.manager.templates_dir, template_name)
        if not os.path.exists(template_path):
            return f"Template '{template_name}' not found."
        
        console.print(f"[green]Previewing template '{template_name}'...[/green]")
        try:
            # Reuse standard Marp build
            subprocess.run(["npx", "@marp-team/marp-cli", "deck.marp.md", "--allow-local-files"], cwd=template_path, check=True)
            
            html_file = os.path.join(template_path, "deck.marp.html")
            if os.path.exists(html_file):
                if os.name == 'posix':
                     subprocess.run(["open", html_file])
                elif os.name == 'nt':
                     os.startfile(html_file)
            return f"Previewing template '{template_name}'."
        except Exception as e:
            return f"Error previewing template: {str(e)}"

    def load_presentation(self, name: str):
        """Loads a presentation context."""
        presentation = self.manager.get_presentation(name)
        if not presentation:
            return f"Error: Presentation '{name}' not found."
        return presentation

    def list_files(self, directory: str = "", **kwargs):
        """List files in the current presentation directory or a subdirectory."""
        if not os.path.exists(self.presentation_dir):
            return "Presentation directory does not exist."
            
        target_dir = self.presentation_dir
        if directory:
            # prevent escaping presentation dir
            target_dir = os.path.abspath(os.path.join(self.presentation_dir, directory))
            if not target_dir.startswith(os.path.abspath(self.presentation_dir)):
                 return "Error: Cannot list files outside presentation directory."
        
        if not os.path.exists(target_dir):
             return f"Directory '{directory}' does not exist."

        try:
            items = []
            for name in os.listdir(target_dir):
                path = os.path.join(target_dir, name)
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    mtime = 0
                items.append((name, mtime))
            
            # Sort by mtime descending (newest first)
            items.sort(key=lambda x: x[1], reverse=True)
            
            files = [x[0] for x in items]
            if not files:
                return "Directory is empty."
            return "\n".join(files)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def read_file(self, filename: str):
        """Read content of a file in the presentation directory."""
        path = os.path.join(self.presentation_dir, filename)
        if not os.path.exists(path):
            return f"Error: File '{filename}' not found."
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, filename: str, content: str):
        """
        Write content to a file in the presentation directory. WARNING: Overwrites entire file.
        Automatically recompiles the presentation after writing.
        """
        if not os.path.exists(self.presentation_dir):
            return "Presentation directory does not exist."

        # Validate deck structure if updating deck.marp.md
        summary = None
        if filename == 'deck.marp.md':
            validation = DeckValidator.validate_and_summarize(content)
            if not validation['valid']:
                return f"Error: Invalid deck structure. {validation['error']}"
            summary = validation.get('summary')

        path = os.path.join(self.presentation_dir, filename)
        try:
            with open(path, 'w') as f:
                f.write(content)
            
            msg = f"Successfully wrote to {filename}"
            if summary:
                msg += "\n\n" + summary
            
            # Auto-compile
            msg += self._try_auto_compile()
            return msg
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def replace_text(self, filename: str, old_text: str, new_text: str):
        """
        Replace text in a file. Use this to edit existing files safely.
        Automatically recompiles the presentation after replacing.
        """
        if not os.path.exists(self.presentation_dir):
            return "Presentation directory does not exist."
        path = os.path.join(self.presentation_dir, filename)
        
        if not os.path.exists(path):
            return f"Error: File '{filename}' not found."
            
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            if old_text not in content:
                return f"Error: '{old_text}' not found in {filename}."
                
            new_content = content.replace(old_text, new_text)
            
            # Validate deck structure if updating deck.marp.md
            summary = None
            if filename == 'deck.marp.md':
                validation = DeckValidator.validate_and_summarize(new_content)
                if not validation['valid']:
                    return f"Error: Invalid deck structure. {validation['error']}"
                summary = validation.get('summary')

            with open(path, 'w') as f:
                f.write(new_content)
            
            msg = f"Successfully replaced text in {filename}"
            if summary:
                msg += "\n\n" + summary
            
            # Auto-compile
            msg += self._try_auto_compile()
            return msg
        except Exception as e:
            return f"Error replacing text: {str(e)}"

    def validate_deck(self):
        """
        Validates the current deck structure and CSS.
        Returns a summary if valid, or an error message if invalid.
        Use this to check for syntax errors without modifying the file.
        """
        path = os.path.join(self.presentation_dir, 'deck.marp.md')
        if not os.path.exists(path):
             return "Error: deck.marp.md not found."
             
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            validation = DeckValidator.validate_and_summarize(content)
            if not validation['valid']:
                return f"Validation Error:\n{validation['error']}"
            
            return f"Validation Successful:\n{validation['summary']}"
        except Exception as e:
            return f"Error validating deck: {str(e)}"

    def copy_file(self, source: str, destination: str):
        """Copy a file within the presentation directory."""
        src_path = os.path.abspath(os.path.join(self.presentation_dir, source))
        dst_path = os.path.abspath(os.path.join(self.presentation_dir, destination))
        
        if not src_path.startswith(os.path.abspath(self.presentation_dir)):
            return "Error: Source path outside presentation directory."
        if not dst_path.startswith(os.path.abspath(self.presentation_dir)):
            return "Error: Destination path outside presentation directory."
            
        if not os.path.exists(src_path):
            return f"Error: Source file '{source}' not found."
            
        try:
            shutil.copy2(src_path, dst_path)
            msg = f"Successfully copied '{source}' to '{destination}'"
            msg += self._try_auto_compile()
            return msg
        except Exception as e:
            return f"Error copying file: {str(e)}"

    def move_file(self, source: str, destination: str):
        """Move/rename a file within the presentation directory."""
        src_path = os.path.abspath(os.path.join(self.presentation_dir, source))
        dst_path = os.path.abspath(os.path.join(self.presentation_dir, destination))
        
        if not src_path.startswith(os.path.abspath(self.presentation_dir)):
            return "Error: Source path outside presentation directory."
        if not dst_path.startswith(os.path.abspath(self.presentation_dir)):
            return "Error: Destination path outside presentation directory."
            
        if not os.path.exists(src_path):
            return f"Error: Source file '{source}' not found."
            
        try:
            shutil.move(src_path, dst_path)
            msg = f"Successfully moved '{source}' to '{destination}'"
            msg += self._try_auto_compile()
            return msg
        except Exception as e:
            return f"Error moving file: {str(e)}"

    def delete_file(self, filename: str):
        """
        Delete a file from the presentation directory.
        Automatically recompiles the presentation after deletion.
        """
        path = os.path.abspath(os.path.join(self.presentation_dir, filename))
        
        if not path.startswith(os.path.abspath(self.presentation_dir)):
            return "Error: Path outside presentation directory."
            
        if not os.path.exists(path):
            return f"Error: File '{filename}' not found."
            
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            msg = f"Successfully deleted '{filename}'"
            msg += self._try_auto_compile()
            return msg
        except Exception as e:
            return f"Error deleting file: {str(e)}"

    def create_directory(self, dirname: str):
        """Create a subdirectory within the presentation."""
        path = os.path.abspath(os.path.join(self.presentation_dir, dirname))
        
        if not path.startswith(os.path.abspath(self.presentation_dir)):
            return "Error: Path outside presentation directory."
            
        try:
            os.makedirs(path, exist_ok=True)
            return f"Successfully created directory '{dirname}'"
        except Exception as e:
            return f"Error creating directory: {str(e)}"

    def generate_image(self, prompt: str, aspect_ratio: str = None, resolution: str = "2K"):
        """
        Generates an image using Nano Banana.
        
        In CLI mode: Synchronously generates, displays, and waits for selection. Automatically recompiles after saving.
        In Web mode: Triggers async generation and returns immediately. The system will
                     call the agent again after user selects an image.
        """
        # Default aspect ratio to presentation setting if not provided
        if not aspect_ratio:
            try:
                aspect_ratio = self.get_aspect_ratio()
                # get_aspect_ratio might return a string error if it fails, check it
                if aspect_ratio and "Error" in aspect_ratio:
                    aspect_ratio = "16:9" # Fallback
                elif not aspect_ratio:
                    aspect_ratio = "16:9" # Fallback
            except Exception:
                aspect_ratio = "16:9"

        # Check if we have an image generation callback (indicates web mode)
        if hasattr(self, 'on_image_generation'):
            # Web mode: Trigger the full async workflow
            # System will handle: generate → display UI → user selects → save → notify agent
            self.waiting_for_user_input = True  # Signal that we need to wait
            self.on_image_generation(prompt, aspect_ratio=aspect_ratio, resolution=resolution)
            return "WAIT: Image generation started. The system is generating 4 candidates for the user to choose from. DO NOT proceed with incorporating the image yet. Wait for a [SYSTEM] message that tells you which image the user selected and its filename."
        
        # CLI mode: Synchronous interactive selection
        # Pause spinner if active
        if self.status_spinner:
            self.status_spinner.stop()
            
        try:
            # Use NanoBananaClient default or provided args
            # The client itself needs to support these args. Assuming it does or checking next.
            # If NanoBananaClient.generate_candidates doesn't take them, we might need to update it too.
            # For now, let's update this signature to match the feature request.
            result = self.nano_client.generate_candidates(prompt, aspect_ratio=aspect_ratio, resolution=resolution)
            candidates = result['candidates']
            batch_slug = result['batch_slug']
            
            if not candidates:
                return "Failed to generate images."
            
            console.print("[bold]Generated Candidates:[/bold]")
            for i, path in enumerate(candidates):
                console.print(f"{i+1}. {path}")
            
            selection = IntPrompt.ask("Select an image (1-4) or 0 to cancel", choices=["0", "1", "2", "3", "4"])
            
            if selection > 0:
                filename = f"image_{selection}.png"
                saved_path = self.nano_client.save_selection(candidates, selection - 1, filename)
                rel_path = os.path.relpath(saved_path, self.presentation_dir)
                msg = f"Image generated and saved to {rel_path}. You can now reference it in the presentation."
                msg += self._try_auto_compile()
                return msg
            else:
                return "Image selection cancelled."
        finally:
            # Restart spinner if it was active
            if self.status_spinner:
                self.status_spinner.start()

    def inspect_slide(self, slide_number: int) -> str:
        """Runs Visual QA on the specified slide and returns a formatted string if issues are found."""
        try:
            # Pass conversation history to VisualQA if available
            history = []
            if hasattr(self.context, 'history'):
                history = self.context.get('history', [])
            
            has_issues, report = self.visual_qa.check_slide(self.presentation_dir, slide_number, history=history)
            
            if has_issues:
                return f"\n\nCRITICAL VISUAL ISSUES FOUND:\n{report}\n\nSTOP AND THINK: You have detected a visual defect. Do not blindly retry the same fix. Analyze the CSS and layout. If you have already attempted a fix, STOP and ask the user for help."
            
            return f"\n\n{report}"
        except Exception as e:
            # Log but don't break the tool
            print(f"Visual QA Error: {e}")
        return ""

    def _run_visual_qa(self, slide_number: int) -> str:
        # Deprecated internal method, kept for backward compatibility if needed, but delegating to new public method
        return self.inspect_slide(slide_number)

    def go_to_slide(self, slide_number: int = None):
        """
        Navigates to a specific slide without recompiling.
        
        Args:
            slide_number: Slide number to navigate to (1-based index).
        """
        if slide_number is None:
             return "Error: slide_number is required. Please specify which slide to go to."

        self.current_slide = slide_number

        # Check if HTML exists
        html_file = os.path.join(self.presentation_dir, "deck.marp.html")
        if not os.path.exists(html_file):
            return "Presentation has not been compiled yet. Use 'compile_presentation' first."
        
        # Run Visual QA
        # qa_report = self.inspect_slide(slide_number)
            
        # Notify listeners (Web UI)
        if self.on_presentation_updated:
            self.on_presentation_updated({"slide_number": slide_number})
            # Wait a tiny bit? No, event handling is immediate usually.
            return f"Navigating to slide {slide_number}."
            
        # Local Open (CLI)
        target = f"file://{os.path.abspath(html_file)}#{slide_number}"
        
        # Use Popen to open without blocking
        if os.name == 'posix':
             subprocess.Popen(["open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif os.name == 'nt':
             # Windows fallback
             os.startfile(html_file) 
        
        return f"Navigating to slide {slide_number}."

    def compile_presentation(self, slide_number: int = None):
        """
        Compiles the presentation using Marp.
        
        IMPORTANT: Most file operations (write_file, replace_text, delete_file) automatically recompile.
        Only call this tool if:
        1. You need to force a recompile without changing files.
        2. You want to open the preview at a specific slide (using slide_number).
        
        Args:
            slide_number: Optional slide number to open the presentation at (1-based index).
        """
        console.print(f"[green]Compiling presentation in {self.presentation_dir}...[/green]")
        try:
            # Use --allow-local-files to support absolute paths or images outside working dir if needed
            subprocess.run(["npx", "@marp-team/marp-cli", "deck.marp.md", "--allow-local-files"], cwd=self.presentation_dir, check=True)
            
            # Post-process HTML to inject IDs for navigation if missing
            # This ensures #1, #2, etc. work in both Web UI and local open
            html_file = os.path.join(self.presentation_dir, "deck.marp.html")
            if os.path.exists(html_file):
                try:
                    with open(html_file, 'r') as f:
                        content = f.read()
                    
                    count = [0]
                    def add_id(match):
                        count[0] += 1
                        tag = match.group(1)
                        if 'id="' in tag:
                            return tag
                        # Insert id before the closing > or space
                        return f'{tag[:-1]} id="{count[0]}">'
                    
                    new_content = re.sub(r'(<section[^>]*>)', add_id, content)
                    
                    if new_content != content:
                        with open(html_file, 'w') as f:
                            f.write(new_content)
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to inject slide IDs: {e}[/yellow]")
            
            # Use the go_to_slide logic if slide_number provided, otherwise just notify/open default
            if slide_number:
                return self.go_to_slide(slide_number)
            
            # Default compilation success path (no specific slide)
            target_slide = self.current_slide
            # qa_report = self.inspect_slide(target_slide)

            if self.on_presentation_updated:
                self.on_presentation_updated({})
                return f"Compilation successful. Presentation updated in Web UI."

            # Local open default
            if os.path.exists(html_file):
                if os.name == 'posix':
                     subprocess.Popen(["open", html_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif os.name == 'nt':
                     os.startfile(html_file)
            return f"Compilation successful."
        except Exception as e:
            return f"Error compiling: {str(e)}"

    def export_pdf(self):
        """Exports the presentation to PDF using Marp."""
        console.print(f"[green]Exporting PDF in {self.presentation_dir}...[/green]")
        try:
            # Derive filename from presentation name
            presentation_name = self.context.get('name', 'presentation')
            # Sanitize name for filename
            safe_name = "".join([c if c.isalnum() or c in (' ', '-', '_') else "_" for c in presentation_name]).strip()
            if not safe_name:
                safe_name = "presentation"
            
            pdf_filename = f"{safe_name}.pdf"
            
            # Ensure Chrome/Chromium is installed or managed by user environment
            # Use --allow-local-files to support local images in PDF export
            # Use -o to specify output filename
            subprocess.run(["npx", "@marp-team/marp-cli", "deck.marp.md", "--pdf", "--allow-local-files", "-o", pdf_filename], cwd=self.presentation_dir, check=True)
            
            pdf_file = os.path.join(self.presentation_dir, pdf_filename)
            if os.path.exists(pdf_file):
                if os.name == 'posix':
                     subprocess.run(["open", pdf_file])
                elif os.name == 'nt':
                     os.startfile(pdf_file)
            return f"PDF export successful. Saved to {pdf_file}"
        except Exception as e:
            return f"Error exporting PDF: {str(e)}. Make sure Chrome/Chromium is installed."

    def get_presentation_summary(self):
        """
        Returns a text summary of the current presentation state, including slide titles and image descriptions.
        Useful for YOU (the agent) to understand the deck content without reading every file.
        """
        if not os.path.exists(self.presentation_dir):
            return "Presentation directory does not exist."
            
        files = sorted([f for f in os.listdir(self.presentation_dir) if f.endswith('.md')])
        if not files:
            return "Presentation is empty."

        summary = []
        for filename in files:
            path = os.path.join(self.presentation_dir, filename)
            try:
                with open(path, 'r') as f:
                    content = f.read()
                
                # Extract title (first line starting with #)
                title = "Untitled Slide"
                images = []
                text_preview = ""
                
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# ') and title == "Untitled Slide":
                        title = line.strip('# ').strip()
                    elif line.strip().startswith('!['):
                        # simplistic image extraction
                        images.append(line.strip())
                    elif line.strip() and not line.startswith('#') and not line.startswith('!['):
                         if not text_preview:
                             text_preview = line.strip()[:50] + "..."

                summary.append(f"File: {filename}")
                summary.append(f"  Title: {title}")
                if images:
                    summary.append(f"  Images: {', '.join(images)}")
                if text_preview:
                    summary.append(f"  Content: {text_preview}")
                summary.append("")
            except Exception as e:
                summary.append(f"File: {filename} (Error reading: {e})")

        return "\n".join(summary)

    def open_presentation_folder(self):
        """Opens the presentation directory in the system file explorer or VS Code."""
        try:
            # Try opening in VS Code first
            subprocess.run(["code", self.presentation_dir], check=False)
            return f"Opened {self.presentation_dir} in VS Code."
        except Exception:
            # Fallback to system open
            try:
                if os.name == 'posix':
                    subprocess.run(["open", self.presentation_dir], check=True)
                elif os.name == 'nt':
                    os.startfile(self.presentation_dir)
                return f"Opened {self.presentation_dir} in system explorer."
            except Exception as e:
                return f"Error opening folder: {e}"

    def get_aspect_ratio(self):
        """Get the current presentation's aspect ratio."""
        try:
            return self.manager.get_presentation_aspect_ratio(self.context['name'])
        except Exception as e:
            return f"Error getting aspect ratio: {str(e)}"
    
    def set_aspect_ratio(self, aspect_ratio: str):
        """Set the presentation's aspect ratio and recompile the deck."""
        try:
            self.manager.set_presentation_aspect_ratio(self.context['name'], aspect_ratio)
            # Recompile the deck
            self.compile_presentation()
            return f"Aspect ratio changed to {aspect_ratio} and deck recompiled."
        except Exception as e:
            return f"Error setting aspect ratio: {str(e)}"
    
    def get_layouts(self):
        """
        Get available slide layouts for this presentation.
        Returns a list of layouts with their names, markdown content, and metadata.
        """
        layouts_path = os.path.join(self.presentation_dir, "layouts.md")
        
        if not os.path.exists(layouts_path):
            return "No layouts file found in this presentation."
        
        try:
            with open(layouts_path, "r") as f:
                content = f.read()
            
            # Parse layouts by splitting on slide breaks and finding layout comments
            import re
            
            # Split by --- to get individual slides
            slides = content.split('\n---\n')
            
            layouts = []
            for slide in slides:
                # Look for layout name in HTML comment
                match = re.search(r'<!-- layout: ([\w-]+) -->', slide)
                if match:
                    layout_name = match.group(1)
                    # Extract just the slide content (skip front matter for first slide)
                    if slide.strip().startswith('---'):
                        # This is the first slide with front matter, skip it
                        continue
                    
                    # Parse metadata from HTML comments
                    image_friendly = re.search(r'<!-- image-friendly: (true|false) -->', slide)
                    aspect_ratio = re.search(r'<!-- recommended-aspect-ratio: ([\d:]+) -->', slide)
                    image_position = re.search(r'<!-- image-position: ([\w-]+) -->', slide)
                    description = re.search(r'<!-- description: (.+?) -->', slide)
                    
                    layout_info = {
                        "name": layout_name,
                        "content": slide.strip(),
                        "image_friendly": image_friendly.group(1) == "true" if image_friendly else False,
                        "recommended_aspect_ratio": aspect_ratio.group(1) if aspect_ratio else None,
                        "image_position": image_position.group(1) if image_position else None,
                        "description": description.group(1) if description else None
                    }
                    
                    layouts.append(layout_info)
            
            if not layouts:
                return "No layouts found in layouts.md"
            
            # Format for easy reading
            result = "Available Layouts:\n\n"
            for layout in layouts:
                result += f"## {layout['name']}\n"
                if layout['description']:
                    result += f"{layout['description']}\n"
                if layout['image_friendly']:
                    result += f"✓ Image-friendly"
                    if layout['recommended_aspect_ratio']:
                        result += f" (recommended aspect ratio: {layout['recommended_aspect_ratio']})"
                    if layout['image_position']:
                        result += f" - Position: {layout['image_position']}"
                    result += "\n"
                result += f"\n```markdown\n{layout['content']}\n```\n\n"
            
            return result
            
        except Exception as e:
            return f"Error reading layouts: {str(e)}"
    
    def create_slide_with_layout(self, title: str = None, position: str = "end"):
        """
        Create a new slide using a layout template.
        
        This tool triggers a UI flow where the user selects a layout from visual previews.
        Similar to image generation, this is an interactive process:
        1. Call this tool to initiate slide creation
        2. System shows layout previews to the user
        3. User selects a layout
        4. System creates the new slide with that layout
        
        Args:
            title: Optional title for the new slide
            position: Where to insert the slide - "end" (default), "beginning", or "after-current"
        
        Returns:
            Instructions for the user to select a layout
        
        Important: 
        - Use this tool ONLY when the user wants to create ONE new slide
        - For multiple slides, create them manually by editing deck.marp.md directly,
          since the UI only allows selecting one layout at a time
        """
        # This is a WEB-MODE tool - it will trigger the layout selection UI
        if hasattr(self, 'on_layout_request') and callable(self.on_layout_request):
            # Notify the session service to show layout options
            self.on_layout_request(title=title, position=position)
            return f"Layout selection UI displayed. Waiting for user to select a layout for the new slide{' titled: ' + title if title else ''}..."
        else:
            # CLI mode fallback - just show available layouts
            return f"Layout selection requires the web UI. Available layouts:\n\n{self.get_layouts()}\n\nTo create a slide, use write_file or replace_text to add the layout markdown to deck.marp.md"

    def get_full_context(self):
        """Reads all markdown files in the presentation to build full context."""
        if not os.path.exists(self.presentation_dir):
            return "Presentation directory empty."
            
        context_str = "## Presentation Files\n\n"
        files = sorted([f for f in os.listdir(self.presentation_dir) if f.endswith('.md')])
        
        if not files:
            return "No markdown files found in presentation."
            
        for filename in files:
            path = os.path.join(self.presentation_dir, filename)
            try:
                with open(path, 'r') as f:
                    content = f.read()
                context_str += f"### {filename}\n```markdown\n{content}\n```\n\n"
            except Exception:
                pass
                
        return context_str

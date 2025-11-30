import os
import subprocess
import shutil
from rich.console import Console
from rich.prompt import IntPrompt
from deckbot.nano_banana import NanoBananaClient
from deckbot.manager import PresentationManager

console = Console()

class PresentationTools:
    def __init__(self, presentation_context, nano_client: NanoBananaClient):
        self.context = presentation_context
        self.nano_client = nano_client
        self.status_spinner = None # To be set by Agent/REPL
        self.waiting_for_user_input = False  # Flag to indicate we're waiting for external input
        
        # Hook for notifying updates (e.g., presentation compiled)
        self.on_presentation_updated = None
        
        # Hook for tool call events (start, end, error)
        self.on_tool_call = None
        
        # Resolve presentation root
        env_root = os.environ.get('VIBE_PRESENTATION_ROOT')
        if env_root:
            root = env_root
        elif os.path.exists("presentations"):
            root = os.path.abspath("presentations")
        else:
            root = os.path.expanduser("~/.vibe_presentation")
        
        self.presentation_dir = os.path.join(root, presentation_context['name'])
        self.manager = PresentationManager(root_dir=root)

    def _wrap_tool(self, tool_name, func):
        """Wrapper that notifies before/after tool execution."""
        def wrapped(*args, **kwargs):
            if self.on_tool_call:
                # Mask args for some tools if needed, but generally fine
                # Convert args to list for JSON serialization if needed
                self.on_tool_call("tool_start", {"tool": tool_name, "args": args, "kwargs": kwargs})
            try:
                result = func(*args, **kwargs)
                if self.on_tool_call:
                    self.on_tool_call("tool_end", {"tool": tool_name, "result": str(result)})
                return result
            except Exception as e:
                if self.on_tool_call:
                    self.on_tool_call("tool_error", {"tool": tool_name, "error": str(e)})
                raise e # Re-raise to let Gemini handle it
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

    def list_files(self, **kwargs):
        """List files in the current presentation directory."""
        if not os.path.exists(self.presentation_dir):
            return "Presentation directory does not exist."
        files = os.listdir(self.presentation_dir)
        return "\n".join(files)

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
        """Write content to a file in the presentation directory."""
        if not os.path.exists(self.presentation_dir):
            return "Presentation directory does not exist."
        path = os.path.join(self.presentation_dir, filename)
        try:
            with open(path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {filename}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

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
            return f"Successfully copied '{source}' to '{destination}'"
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
            return f"Successfully moved '{source}' to '{destination}'"
        except Exception as e:
            return f"Error moving file: {str(e)}"

    def delete_file(self, filename: str):
        """Delete a file from the presentation directory."""
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
            return f"Successfully deleted '{filename}'"
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

    def generate_image(self, prompt: str):
        """
        Generates an image using Nano Banana.
        
        In CLI mode: Synchronously generates, displays, and waits for selection.
        In Web mode: Triggers async generation and returns immediately. The system will
                     call the agent again after user selects an image.
        """
        # Check if we have an image generation callback (indicates web mode)
        if hasattr(self, 'on_image_generation'):
            # Web mode: Trigger the full async workflow
            # System will handle: generate → display UI → user selects → save → notify agent
            self.waiting_for_user_input = True  # Signal that we need to wait
            self.on_image_generation(prompt)
            return "WAIT: Image generation started. The system is generating 4 candidates for the user to choose from. DO NOT proceed with incorporating the image yet. Wait for a [SYSTEM] message that tells you which image the user selected and its filename."
        
        # CLI mode: Synchronous interactive selection
        # Pause spinner if active
        if self.status_spinner:
            self.status_spinner.stop()
            
        try:
            candidates = self.nano_client.generate_candidates(prompt)
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
                return f"Image generated and saved to {rel_path}. You can now reference it in the presentation."
            else:
                return "Image selection cancelled."
        finally:
            # Restart spinner if it was active
            if self.status_spinner:
                self.status_spinner.start()

    def compile_presentation(self):
        """Compiles the presentation using Marp."""
        console.print(f"[green]Compiling presentation in {self.presentation_dir}...[/green]")
        try:
            # Use --allow-local-files to support absolute paths or images outside working dir if needed
            subprocess.run(["npx", "@marp-team/marp-cli", "deck.marp.md", "--allow-local-files"], cwd=self.presentation_dir, check=True)
            
            # Notify listeners
            if self.on_presentation_updated:
                self.on_presentation_updated()

            # Try to open the HTML/PDF? Defaults to HTML
            # If we have a callback, assume it handles UI update and skip opening if requested.
            # For now, we only skip opening if explicitly told or maybe just always open in CLI mode?
            # We don't know if we are in CLI or Web mode easily here without passing a flag.
            # But if on_presentation_updated is set, it implies Web Mode usually.
            # Let's skip opening if callback is set, assuming Web Mode handles it.
            if self.on_presentation_updated:
                return "Compilation successful. Presentation updated in Web UI."

            html_file = os.path.join(self.presentation_dir, "deck.marp.html")
            if os.path.exists(html_file):
                if os.name == 'posix':
                     subprocess.run(["open", html_file])
                elif os.name == 'nt':
                     os.startfile(html_file)
            return "Compilation successful."
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

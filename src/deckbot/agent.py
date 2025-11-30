import os
import json
import google.generativeai as genai
from rich.console import Console
from deckbot.nano_banana import NanoBananaClient
from deckbot.tools import PresentationTools

class Agent:
    def __init__(self, presentation_context):
        self.context = presentation_context
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        # Initialize tools
        self.nano_client = NanoBananaClient(presentation_context)
        self.tools_handler = PresentationTools(presentation_context, self.nano_client)
        
        # Wrap tools for visibility and patch handler
        def w(name, original_func):
            wrapper = self.tools_handler._wrap_tool(name, original_func)
            # Monkey-patch the handler so direct calls also emit events
            setattr(self.tools_handler, name, wrapper)
            return wrapper
            
        # Note: We must pass the original methods before they get patched
        self.tools_list = [
            w("list_files", self.tools_handler.list_files),
            w("read_file", self.tools_handler.read_file),
            w("write_file", self.tools_handler.write_file),
            w("copy_file", self.tools_handler.copy_file),
            w("move_file", self.tools_handler.move_file),
            w("delete_file", self.tools_handler.delete_file),
            w("create_directory", self.tools_handler.create_directory),
            w("generate_image", self.tools_handler.generate_image),
            w("compile_presentation", self.tools_handler.compile_presentation),
            w("list_presentations", self.tools_handler.list_presentations),
            w("create_presentation", self.tools_handler.create_presentation),
            w("load_presentation", self.tools_handler.load_presentation),
            w("get_presentation_summary", self.tools_handler.get_presentation_summary),
            w("open_presentation_folder", self.tools_handler.open_presentation_folder),
            w("export_pdf", self.tools_handler.export_pdf),
            w("list_templates", self.tools_handler.list_templates),
            w("preview_template", self.tools_handler.preview_template),
            w("get_aspect_ratio", self.tools_handler.get_aspect_ratio),
            w("set_aspect_ratio", self.tools_handler.set_aspect_ratio)
        ]

        # Set up history file path
        if os.environ.get('VIBE_PRESENTATION_ROOT'):
             root = os.environ.get('VIBE_PRESENTATION_ROOT')
        elif os.path.exists("presentations"):
            root = os.path.abspath("presentations")
        else:
            root = os.path.expanduser("~/.vibe_presentation")
        
        if not os.path.exists(root):
            os.makedirs(root, exist_ok=True)
            
        self.presentation_dir = os.path.join(root, presentation_context['name'])
        self.history_file = os.path.join(self.presentation_dir, "chat_history.jsonl")

        # Initialize model logic
        self.model = None
        self.chat_session = None
        self.history = [] # Local in-memory history for re-initialization

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model_names = ['gemini-3-pro-preview']
            # Initial model init (will be refreshed on chat)
            self._init_model(self._build_system_prompt())
        else:
            import sys
            # Only print warning if not in test mode
            if 'behave' not in sys.modules:
                print("Warning: GOOGLE_API_KEY not found in environment.")

    def _build_system_prompt(self):
        # Fetch dynamic content
        file_context = self.tools_handler.get_full_context()

        # Read Marp documentation
        marp_docs = ""
        try:
            with open("MARP.md", "r") as f:
                marp_docs = f.read()
        except FileNotFoundError:
            # Fallback or warn if needed, but for now just keep it empty
            pass
            
        # Get current presentation aspect ratio
        current_aspect_ratio = "4:3"  # default
        try:
            aspect_ratio = self.tools_handler.get_aspect_ratio()
            if aspect_ratio:
                current_aspect_ratio = aspect_ratio
        except Exception:
            pass
            
        # Template instructions from metadata
        template_instructions = ""
        try:
            metadata_path = os.path.join(self.presentation_dir, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    data = json.load(f)
                    if "instructions" in data and data["instructions"]:
                        template_instructions = f"\n## Branding & Template Instructions\n{data['instructions']}\n"
        except Exception:
            pass
        
        return f"""
You are "DeckBot", a helpful AI assistant for creating Marp (Markdown) presentations.

## Current Presentation Context
Name: {self.context['name']}
Description: {self.context.get('description', '')}
{template_instructions}
{file_context}

## Your Role
1. Help the user outline, write, and refine the presentation content in Markdown.
2. Manage the files directly. Use 'write_file' to create or update slides.
3. Create visuals using 'generate_image'.
4. Always keep the "Vibe" in mind: Professional but enthusiastic, clean, and modern.

## Design & Aesthetics
1. **Icons over Emojis**: Prefer using Lucide icons instead of emojis.
   - Use the following syntax to embed Lucide icons:
     `![icon-name](https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{{icon-name}}.svg)`
   - Example: `![smile](https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/smile.svg)`
   - You can resize icons using Marp syntax: `![w:32](...)`
2. **Clean Layouts**: Use ample whitespace.
3. **Visuals**: Prefer high-quality images (generated or provided) over cluttered text.

## Marp Documentation
{marp_docs}

## Current Presentation Settings
- Aspect Ratio: {current_aspect_ratio}

## Capabilities & Tools
- Use 'list_files' to see what slides exist.
- Use 'read_file' to read slide content (though full context is provided above).
- Use 'write_file' to create or update slides.
- Use 'copy_file', 'move_file', 'delete_file', 'create_directory' to organize and manage files within the presentation.
- Use 'generate_image' to create visuals. 
  - You can specify 'aspect_ratio' (e.g., "1:1", "16:9", "9:16", "4:3") and 'resolution' ("1K", "2K", "4K"). 
  - **Default aspect ratio is {current_aspect_ratio} (matching the presentation)** unless the user requests otherwise.
  - Default resolution is 2K.
  - Consider the slide layout when choosing aspect ratio - if the user asks for a "square image" use "1:1", "landscape" use "16:9", etc.
  - **IMPORTANT**: When you call this, the system will generate candidates and let the user pick. DO NOT write any files that reference the image until you receive a [SYSTEM] message confirming which image was selected.
- Use 'get_aspect_ratio' and 'set_aspect_ratio' to manage presentation aspect ratio (e.g., "16:9", "4:3"). Changing this recompiles the deck.
- Use 'compile_presentation' to BUILD and PREVIEW the actual slide deck (opens HTML). Use this when the user wants to "see the deck" or "preview".
- Use 'export_pdf' to EXPORT the deck to PDF. This requires Chrome/Chromium installed on the system.
- Use 'open_presentation_folder' to OPEN the source files for the user to edit.
- Use 'get_presentation_summary' to get a text summary of the slide deck state (titles, images, text previews). Use this for YOUR understanding or to summarize progress in chat, but NOT to "show" the deck visually.
- Use 'list_presentations', 'create_presentation', 'load_presentation' to manage decks.

## Image Generation Workflow
When the user asks for an image:
1. Call 'generate_image' with the prompt - this starts the process
2. STOP and WAIT - the system will show candidates to the user
3. The system will send you a [SYSTEM] message like: "[SYSTEM] User selected an image. It has been saved to `images/filename.png`. Please incorporate this image..."
4. ONLY THEN should you update the presentation files to reference that image path
5. After incorporating, call 'compile_presentation' if appropriate to update the preview

## Behavior
- Be proactive. If the user agrees to a plan, execute it (write the files).
- If the presentation is empty, suggest a structure.
- If the presentation has content, offer to summarize or refine it.
"""

    def _init_model(self, system_prompt):
        for model_name in self.model_names:
            try:
                self.model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt,
                    tools=self.tools_list
                )
                # Initialize chat session with existing history
                self.chat_session = self.model.start_chat(history=self.history, enable_automatic_function_calling=True)
                return
            except Exception as e:
                # Silently continue trying other models
                continue
        import sys
        # Only print error if not in test mode
        if 'behave' not in sys.modules:
            print("Error: Could not initialize any Gemini model. Please check your API key and network connection.")

    def chat(self, user_input, status_spinner=None):
        if not self.model:
            return "Error: API key not found or model initialization failed."

        # Update tools with spinner if provided
        if status_spinner:
            self.tools_handler.status_spinner = status_spinner
        
        # Reset waiting flag at the start of each turn
        self.tools_handler.waiting_for_user_input = False

        # Refresh system prompt and re-initialize model to include latest file context
        new_system_prompt = self._build_system_prompt()
        # We preserve the history from the current session
        if self.chat_session:
            self.history = self.chat_session.history
        
        self._init_model(new_system_prompt)
        
        try:
            self._log_message("user", user_input)
            response = self.chat_session.send_message(user_input)
            text_response = response.text
            self._log_message("model", text_response)
            
            # If tool set the waiting flag, append a note to the response
            if self.tools_handler.waiting_for_user_input:
                # Don't add anything to the response - it's already explained in the tool return value
                pass
            
            return text_response
        except Exception as e:
            # If tool use fails or returns something other than text, catch it.
            # With enable_automatic_function_calling=True, response.text should work after tools run.
            return f"Error communicating with AI: {str(e)}"

    def _log_message(self, role, content):
        try:
            with open(self.history_file, "a") as f:
                entry = {"role": role, "content": content}
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def load_history(self):
        if not os.path.exists(self.history_file):
            return []
        
        loaded_history = []
        try:
            with open(self.history_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        # Convert to format expected by Gemini history
                        # parts=[text], role='user'|'model'
                        loaded_history.append({
                            "role": entry["role"],
                            "parts": [entry["content"]]
                        })
                    except json.JSONDecodeError:
                        continue
            
            # Update internal history
            self.history = loaded_history
            # Re-init chat session with loaded history
            if self.model:
                self.chat_session = self.model.start_chat(history=self.history, enable_automatic_function_calling=True)
                
            return loaded_history
        except Exception:
            return []

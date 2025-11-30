import os
import json
from google import genai
from google.genai import types
from rich.console import Console
from deckbot.nano_banana import NanoBananaClient
from deckbot.tools import PresentationTools

class Agent:
    def __init__(self, presentation_context):
        self.context = presentation_context
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        # Check for deprecated GEMINI_API_KEY and warn user
        if not self.api_key and os.getenv("GEMINI_API_KEY"):
            print("Warning: GEMINI_API_KEY is set but deprecated. Please use GOOGLE_API_KEY instead.")
            print("  export GOOGLE_API_KEY=$GEMINI_API_KEY")
            # For now, fall back to GEMINI_API_KEY for backwards compatibility
            self.api_key = os.getenv("GEMINI_API_KEY")
        
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
            w("set_aspect_ratio", self.tools_handler.set_aspect_ratio),
            w("go_to_slide", self.tools_handler.go_to_slide)
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
        self.client = None

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            # Try models in order of preference
            self.model_names = [
                'gemini-2.0-flash-exp',
                'gemini-exp-1206',
                'gemini-1.5-pro',
                'gemini-1.5-flash'
            ]
            # Initial model init (will be refreshed on chat)
            self._init_model(self._build_system_prompt())
        else:
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
            
        # Template instructions and design opinions from metadata
        template_instructions = ""
        design_opinions_section = ""
        try:
            metadata_path = os.path.join(self.presentation_dir, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    data = json.load(f)
                    if "instructions" in data and data["instructions"]:
                        template_instructions = f"\n## Branding & Template Instructions\n{data['instructions']}\n"
                    
                    # Build design opinions section if defined
                    if "design_opinions" in data and data["design_opinions"]:
                        opinions = data["design_opinions"]
                        design_opinions_section = "\n## Design & Aesthetics\n"
                        
                        # Handle icon preference
                        if "icons" in opinions:
                            if opinions["icons"] == "lucide":
                                design_opinions_section += """1. **Icons over Emojis**: Prefer using Lucide icons instead of emojis.
   - Use the following syntax to embed Lucide icons:
     `![icon-name](https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{{icon-name}}.svg)`
   - Example: `![smile](https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/smile.svg)`
   - You can resize icons using Marp syntax: `![w:32](...)`
"""
                            elif opinions["icons"] == "emoji":
                                design_opinions_section += "1. **Icons**: Use emojis for visual interest.\n"
                            elif opinions["icons"] == "none":
                                design_opinions_section += "1. **Icons**: Avoid using icons or emojis unless specifically requested.\n"
                        
                        # Handle color palette
                        if "color_palette" in opinions and opinions["color_palette"]:
                            colors = ", ".join(opinions["color_palette"])
                            design_opinions_section += f"2. **Color Palette**: Prefer these colors: {colors}\n"
                        
                        # Handle typography style
                        if "typography_style" in opinions:
                            design_opinions_section += f"3. **Typography Style**: {opinions['typography_style']}\n"
                        
                        design_opinions_section += "\n"
        except Exception:
            pass
        
        # Get current presentation aspect ratio
        current_aspect_ratio = "4:3"  # default
        try:
            aspect_ratio = self.tools_handler.get_aspect_ratio()
            if aspect_ratio:
                current_aspect_ratio = aspect_ratio
        except Exception:
            pass

        final_design_section = design_opinions_section if design_opinions_section else """
## Design & Aesthetics
1. **Clean Layouts**: Use ample whitespace.
2. **Visuals**: Prefer high-quality images (generated or provided) over cluttered text.
"""
        
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

{final_design_section}

## Marp Documentation
{marp_docs}

## Current Presentation Settings
- Aspect Ratio: {current_aspect_ratio}
- Note: Do NOT repeatedly check 'get_aspect_ratio' unless you have a reason to believe it changed.

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
  - **IMPORTANT**: You can optionally pass a 'slide_number' (integer) to open the presentation directly at that slide. E.g., `compile_presentation(slide_number=5)`.
- Use 'go_to_slide' to navigate to a specific slide (e.g., `go_to_slide(slide_number=3)`) WITHOUT recompiling. Use this when the deck is already built and you just want to change the view.
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
        if not self.client:
            return
            
        for model_name in self.model_names:
            try:
                # Store the model name and system prompt for later use
                self.model_name = model_name
                self.system_prompt = system_prompt
                self.model = model_name  # Just store the name
                # Chat session will be created when we actually send messages
                self.chat_session = True  # Flag to indicate model is ready
                return
            except Exception as e:
                # print(f"Failed to init {model_name}: {e}") # Debugging
                continue
        print("Error: Could not initialize any Gemini model. Please check your API key and network connection.")

    def chat(self, user_input, status_spinner=None):
        if not self.model or not self.client:
            return "Error: API key not found or model initialization failed."

        # Update tools with spinner if provided
        if status_spinner:
            self.tools_handler.status_spinner = status_spinner
        
        # Reset waiting flag at the start of each turn
        self.tools_handler.waiting_for_user_input = False

        # Refresh system prompt to include latest file context
        new_system_prompt = self._build_system_prompt()
        self.system_prompt = new_system_prompt
        
        try:
            self._log_message("user", user_input)
            
            # Build message history for the API call
            # Convert our internal history format to the new API format
            contents = []
            
            # Add system instruction as first message
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=f"[System Instructions]\n{new_system_prompt}\n\n[User Message]\n{user_input}")]
            ))
            
            # Make the API call with automatic function calling
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        tools=self.tools_list,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=False
                        )
                    )
                )
            except KeyError as ke:
                # If automatic function calling fails to find a tool
                import traceback
                traceback.print_exc()
                return f"Error: Tool not found or failed to execute: {repr(ke)}. Available tools: {[t.__name__ if hasattr(t, '__name__') else str(t) for t in self.tools_list[:5]]}"
            
            # Extract text from response
            text_response = ""
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_response += part.text
            
            if not text_response:
                text_response = "I understand, but I don't have a response at the moment."
            
            self._log_message("model", text_response)
            
            # If tool set the waiting flag, append a note to the response
            if self.tools_handler.waiting_for_user_input:
                # Don't add anything to the response - it's already explained in the tool return value
                pass
            
            return text_response
        except Exception as e:
            # If tool use fails or returns something other than text, catch it.
            import traceback
            traceback.print_exc()
            return f"Error communicating with AI: {repr(e)}"

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
            # Chat session will be created lazily when first message is sent
            # with the loaded history included
                
            return loaded_history
        except Exception:
            return []

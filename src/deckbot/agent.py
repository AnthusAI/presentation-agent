import os
import json
from google import genai
from google.genai import types
from rich.console import Console
from deckbot.nano_banana import NanoBananaClient
from deckbot.tools import PresentationTools
from deckbot.preferences import PreferencesManager

class Agent:
    def __init__(self, presentation_context, root_dir=None):
        self.context = presentation_context
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        # Initialize preferences
        self.prefs = PreferencesManager()
        
        # Check for deprecated GEMINI_API_KEY and warn user

        if not self.api_key and os.getenv("GEMINI_API_KEY"):
            print("Warning: GEMINI_API_KEY is set but deprecated. Please use GOOGLE_API_KEY instead.")
            print("  export GOOGLE_API_KEY=$GEMINI_API_KEY")
            # For now, fall back to GEMINI_API_KEY for backwards compatibility
            self.api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize tools
        # Pass root_dir to NanoBananaClient
        self.nano_client = NanoBananaClient(presentation_context, root_dir=root_dir)
        self.tools_handler = PresentationTools(presentation_context, self.nano_client, root_dir=root_dir, api_key=self.api_key)
        
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
            w("replace_text", self.tools_handler.replace_text),
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
            w("go_to_slide", self.tools_handler.go_to_slide),
            w("inspect_slide", self.tools_handler.inspect_slide),
            w("validate_deck", self.tools_handler.validate_deck),
            w("remix_slide", self.tools_handler.remix_slide),
            w("remix_image", self.tools_handler.remix_image)
        ]

        # Set up history file path
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
            
            # Load models from preferences
            primary_model = self.prefs.get('primary_model', 'gemini-3-pro-preview')
            secondary_model = self.prefs.get('secondary_model', 'gemini-2.0-flash-exp')
            self.secondary_model_name = secondary_model

            # Log model configuration
            print(f"Primary Model: {primary_model}")
            print(f"Secondary Model: {secondary_model}")

            # Try models in order of preference
            self.model_names = [
                primary_model,
                secondary_model,
                'gemini-2.0-flash-exp',
                'gemini-exp-1206',
                'gemini-1.5-pro',
                'gemini-1.5-flash'
            ]
            # Remove duplicates while preserving order
            self.model_names = list(dict.fromkeys(self.model_names))
            
            # Initial model init (will be refreshed on chat)
            self._init_model(self._build_system_prompt())
        else:
            print("Warning: GOOGLE_API_KEY not found in environment.")
            
        # Subscribe to tool events for logging
        self.tools_handler.add_tool_listener(self._on_tool_event)
        
        # Load history
        self.load_history()

    def _build_system_prompt(self, current_slide=None):
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
                            if isinstance(opinions["color_palette"], list):
                                colors = ", ".join(opinions["color_palette"])
                            else:
                                colors = str(opinions["color_palette"])
                            design_opinions_section += f"2. **Color Palette**: Prefer these colors: {colors}\n"
                        
                        # Handle typography style
                        if "typography_style" in opinions:
                            design_opinions_section += f"3. **Typography Style**: {opinions['typography_style']}\n"
                        
                        # Handle all other keys generically
                        for key, value in opinions.items():
                            if key not in ["icons", "color_palette", "typography_style"]:
                                design_opinions_section += f"- **{key}**: {value}\n"
                        
                        design_opinions_section += "\n"
        except Exception:
            pass
        
        # Load available layouts
        layouts_section = ""
        try:
            layouts_path = os.path.join(self.presentation_dir, "layouts.md")
            if os.path.exists(layouts_path):
                with open(layouts_path, "r") as f:
                    layouts_content = f.read()
                
                # Parse layout names from HTML comments
                import re
                layout_names = re.findall(r'<!-- layout: ([\w-]+) -->', layouts_content)
                
                if layout_names:
                    layouts_section = "\n## Available Layouts\n"
                    layouts_section += "This presentation includes pre-designed slide layouts. Use the 'get_layouts' tool to see full details, or reference these layouts when creating slides:\n\n"
                    
                    # Parse all layout metadata
                    for layout_name in layout_names:
                        # Find this layout's metadata in the content
                        layout_start = layouts_content.find(f'<!-- layout: {layout_name} -->')
                        if layout_start >= 0:
                            # Find next layout or end of file
                            next_layout = layouts_content.find('<!-- layout:', layout_start + 1)
                            layout_section = layouts_content[layout_start:next_layout if next_layout > 0 else len(layouts_content)]
                            
                            # Extract metadata
                            image_friendly = re.search(r'<!-- image-friendly: (true|false) -->', layout_section)
                            aspect_ratio = re.search(r'<!-- recommended-aspect-ratio: ([\d:]+) -->', layout_section)
                            description = re.search(r'<!-- description: (.+?) -->', layout_section)
                            
                            desc_text = description.group(1) if description else f"{layout_name} layout"
                            layouts_section += f"- **{layout_name}**: {desc_text}"
                            
                            if image_friendly and image_friendly.group(1) == "true":
                                layouts_section += f" ✓ Image-friendly"
                                if aspect_ratio:
                                    layouts_section += f" (best aspect ratio: {aspect_ratio.group(1)})"
                            
                            layouts_section += "\n"
                    
                    layouts_section += "\n**Important for Image Generation**: When generating images for specific layouts, use the recommended aspect ratio for that layout. Call 'get_layouts()' to see all layout details including aspect ratio recommendations.\n"
        except Exception:
            pass
        
        # Get current presentation aspect ratio
        current_aspect_ratio = "4:3"  # default
        try:
            aspect_ratio = self.tools_handler.manager.get_presentation_aspect_ratio(self.context['name'])
            if aspect_ratio:
                current_aspect_ratio = aspect_ratio
        except Exception:
            pass

        final_design_section = design_opinions_section if design_opinions_section else """
## Design & Aesthetics
1. **Clean Layouts**: Use ample whitespace.
2. **Visuals**: Prefer high-quality images (generated or provided) over cluttered text.
"""

        # Build current slide context
        slide_context = ""
        if current_slide:
            slide_context = f"""
## Current User Context
The user is currently viewing **slide {current_slide}**. When using navigation tools like 'go_to_slide()' or 'compile_presentation()', keep this context in mind. The user's focus is on this slide.
"""

        return f"""
You are "DeckBot", a helpful AI assistant for creating Marp (Markdown) presentations.

## Current Presentation Context
Name: {self.context['name']}
Description: {self.context.get('description', '')}
{template_instructions}
{slide_context}
## Context - Read this First!
The following files are the CURRENT content of the presentation.
You do NOT need to call 'read_file' for these files.
{file_context}

## Your Role
1. Help the user outline, write, and refine the presentation content in Markdown.
2. Manage the files directly. Use 'write_file' to create or update slides.
3. Create visuals using 'generate_image'.
4. Always keep the "Vibe" in mind: Professional but enthusiastic, clean, and modern.

{final_design_section}
{layouts_section}

## Image Sizing & Styling with Marp

**IMPORTANT**: Marp provides special directives for controlling image sizes. These directives are placed in the image's alt text (the brackets in `![...](...)`).

### Sizing Syntax
Use these directives in the alt text to control image dimensions:

```markdown
![w:200px](image.jpg)          # Width only
![h:150px](image.jpg)          # Height only
![w:300px h:200px](image.jpg)  # Both width and height
![width:200px](image.jpg)      # Alternative syntax
![height:150px](image.jpg)     # Alternative syntax
```

**Supported units**: `px`, `cm`, `mm`, `in`, `pt`, `pc`, `em`, `%`

### Common Use Cases

1. **Small inline icons or decorations**:
   ```markdown
   ![w:32px](icon.svg) This is an icon
   ```

2. **Constrained images in layouts**:
   ```markdown
   ![w:250px](portrait-photo.jpg)
   ```

3. **Specific aspect ratios**:
   ```markdown
   ![w:400px h:300px](screenshot.png)
   ```

### How CSS and Marp Directives Interact

- **Layout CSS uses `max-width: 100%`** (not `width: 100%`) to allow Marp sizing directives to work
- This means:
  - Images will **never exceed** their container width
  - But they **can be smaller** when you use Marp sizing directives
  - Without sizing directives, images will naturally fit their container

### Styling with CSS

You can **combine** Marp sizing directives with CSS styling:

```markdown
![w:200px](image.jpg)
```

Then add CSS rules for borders, shadows, etc:

```css
img {{
  border: 3px solid #333;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}}
```

**What works**:
- Borders, shadows, filters, transforms, opacity, etc. (any non-sizing CSS)
- Marp sizing directives control the dimensions
- CSS controls the appearance

**What doesn't work**:
- CSS rules that set `width: 100%` will override Marp sizing (but layouts use `max-width: 100%` to avoid this)

### Best Practices

1. **Use Marp directives for sizing**: `![w:200px](...)` instead of relying on CSS
2. **Use CSS for styling**: borders, shadows, colors, effects
3. **Test your sizing**: If images aren't responding to size directives, check for conflicting CSS `width` or `height` rules
4. **Be specific**: `![w:150px](...)` is clearer than hoping CSS will size it correctly

## Marp Documentation
{marp_docs}

        ## Current Presentation Settings
        - Aspect Ratio: {current_aspect_ratio} (Provided by system - DO NOT call 'get_aspect_ratio' to check this)
        - Note: Only use 'set_aspect_ratio' if the user explicitly asks to change it.

## Capabilities & Tools
- Use 'list_files' to see what slides exist.
  - **Note**: `list_files` returns items in **reverse-chronological order** (newest first). The first file listed is the most recently created/modified.
  - Generated image batches are stored in the `drafts/` directory. Use `list_files('drafts')` to find previously generated images.
- Use 'read_file' ONLY for files NOT listed in the context above (e.g., logs, data files). 
  - **DO NOT use 'read_file' for deck.marp.md or other markdown files provided in the 'Current Presentation Context'.** 
  - Reading them again is redundant and wastes resources.
- Use 'create_slide_with_layout' to create a SINGLE new slide using a layout template.
  - **IMPORTANT**: Use this tool when the user wants to create ONLY ONE new slide.
  - This triggers an interactive UI where the user selects from visual layout previews (similar to image generation).
  - You call the tool → System shows layouts → User picks one → Slide is created automatically.
  - **DO NOT use this tool if the user wants multiple slides** - instead, create multiple slides manually using 'replace_text' or 'write_file', since the UI only allows selecting one layout at a time.
- Use 'replace_text' to safely edit part of a file (e.g., insert an image link, change a title) without rewriting the whole file.
  - **ALWAYS prefer 'replace_text' for small edits to existing files.**
  - **Use this for creating MULTIPLE slides** by adding them to deck.marp.md.
  - **Note**: Automatically recompiles the presentation. You do not need to call 'compile_presentation' manually.
- Use 'write_file' to create NEW files or completely OVERWRITE existing files.
  - **WARNING**: 'write_file' replaces the ENTIRE content of the file. If you use it on an existing file, you MUST provide the COMPLETE new content (including all existing slides), otherwise you will delete user data.
  - **Note**: Automatically recompiles the presentation.
- Use 'copy_file', 'move_file', 'delete_file', 'create_directory' to organize and manage files within the presentation.
- Use 'generate_image' to create visuals. 
  - You can specify 'aspect_ratio' (e.g., "1:1", "16:9", "9:16", "4:3") and 'resolution' ("1K", "2K", "4K"). 
  - **Default aspect ratio is {current_aspect_ratio} (matching the presentation)** unless the user requests otherwise.
  - Default resolution is 2K.
  - Consider the slide layout when choosing aspect ratio - if the user asks for a "square image" use "1:1", "landscape" use "16:9", etc.
  - **CRITICAL - PROMPT FIDELITY**: The 'prompt' parameter goes directly to the image generation model. You MUST include ALL user-specified details, constraints, and style requirements in the prompt. Do NOT summarize or simplify the user's request.
    - If user says "no title" → include "no title" in prompt
    - If user says "flat design, no shadows" → include "flat design, no shadows" in prompt  
    - If user says "blue bars and red line" → include "blue bars and red line" in prompt
    - Only omit non-visual details like "for page 1" or "add this to slide 3"
    - Preserve negative constraints (no X, without Y, avoid Z) - these are critical for the image model
  - **IMPORTANT**: When you call this, the system will generate candidates and let the user pick. DO NOT write any files that reference the image until you receive a [SYSTEM] message confirming which image was selected.
- Use 'get_aspect_ratio' and 'set_aspect_ratio' to manage presentation aspect ratio (e.g., "16:9", "4:3"). Changing this recompiles the deck.
- Use 'compile_presentation' to BUILD and PREVIEW the actual slide deck (opens HTML). Use this when the user wants to "see the deck" or "preview".
  - **IMPORTANT**: Do NOT call this after using 'write_file' or 'replace_text', as those tools automatically recompile. Only use this if you need to force a recompile or open a specific slide.
  - **IMPORTANT**: You can optionally pass a 'slide_number' (integer) to open the presentation directly at that slide. E.g., `compile_presentation(slide_number=5)`.
  - **NOTE**: This tool does NOT automatically run visual inspection. If you want to verify the visual layout, you MUST call 'inspect_slide' afterwards.
- Use 'go_to_slide' to navigate to a specific slide (e.g., `go_to_slide(slide_number=3)`) WITHOUT recompiling. Use this when the deck is already built and you just want to change the view.
  - **NOTE**: This tool does NOT automatically run visual inspection. If you want to verify the visual layout, you MUST call 'inspect_slide' afterwards.
- Use 'inspect_slide' to visually check a specific slide for errors.
  - **USE THIS** after 'go_to_slide' or 'compile_presentation' if you suspect layout issues or want to verify a fix.
  - It will return a detailed visual report and alert you to critical issues like content overflow.
- Use 'validate_deck' to check the deck for syntax errors (CSS, frontmatter) without modifying it.
  - Use this if the user reports formatting issues or if you want to verify your changes are valid.
- Use 'export_pdf' to EXPORT the deck to PDF. This requires Chrome/Chromium installed on the system.
- Use 'open_presentation_folder' to OPEN the source files for the user to edit.
- Use 'get_presentation_summary' to get a text summary of the slide deck state (titles, images, text previews). Use this for YOUR understanding or to summarize progress in chat, but NOT to "show" the deck visually.
- Use 'list_presentations', 'create_presentation', 'load_presentation' to manage decks.
- Use 'remix_slide' to remix an entire slide by rendering it to an image and generating a remixed version.
  - **CRITICAL**: Use this when the user says "remix this slide", "remix slide X", "remix the slide", or any variation asking to remix a SLIDE
  - The tool renders the entire slide (including all text, images, and layout) to an image first, then generates remixed candidates
  - After selection, the remixed image will replace the ENTIRE slide contents by overlaying the image
  - Requires 'slide_number' (integer) - use the current slide number if user says "this slide" or "the slide"
  - Requires 'remix_prompt' (string describing the transformation, e.g., "make it look like everything is on fire")
  - **DO NOT use 'remix_image' when the user asks to remix a slide** - always use 'remix_slide' for slide remixing
- Use 'remix_image' to remix a specific existing image file.
  - **CRITICAL**: Only use this when the user explicitly mentions an IMAGE FILE by name or path (e.g., "remix images/logo.png")
  - The tool uses the existing image file as a reference and generates remixed candidates
  - After selection, the remixed image will replace the original image file and all references to it
  - Requires 'image_path' (string, relative to presentation directory, e.g., "images/logo.png")
  - Requires 'remix_prompt' (string describing the transformation)
  - **IMPORTANT**: If the user says "remix this slide" or "remix slide X", you MUST use 'remix_slide', NOT 'remix_image'

## Image Generation Workflow
When the user asks for an image:
1. Call 'generate_image' with the prompt - this starts the process
2. STOP and WAIT - the system will show candidates to the user
3. The system will send you a SYSTEM message indicating which image was selected, including:
   - A batch ID identifying which generation request this selection came from
   - The file path where the image was saved (e.g., images/selected_image.png)
   - If you see a SYSTEM message with an old batch ID while working on a NEW image request, IGNORE the old selection
   - Only act on SYSTEM messages that correspond to the CURRENT image generation batch
4. ONLY THEN should you update the presentation files to reference that image path
5. After incorporating, you MUST call 'compile_presentation' immediately to update the preview for the user. Do not ask for permission.

**Important**: Each image generation creates a new batch with a unique ID. Previous SYSTEM messages in the history may reference old batches - these are for context only and should NOT be re-processed.

## Behavior
- Be proactive. If the user agrees to a plan, execute it (write the files).
- If the presentation is empty, suggest a structure.
- If the presentation has content, offer to summarize or refine it.
"""

    def _on_tool_event(self, event, data):
        """Log tool usage to history."""
        if event == "tool_start":
            # Log function call with normalized args
            # Use normalized_args if available, otherwise fall back to kwargs
            normalized_args = data.get("args", {})
            if not normalized_args:
                # Fallback for old format
                normalized_args = data.get("kwargs", {}).copy()
            
            part = types.Part(
                function_call=types.FunctionCall(
                    name=data["tool"],
                    args=normalized_args
                )
            )
            self._log_message("model", parts=[part])
            
        elif event == "tool_end":
            # Log function response
            part = types.Part(
                function_response=types.FunctionResponse(
                    name=data["tool"],
                    response={"result": data["result"]} 
                )
            )
            # Role for function response
            self._log_message("tool", parts=[part])
            
        elif event == "tool_error":
             # Log error
             part = types.Part(
                function_response=types.FunctionResponse(
                    name=data["tool"],
                    response={"error": data["error"]}
                )
             )
             self._log_message("tool", parts=[part])

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

    def _generate_with_fallback(self, contents):
        """
        Attempt generation with current model. 
        If 429/Resource Exhausted occurs, switch to secondary model and retry.
        """
        try:
            return self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=self.tools_list,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=False
                    )
                )
            )
        except Exception as e:
            # Check for Resource Exhausted error
            error_str = str(e)
            # print(f"DEBUG: Error string: {error_str}") # Debug
            is_resource_exhausted = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str
            
            if is_resource_exhausted:
                # print(f"DEBUG: Resource exhausted. Current: {self.model_name}, Secondary: {self.secondary_model_name}")
                # If we haven't switched yet and have a secondary model
                if self.model_name != self.secondary_model_name and self.secondary_model_name:
                    print(f"Resource exhausted on {self.model_name}. Switching to secondary model: {self.secondary_model_name}")
                    self.model_name = self.secondary_model_name
                    
                    # Retry with new model
                    return self.client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            tools=self.tools_list,
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                                disable=False
                            )
                        )
                    )
            # Re-raise if not handled
            raise e

    def chat(self, user_input, status_spinner=None, cancelled_flag=None, current_slide=None):
        if not self.model or not self.client:
            return "Error: API key not found or model initialization failed."

        # Check for cancellation at start
        if cancelled_flag and cancelled_flag.is_cancelled():
            return "Request cancelled by user."

        # Update tools with spinner if provided
        if status_spinner:
            self.tools_handler.status_spinner = status_spinner

        # Reset waiting flag at the start of each turn
        self.tools_handler.waiting_for_user_input = False

        # Refresh system prompt to include latest file context and current slide
        new_system_prompt = self._build_system_prompt(current_slide=current_slide)
        self.system_prompt = new_system_prompt
        
        try:
            # Note: User message may already be logged by /api/chat endpoint
            # Check if it's already in history to avoid duplicates
            should_log = True
            if self.history and len(self.history) > 0:
                last_entry = self.history[-1]
                if last_entry.get("role") == "user":
                    parts = last_entry.get("parts", [])
                    if parts and hasattr(parts[0], 'text') and parts[0].text == user_input:
                        should_log = False

            if should_log:
                self._log_message("user", user_input)
            
            # Build message history for the API call
            # Convert our internal history format to the new API format
            contents = []
            
            # Add system instruction as first message
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=f"[System Instructions]\n{new_system_prompt}")]
            ))
            
            # Add conversation history if it exists
            for msg in self.history:
                # Trust the role from history
                role = msg.get("role", "user")
                
                msg_parts = msg.get("parts", [])
                content_parts = []
                
                for p in msg_parts:
                    if isinstance(p, types.Part):
                        content_parts.append(p)
                    elif isinstance(p, str):
                        content_parts.append(types.Part(text=p))
                    # If other types (dict), assume already handled or ignore?
                    # load_history ensures types.Part.
                
                if content_parts:
                    contents.append(types.Content(
                        role=role,
                        parts=content_parts
                    ))
            
            # Add current user message
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            ))
            
            # Emit request details if callback is set (web mode)
            if hasattr(self.tools_handler, 'on_agent_request'):
                request_details = {
                    'user_message': user_input,
                    'system_prompt': new_system_prompt,
                    'model': self.model_name
                }
                self.tools_handler.on_agent_request(request_details)
            
            # Check for cancellation before API call
            if cancelled_flag and cancelled_flag.is_cancelled():
                return "Request cancelled by user."
            
            # Make the API call with automatic function calling
            try:
                response = self._generate_with_fallback(contents)
                
                # Check for cancellation after API call
                if cancelled_flag and cancelled_flag.is_cancelled():
                    return "Request cancelled by user."
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
                        # Also check function responses for tool return values
                        elif hasattr(part, 'function_response') and part.function_response:
                            # Extract response text from function response if available
                            func_response = part.function_response
                            if hasattr(func_response, 'response') and func_response.response:
                                # Function response might be a string or dict
                                if isinstance(func_response.response, str):
                                    text_response += func_response.response
                                elif isinstance(func_response.response, dict) and 'text' in func_response.response:
                                    text_response += func_response.response['text']
            
            if not text_response:
                # If we're waiting for user input (e.g., image selection), don't return a generic message
                # The tool return value should already explain what's happening via tool_end event
                if self.tools_handler.waiting_for_user_input:
                    text_response = ""  # Return empty string - the tool message already explains the wait
                else:
                    text_response = "I understand, but I don't have a response at the moment."
            
            # If tool set the waiting flag, don't log an empty response
            # The tool return value already explains what's happening
            if text_response or not self.tools_handler.waiting_for_user_input:
                self._log_message("model", text_response)
            
            # If tool set the waiting flag, don't add anything - it's already explained in the tool return value
            if self.tools_handler.waiting_for_user_input:
                # Return the tool's message (which should explain the wait state)
                # If text_response is empty, that's fine - the tool message was already shown
                pass
            
            return text_response
        except Exception as e:
            # If tool use fails or returns something other than text, catch it.
            import traceback
            traceback.print_exc()
            return f"Error communicating with AI: {repr(e)}"

    def _log_message(self, role, content=None, parts=None):
        # Keep SYSTEM messages in history - they provide important context
        # about which batch an image selection came from
        try:
            with open(self.history_file, "a") as f:
                entry = {"role": role}
                if parts:
                    # Serialize parts
                    serialized_parts = []
                    for p in parts:
                        if isinstance(p, types.Part):
                            part_dict = {}
                            if p.text: part_dict['text'] = p.text
                            if p.function_call: 
                                part_dict['function_call'] = {
                                    'name': p.function_call.name,
                                    'args': p.function_call.args
                                }
                            if p.function_response:
                                part_dict['function_response'] = {
                                    'name': p.function_response.name,
                                    'response': p.function_response.response
                                }
                            serialized_parts.append(part_dict)
                        elif isinstance(p, dict):
                            serialized_parts.append(p)
                        else:
                            # Fallback for simple text in parts
                            serialized_parts.append({"text": str(p)})
                    entry["parts"] = serialized_parts
                else:
                    entry["content"] = content
                f.write(json.dumps(entry) + "\n")
            
            # Update in-memory history
            mem_parts = []
            if parts:
                mem_parts = parts
            else:
                mem_parts = [types.Part(text=content)]
            
            self.history.append({"role": role, "parts": mem_parts})
            
        except Exception as e:
            print(f"Error logging message: {e}")

    def load_history(self):
        if not os.path.exists(self.history_file):
            return []
        
        loaded_history = []
        try:
            with open(self.history_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        role = entry["role"]
                        parts = []
                        
                        if "parts" in entry:
                            for p_data in entry["parts"]:
                                part = types.Part()
                                if "text" in p_data:
                                    part.text = p_data["text"]
                                if "function_call" in p_data:
                                    fc = p_data["function_call"]
                                    part.function_call = types.FunctionCall(
                                        name=fc["name"],
                                        args=fc["args"]
                                    )
                                if "function_response" in p_data:
                                    fr = p_data["function_response"]
                                    part.function_response = types.FunctionResponse(
                                        name=fr["name"],
                                        response=fr["response"]
                                    )
                                parts.append(part)
                        elif "content" in entry:
                             parts.append(types.Part(text=entry["content"]))
                             
                        loaded_history.append({
                            "role": role,
                            "parts": parts 
                        })
                    except json.JSONDecodeError:
                        continue
            
            self.history = loaded_history
            return loaded_history
        except Exception:
            return []

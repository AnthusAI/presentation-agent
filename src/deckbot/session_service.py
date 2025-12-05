import os
import json
import threading
from typing import Optional, List, Dict, Callable, Any
from datetime import datetime
from deckbot.agent import Agent
from deckbot.nano_banana import NanoBananaClient

class SessionService:
    def __init__(self, presentation_context: Dict[str, Any]):
        self.context = presentation_context
        self.agent = Agent(presentation_context)
        # NanoClient is also initialized inside Agent, but we might want direct access or share the instance.
        # Agent creates its own NanoBananaClient. We should probably use the one from the agent 
        # or modify Agent to accept one. For now, we'll access it via agent.nano_client
        self.nano_client = self.agent.nano_client
        
        self.listeners: List[Callable[[str, Any], None]] = []
        self._lock = threading.Lock()
        
        # Web-specific state
        self.pending_candidates: List[str] = []
        self.last_image_prompt: str = ""
        
        # Cancellation flag
        self._cancelled = False
        
        # Chat history file path (same as agent's history file)
        self.history_file = getattr(self.agent, 'history_file', None)

        # Web-specific state for layout selection
        self.pending_layout_request = None
        
        # Hook presentation updates
        if hasattr(self.agent, 'tools_handler'):
            # Accept slide_number (or any data) and forward it
            self.agent.tools_handler.on_presentation_updated = lambda data=None: self._notify("presentation_updated", data)
            # Hook image generation requests from the agent
            self.agent.tools_handler.on_image_generation = self._handle_agent_image_request
            # Hook layout creation requests from the agent
            self.agent.tools_handler.on_layout_request = self._handle_layout_request
            # Hook tool events
            self.agent.tools_handler.on_tool_call = self._handle_tool_event
            # Hook agent request details
            self.agent.tools_handler.on_agent_request = self._handle_agent_request_details

    def subscribe(self, callback: Callable[[str, Any], None]):
        """Subscribe to events. Callback receives (event_type, data)."""
        with self._lock:
            self.listeners.append(callback)

    def _handle_tool_event(self, event_type: str, data: Any):
        """Forward tool events to listeners."""
        self._notify(event_type, data)
        
        # Log tool_image events to chat history
        if event_type == "tool_image":
            self._log_rich_message(
                message_type="tool_image",
                role="system",
                data=data
            )

    def _handle_agent_request_details(self, details: Dict[str, Any]):
        """Handle agent request details - notify and log."""
        self._notify("agent_request_details", details)
        self._log_agent_request_details(details)

    def _notify(self, event_type: str, data: Any = None):
        with self._lock:
            for listener in self.listeners:
                try:
                    listener(event_type, data)
                except Exception as e:
                    print(f"Error in listener: {e}")

    def _log_rich_message(self, message_type: str, role: str, data: Dict[str, Any], content: str = None):
        """
        Log a rich message to chat_history.jsonl for UI reconstruction.
        
        Args:
            message_type: Type of message (e.g., 'image_request_details', 'image_candidate')
            role: Message role (user, model, system)
            data: Message data dictionary
            content: Optional text content for the message
        """
        # Skip logging if history file not available (e.g., in tests)
        if not self.history_file:
            return
            
        try:
            entry = {
                "role": role,
                "message_type": message_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data
            }
            if content:
                entry["content"] = content
            
            with open(self.history_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # Silently fail in test environments
            pass

    def _log_image_request_details(self, details: Dict[str, Any]):
        """Log image generation request details for UI reconstruction."""
        self._log_rich_message(
            message_type="image_request_details",
            role="system",
            data=details
        )

    def _log_image_candidate(self, image_path: str, index: int, batch_slug: str):
        """Log individual image candidate for UI reconstruction."""
        self._log_rich_message(
            message_type="image_candidate",
            role="system",
            data={
                "image_path": image_path,
                "index": index,
                "batch_slug": batch_slug
            }
        )

    def _log_image_selection(self, index: int, batch_slug: str, filename: str, saved_path: str):
        """Log image selection for UI reconstruction."""
        self._log_rich_message(
            message_type="image_selection",
            role="system",
            data={
                "index": index,
                "batch_slug": batch_slug,
                "filename": filename,
                "saved_path": saved_path
            }
        )

    def _log_agent_request_details(self, details: Dict[str, Any]):
        """Log agent request details for UI reconstruction."""
        # Store details alongside the user message
        self._log_rich_message(
            message_type="agent_request_details",
            role="user",
            data=details,
            content=details.get('user_message', '')
        )

    def send_message(self, user_input: str, status_spinner=None, current_slide=None) -> str:
        """Send a message to the agent and get the response."""
        # Clear cancellation flag at start of new request
        self._cancelled = False

        # Emit user message so it appears in chat
        self._notify("message", {"role": "user", "content": user_input})
        self._notify("thinking_start")
        try:
            response = self.agent.chat(
                user_input,
                status_spinner=status_spinner,
                cancelled_flag=self,
                current_slide=current_slide
            )
            self._notify("message", {"role": "model", "content": response})
            return response
        except Exception as e:
            if self._cancelled:
                error_msg = "Request cancelled by user."
                self._notify("message", {"role": "model", "content": error_msg})
                return error_msg
            error_msg = f"Error: {str(e)}"
            print(f"Agent error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self._notify("message", {"role": "model", "content": error_msg})
            return error_msg
        finally:
            self._notify("thinking_end")
    
    def cancel(self):
        """Cancel the current request."""
        self._cancelled = True
    
    def is_cancelled(self):
        """Check if the current request is cancelled."""
        return self._cancelled

    def _handle_agent_image_request(self, prompt: str, aspect_ratio: str = "1:1", resolution: str = "2K", remix_reference_image=None, remix_slide_number=None, remix_image_path=None):
        """
        Called when agent's generate_image tool is invoked (web mode).
        
        This is the deterministic system workflow:
        1. Generate 4 candidates (with progress updates)
        2. Display each image in chat as individual messages
        3. Wait for user selection (handled by select_image method)
        4. Save selected image (handled by select_image method)
        5. Notify agent with filename (handled by select_image method)
        """
        # Generate images in the background and notify via SSE
        import threading
        import traceback
        def _generate():
            self.last_image_prompt = prompt
            batch_slug_sent = False
            sent_candidate_count = 0  # Track how many candidates we've already sent
            current_batch_slug = None  # Track batch slug locally across progress callbacks
            
            # Capture remix_reference_image and metadata in closure
            remix_ref = remix_reference_image
            remix_slide = remix_slide_number
            remix_img_path = remix_image_path
            
            def progress(current, total, status, current_candidates, prompt_details=None):
                nonlocal batch_slug_sent, sent_candidate_count, current_batch_slug
                
                # Send request details on first progress update
                if prompt_details and not batch_slug_sent:
                    # Generate batch slug for this request
                    from deckbot.nano_banana import generate_batch_slug
                    current_batch_slug = generate_batch_slug(prompt)
                    prompt_details['batch_slug'] = current_batch_slug
                    self._notify("image_request_details", prompt_details)
                    # Log request details to chat history
                    self._log_image_request_details(prompt_details)
                    batch_slug_sent = True
                
                # Send progress update
                self._notify("image_progress", {
                    "current": current, 
                    "total": total, 
                    "status": status
                })
                
                # Send only NEW candidates (ones we haven't sent yet)
                if current_candidates:
                    candidates_to_send = current_candidates[sent_candidate_count:]
                    for idx, candidate_path in enumerate(candidates_to_send):
                        actual_index = sent_candidate_count + idx
                        # Use the local batch slug that was set on first progress callback
                        batch_slug = current_batch_slug or ''
                        self._notify("image_candidate", {
                            "image_path": candidate_path,
                            "index": actual_index,
                            "batch_slug": batch_slug
                        })
                        # Log each candidate to chat history
                        self._log_image_candidate(candidate_path, actual_index, batch_slug)
                    sent_candidate_count = len(current_candidates)
            
            try:
                print(f"[IMAGE GEN] Starting generation for prompt: {prompt[:50]}... (aspect_ratio={aspect_ratio}, resolution={resolution})")
                # Deterministic: Always generate 4 candidates
                # Prepare batch metadata
                batch_metadata = {}
                if remix_slide is not None:
                    batch_metadata["remix_slide_number"] = remix_slide
                if remix_img_path is not None:
                    batch_metadata["remix_image_path"] = remix_img_path
                
                result = self.nano_client.generate_candidates(
                    prompt, 
                    status_spinner=None, 
                    progress_callback=progress,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    remix_reference_image=remix_ref,
                    batch_metadata=batch_metadata if batch_metadata else None
                )
                candidates = result['candidates']
                batch_slug = result['batch_slug']
                print(f"[IMAGE GEN] Generated {len(candidates)} candidates in batch: {batch_slug}")
                
                # Store candidates with batch info
                self.pending_candidates = candidates
                self.current_batch_slug = batch_slug
                
                # Final notification
                self._notify("images_ready", {"batch_slug": batch_slug})
                print(f"[IMAGE GEN] Notified images_ready")
            except Exception as e:
                print(f"[IMAGE GEN ERROR] {type(e).__name__}: {e}")
                traceback.print_exc()
                self._notify("message", {"role": "system", "content": f"Error generating images: {str(e)}"})
        
        # Run in thread to avoid blocking the agent response
        print(f"[IMAGE GEN] Starting thread for image generation")
        threading.Thread(target=_generate, daemon=True).start()

    def generate_images(self, prompt: str, status_spinner=None) -> List[str]:
        """Generate image candidates (direct call, typically from CLI)."""
        self._notify("generating_images_start", {"prompt": prompt})
        self.last_image_prompt = prompt
        
        def progress(current, total, status, current_candidates, prompt_details=None):
            payload = {
                "current": current, 
                "total": total, 
                "status": status,
                "candidates": current_candidates
            }
            if prompt_details:
                payload["prompt_details"] = prompt_details
            self._notify("image_progress", payload)
        
        try:
            # agent.nano_client.generate_candidates expects a rich spinner potentially.
            # We pass it through if provided (CLI mode).
            result = self.nano_client.generate_candidates(prompt, status_spinner=status_spinner, progress_callback=progress)
            candidates = result['candidates']
            batch_slug = result['batch_slug']
            
            self.pending_candidates = candidates
            self.current_batch_slug = batch_slug
            self._notify("images_ready", {"candidates": candidates, "prompt": prompt, "batch_slug": batch_slug})
            return candidates
        except Exception as e:
            self._notify("error", {"message": str(e)})
            return []

    def select_image(self, index: int, filename: Optional[str] = None) -> Optional[str]:
        """
        Deterministic image selection workflow (step 3-5 of image generation).
        
        When user clicks an image in the UI:
        1. Validate selection
        2. Auto-generate filename if needed
        3. DETERMINISTIC: Save file to images/ folder
        4. DETERMINISTIC: Notify UI of selection
        5. DETERMINISTIC: Tell agent about the selection so it can incorporate the image
        """
        print(f"[SELECT_IMAGE] Called with index={index}, filename={filename}")
        print(f"[SELECT_IMAGE] pending_candidates={self.pending_candidates}")
        
        if not self.pending_candidates or index < 0 or index >= len(self.pending_candidates):
            print(f"[SELECT_IMAGE] Invalid selection - returning None")
            return None
        
        # Step 2: Auto-generate filename if not provided (deterministic naming)
        if not filename:
            # Extract a base name from the last prompt
            base = "".join([c if c.isalnum() else "_" for c in self.last_image_prompt[:20]]).strip("_")
            if not base:
                base = "image"
            # Find next available number
            i = 1
            while True:
                filename = f"{base}_{i}.png"
                test_path = os.path.join(self.nano_client.images_dir, filename)
                if not os.path.exists(test_path):
                    break
                i += 1
            
        try:
            # Step 3: DETERMINISTIC - Always save to images/ folder
            saved_path = self.nano_client.save_selection(self.pending_candidates, index, filename)
            rel_path = f"images/{filename}"
            
            # Step 4: DETERMINISTIC - Always notify UI
            self._notify("image_selected", {"path": saved_path, "filename": filename})
            
            # Log image selection to chat history
            batch_slug = getattr(self, 'current_batch_slug', '')
            self._log_image_selection(index, batch_slug, filename, rel_path)
            
            # Step 5: DETERMINISTIC - Always notify agent with the filename
            # This is a system message, not a user message, telling agent what happened
            import threading
            def _notify_agent():
                try:
                    # Load batch metadata to get remix context
                    batch_metadata = {}
                    if hasattr(self, 'current_batch_slug') and self.current_batch_slug:
                        batch_folder = os.path.join(self.nano_client.drafts_dir, self.current_batch_slug)
                        metadata_path = os.path.join(batch_folder, "metadata.json")
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, "r") as f:
                                    batch_metadata = json.load(f)
                            except Exception as e:
                                print(f"Error reading batch metadata: {e}")
                    
                    # Build system notification with explicit instructions
                    batch_info = f" (batch: {self.current_batch_slug})" if hasattr(self, 'current_batch_slug') and self.current_batch_slug else ""
                    
                    if batch_metadata.get("remix_slide_number"):
                        # Remix slide: replace entire slide contents with image
                        slide_num = batch_metadata["remix_slide_number"]
                        system_notification = f"[SYSTEM] User selected a remixed image from{batch_info}. It has been saved to `{rel_path}`. REPLACE the entire contents of slide {slide_num} with this image by overlaying it. The image should cover the entire slide."
                    elif batch_metadata.get("remix_image_path"):
                        # Remix image: replace the original image
                        original_path = batch_metadata["remix_image_path"]
                        system_notification = f"[SYSTEM] User selected a remixed image from{batch_info}. It has been saved to `{rel_path}`. REPLACE the original image at `{original_path}` with this new remixed image. Update all references to use `{rel_path}` instead of `{original_path}`."
                    else:
                        # Regular image generation: incorporate as usual
                        system_notification = f"[SYSTEM] User selected an image from{batch_info}. It has been saved to `{rel_path}`. Please incorporate this image into the presentation."
                    
                    self._notify("message", {"role": "system", "content": system_notification})
                    self._notify("thinking_start")
                    
                    try:
                        response = self.agent.chat(system_notification, status_spinner=None)
                        self._notify("message", {"role": "model", "content": response})
                    finally:
                        self._notify("thinking_end")
                except Exception as e:
                    print(f"Error notifying agent: {e}")
                    self._notify("error", {"message": f"Error incorporating image: {e}"})
            
            # Run in background so API call returns immediately
            threading.Thread(target=_notify_agent, daemon=True).start()
            
            # Also trigger a preview refresh after a short delay to ensure compilation happens
            def _delayed_refresh():
                import time
                time.sleep(2)  # Give agent time to process and compile
                self._notify("presentation_updated")
            
            threading.Thread(target=_delayed_refresh, daemon=True).start()
            
            self.pending_candidates = [] # Clear candidates after selection
            return saved_path
        except Exception as e:
            self._notify("error", {"message": str(e)})
            raise e

    def get_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools."""
        tools = []
        for tool in self.agent.tools_list:
            name = getattr(tool, '__name__', str(tool))
            doc = getattr(tool, '__doc__', "No description available.")
            if doc:
                doc = doc.strip().split('\n')[0] # Use first line of docstring
            tools.append({"name": name, "description": doc})
        return tools

    def get_history(self):
        """
        Get chat history including rich UI messages.
        
        Loads directly from chat_history.jsonl to include:
        - Regular text messages (role, parts)
        - Rich UI messages (message_type, data)
        """
        if not os.path.exists(self.history_file):
            return []
        
        history = []
        try:
            with open(self.history_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        
                        # Check if this is a rich message with message_type
                        if "message_type" in entry:
                            # Rich message - return as-is for frontend to handle
                            history.append(entry)
                        else:
                            # Regular message - convert parts if needed
                            serializable_entry = {"role": entry.get("role", "user")}
                            
                            # Handle parts field
                            if "parts" in entry:
                                parts = entry["parts"]
                                serializable_parts = []
                                
                                for part in parts:
                                    if isinstance(part, dict):
                                        # Already serializable
                                        serializable_parts.append(part)
                                    elif isinstance(part, str):
                                        # Plain string
                                        serializable_parts.append({"text": part})
                                
                                serializable_entry["parts"] = serializable_parts
                            
                            # Handle old-style content field
                            if "content" in entry:
                                serializable_entry["content"] = entry["content"]
                            
                            history.append(serializable_entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error loading history: {e}")
        
        return history

    def get_layouts(self):
        """Get available layouts for the current presentation with metadata."""
        import re
        
        layouts_path = os.path.join(self.agent.presentation_dir, "layouts.md")
        
        if not os.path.exists(layouts_path):
            return []
        
        try:
            with open(layouts_path, "r") as f:
                content = f.read()
            
            # Split by --- to get individual slides
            slides = content.split('\n---\n')
            
            layouts = []
            for i, slide in enumerate(slides):
                # Look for layout name in HTML comment
                match = re.search(r'<!-- layout: ([\w-]+) -->', slide)
                if match:
                    layout_name = match.group(1)
                    # Skip front matter slide
                    if slide.strip().startswith('---'):
                        continue
                    
                    # Parse metadata from HTML comments
                    image_friendly = re.search(r'<!-- image-friendly: (true|false) -->', slide)
                    aspect_ratio = re.search(r'<!-- recommended-aspect-ratio: ([\d:]+) -->', slide)
                    image_position = re.search(r'<!-- image-position: ([\w-]+) -->', slide)
                    description = re.search(r'<!-- description: (.+?) -->', slide)
                    
                    layouts.append({
                        "name": layout_name,
                        "content": slide.strip(),
                        "index": i,
                        "image_friendly": image_friendly.group(1) == "true" if image_friendly else False,
                        "recommended_aspect_ratio": aspect_ratio.group(1) if aspect_ratio else None,
                        "image_position": image_position.group(1) if image_position else None,
                        "description": description.group(1) if description else None
                    })
            
            return layouts
        except Exception as e:
            print(f"Error reading layouts: {e}")
            return []
    
    def _handle_layout_request(self, title=None, position="end"):
        """
        Called when agent's create_slide_with_layout tool is invoked.
        Shows layout selection UI to the user.
        """
        # Store the request details
        self.pending_layout_request = {
            "title": title,
            "position": position
        }
        
        # Get available layouts
        layouts = self.get_layouts()
        
        # Notify frontend to show layout selection UI
        self._notify("layout_request", {
            "layouts": layouts,
            "title": title,
            "position": position
        })
    
    def select_layout(self, layout_name: str):
        """
        Handle layout selection from UI after create_slide_with_layout was called.
        Creates the new slide with the selected layout.
        """
        if not self.pending_layout_request:
            return {"error": "No pending layout request"}
        
        try:
            request = self.pending_layout_request
            title = request.get("title")
            position = request.get("position", "end")
            
            # Get the layout content
            layouts = self.get_layouts()
            selected_layout = next((l for l in layouts if l["name"] == layout_name), None)
            
            if not selected_layout:
                return {"error": f"Layout '{layout_name}' not found"}
            
            # Read current deck
            deck_path = os.path.join(self.agent.presentation_dir, "deck.marp.md")
            with open(deck_path, "r") as f:
                deck_content = f.read()
            
            # Prepare new slide content
            new_slide = "\n---\n\n" + selected_layout["content"]
            
            # Replace placeholder title if provided
            if title:
                # Try to replace the first heading in the layout
                import re
                new_slide = re.sub(r'^# .+$', f'# {title}', new_slide, count=1, flags=re.MULTILINE)
            
            # Insert slide based on position
            if position == "beginning":
                # Insert after front matter
                parts = deck_content.split('\n---\n', 2)
                if len(parts) >= 2:
                    deck_content = parts[0] + '\n---\n' + new_slide + '\n---\n' + '\n---\n'.join(parts[1:])
            elif position == "after-current":
                # For now, just append to end (would need slide tracking for true "after-current")
                deck_content += new_slide
            else:  # "end" (default)
                deck_content += new_slide
            
            # Write updated deck
            with open(deck_path, "w") as f:
                f.write(deck_content)
            
            # Clear pending request
            self.pending_layout_request = None
            
            # Notify the agent about the completion
            import threading
            def _notify_agent():
                try:
                    system_notification = f"[SYSTEM] New slide created using '{layout_name}' layout{' with title: ' + title if title else ''}. The slide has been added to the presentation."
                    
                    self._notify("message", {"role": "system", "content": system_notification})
                    self._notify("thinking_start")
                    
                    try:
                        response = self.agent.chat(system_notification, status_spinner=None)
                        self._notify("message", {"role": "model", "content": response})
                    finally:
                        self._notify("thinking_end")
                        # Trigger preview update
                        self._notify("presentation_updated")
                except Exception as e:
                    print(f"Error notifying agent about layout creation: {e}")
                    self._notify("error", {"message": f"Error finalizing layout: {e}"})
            
            # Run in background so API call returns immediately
            threading.Thread(target=_notify_agent, daemon=True).start()
            
            return {"status": "success", "layout": layout_name, "title": title}
        except Exception as e:
            self._notify("error", {"message": str(e)})
            raise e
    
    def get_state(self):
        """Get current session state."""
        return {
            "presentation": self.context,
            "pending_candidates": self.pending_candidates,
            "last_prompt": self.last_image_prompt
        }


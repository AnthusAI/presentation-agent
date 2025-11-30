import os
import json
import threading
from typing import Optional, List, Dict, Callable, Any
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

        # Hook presentation updates
        if hasattr(self.agent, 'tools_handler'):
            self.agent.tools_handler.on_presentation_updated = lambda: self._notify("presentation_updated")
            # Hook image generation requests from the agent
            self.agent.tools_handler.on_image_generation = self._handle_agent_image_request
            # Hook tool events
            self.agent.tools_handler.on_tool_call = self._handle_tool_event

    def subscribe(self, callback: Callable[[str, Any], None]):
        """Subscribe to events. Callback receives (event_type, data)."""
        with self._lock:
            self.listeners.append(callback)

    def _handle_tool_event(self, event_type: str, data: Any):
        """Forward tool events to listeners."""
        self._notify(event_type, data)

    def _notify(self, event_type: str, data: Any = None):
        with self._lock:
            for listener in self.listeners:
                try:
                    listener(event_type, data)
                except Exception as e:
                    print(f"Error in listener: {e}")

    def send_message(self, user_input: str, status_spinner=None) -> str:
        """Send a message to the agent and get the response."""
        self._notify("thinking_start")
        try:
            response = self.agent.chat(user_input, status_spinner=status_spinner)
            self._notify("message", {"role": "model", "content": response})
            return response
        finally:
            self._notify("thinking_end")

    def _handle_agent_image_request(self, prompt: str):
        """
        Called when agent's generate_image tool is invoked (web mode).
        
        This is the deterministic system workflow:
        1. Generate 4 candidates (with progress updates)
        2. Display in UI sidebar
        3. Wait for user selection (handled by select_image method)
        4. Save selected image (handled by select_image method)
        5. Notify agent with filename (handled by select_image method)
        """
        # Send the prompt as a regular message first so user knows what's happening
        self._notify("message", {"role": "model", "content": f"I'll generate images with this prompt: **{prompt}**"})
        
        # Generate images in the background and notify via SSE
        import threading
        def _generate():
            self.last_image_prompt = prompt
            
            def progress(current, total, status, current_candidates):
                # Update progress AND show candidates as they're generated
                self._notify("image_progress", {
                    "current": current, 
                    "total": total, 
                    "status": status,
                    "candidates": current_candidates  # Show images incrementally
                })
            
            try:
                # Deterministic: Always generate 4 candidates
                candidates = self.nano_client.generate_candidates(prompt, status_spinner=None, progress_callback=progress)
                self.pending_candidates = candidates
                # Final notification with all candidates
                self._notify("images_ready", {"candidates": candidates, "prompt": prompt})
            except Exception as e:
                self._notify("error", {"message": str(e)})
        
        # Run in thread to avoid blocking the agent response
        threading.Thread(target=_generate, daemon=True).start()

    def generate_images(self, prompt: str, status_spinner=None) -> List[str]:
        """Generate image candidates (direct call, typically from CLI)."""
        self._notify("generating_images_start", {"prompt": prompt})
        self.last_image_prompt = prompt
        
        def progress(current, total, status, current_candidates):
            self._notify("image_progress", {
                "current": current, 
                "total": total, 
                "status": status,
                "candidates": current_candidates
            })
        
        try:
            # agent.nano_client.generate_candidates expects a rich spinner potentially.
            # We pass it through if provided (CLI mode).
            candidates = self.nano_client.generate_candidates(prompt, status_spinner=status_spinner, progress_callback=progress)
            
            self.pending_candidates = candidates
            self._notify("images_ready", {"candidates": candidates, "prompt": prompt})
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
        if not self.pending_candidates or index < 0 or index >= len(self.pending_candidates):
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
            
            # Step 5: DETERMINISTIC - Always notify agent with the filename
            # This is a system message, not a user message, telling agent what happened
            import threading
            def _notify_agent():
                try:
                    # This is the key: we're telling the agent what the system did
                    system_notification = f"[SYSTEM] User selected an image. It has been saved to `{rel_path}`. Please incorporate this image into the presentation."
                    
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

    def get_history(self):
        """Get chat history."""
        # Agent.load_history returns list of {role, parts=[text]}
        return self.agent.load_history()

    def get_state(self):
        """Get current session state."""
        return {
            "presentation": self.context,
            "pending_candidates": self.pending_candidates,
            "last_prompt": self.last_image_prompt
        }


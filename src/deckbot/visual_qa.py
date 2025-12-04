import os
import subprocess
import time
import logging
from typing import Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class VisualQA:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Use a model capable of vision. Flash is fast and good for this.
        self.model_name = "gemini-2.0-flash-exp" 
        self.client = None
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client: {e}")
        else:
            logger.warning("VisualQA initialized without API key")

    # Rate limiting: 10 requests per minute = 1 request every 6 seconds.
    # We'll use a class-level timestamp to track the last call.
    _last_call_time = 0

    def check_slide(self, presentation_dir: str, slide_number: int, history: list = None) -> tuple[bool, str]:
        """
        Checks a specific slide for visual issues using Gemini.
        Returns (has_issues, report_string).
        """
        start_time = time.time()
        
        # TEST MOCKING
        mock_response = os.getenv("MOCK_VISUAL_QA")
        if mock_response:
            if mock_response == "No issues found.":
                return False, f"[Visual QA] Checked slide {slide_number}. Saw: \"Mock slide description\". No issues found. (MOCK)"
            return True, f"[Visual QA Report]\n{mock_response} (MOCK)"

        if not self.client:
            return False, "[Visual QA] Skipped (No API Key)"

        # 1. Ensure previews exist
        image_path, was_generated = self._ensure_preview(presentation_dir, slide_number)
        
        if not image_path:
            logger.warning(f"Could not generate preview image for Visual QA (slide {slide_number}).")
            return False, "[Visual QA] Skipped (Preview generation failed)"

        # 2. Load image
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            logger.error(f"Could not read preview image: {e}")
            return False, f"[Visual QA] Error reading image: {e}"

        # 3. Prepare History
        history_text = ""
        if history:
            recent_history = history[-5:]
            history_text = "\nRECENT CONVERSATION HISTORY:\n"
            for msg in recent_history:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                if isinstance(content, list):
                    content = " ".join([str(p) for p in content])
                history_text += f"{role.upper()}: {content[:200]}...\n"

        # 4. Call Gemini with Rate Limiting
        
        # Enforce minimum 6s delay between calls
        time_since_last = time.time() - VisualQA._last_call_time
        if time_since_last < 6.5:
            sleep_time = 6.5 - time_since_last
            print(f"[Visual QA] Rate limiting: Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)

        try:
            gemini_start = time.time()
            prompt = f"""
You are a Visual QA agent for a presentation deck. 
The user is working on this presentation. 
{history_text}

Look at this screenshot of slide {slide_number}.
First, provide a one-sentence description of what you see.

Then, perform a PIXEL-PEEPING inspection of the BOTTOM EDGE of the slide.
- Does any text line appear cut in half horizontally?
- Does any image content appear abruptly truncated?
- Is the slide footer fully visible and intact?
- If ANY element looks like it continues past the bottom edge, REPORT IT as an overflow issue.

Also check for:
- Placeholder text/images.
- Raw code artifacts.
- Overlaps.

Format your response as:
DESCRIPTION: <description>
VERDICT: <"No issues found" or "ISSUES FOUND">
<List issues if any>
"""
            # Simple retry for 429
            max_retries = 3
            retry_delay = 10
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part(text=prompt),
                                    types.Part(inline_data=types.Blob(
                                        mime_type="image/png",
                                        data=image_bytes
                                    ))
                                ]
                            )
                        ],
                        config=types.GenerateContentConfig(
                            temperature=0.0
                        )
                    )
                    VisualQA._last_call_time = time.time()
                    break # Success
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if attempt < max_retries - 1:
                            print(f"[Visual QA] Hit rate limit (429). Retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2 # Exponential backoff
                            continue
                    raise e # Re-raise if not 429 or retries exhausted

            result = response.text.strip()
            duration = time.time() - gemini_start
            
            # Parse result
            description = "Unknown slide"
            if "DESCRIPTION:" in result:
                parts = result.split("DESCRIPTION:", 1)[1].split("VERDICT:", 1)
                description = parts[0].strip()
                if len(parts) > 1:
                    verdict_part = parts[1].strip()
                else:
                    verdict_part = result
            else:
                verdict_part = result

            if "No issues found" in verdict_part:
                return False, f"[Visual QA] Checked slide {slide_number}. Saw: \"{description}\". No issues found. (Took {duration:.1f}s)"
            
            return True, f"[Visual QA Report] (Took {duration:.1f}s)\n{result}"
            
        except Exception as e:
            logger.error(f"Error running Visual QA: {e}")
            return False, f"Error running Visual QA: {e}"

    def _ensure_preview(self, presentation_dir: str, slide_number: int, force: bool = False) -> tuple[Optional[str], bool]:
        """
        Ensures the preview image for the given slide exists and is up to date.
        Returns (path_to_image, was_generated).
        """
        preview_dir = os.path.join(presentation_dir, ".previews")
        os.makedirs(preview_dir, exist_ok=True)
        
        filename = f"slide.{slide_number:03d}.png"
        filepath = os.path.join(preview_dir, filename)
        
        md_path = os.path.join(presentation_dir, "deck.marp.md")
        
        needs_gen = False
        if force or not os.path.exists(filepath):
            needs_gen = True
        elif os.path.exists(md_path):
            if os.path.getmtime(md_path) > os.path.getmtime(filepath):
                needs_gen = True
        
        if needs_gen:
            print(f"[DEBUG] Generating previews for {presentation_dir}...")
            try:
                # Generate only the specific slide if possible to save time?
                # Marp CLI doesn't easily support single slide render without splitting file.
                # But we can render all.
                # Optimization: If deck is large, this is slow.
                # But for now, correctness > speed.
                subprocess.run(
                    [
                        'npx', '@marp-team/marp-cli',
                        'deck.marp.md',
                        '--images', 'png',
                        '--output', os.path.join('.previews', 'slide.png'),
                        '--allow-local-files'
                    ],
                    cwd=presentation_dir,
                    check=True,
                    capture_output=True,
                    timeout=30
                )
                if os.path.exists(filepath):
                    return filepath, True
            except subprocess.CalledProcessError as e:
                logger.error(f"Marp generation failed: {e.stderr.decode()}")
                return None, False
            except Exception as e:
                logger.error(f"VisualQA generation error: {e}")
                return None, False
                
        if os.path.exists(filepath):
            return filepath, False
        return None, False

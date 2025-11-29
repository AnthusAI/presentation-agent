import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self, presentation_context):
        self.context = presentation_context
        self.api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.chat_session = self.model.start_chat(history=[])
            
            # Inject system prompt
            system_prompt = self._build_system_prompt()
            # Gemini Pro doesn't have a separate system prompt arg in start_chat yet in all versions,
            # but we can send it as the first message or use instructions if available.
            # For this demo, sending as first message is a common pattern if system_instruction isn't supported.
            # However, newer SDKs support system_instruction. Let's try to use it or fallback.
            try:
                 self.model = genai.GenerativeModel('gemini-1.5-pro-latest', system_instruction=system_prompt)
                 self.chat_session = self.model.start_chat(history=[])
            except:
                 # Fallback for older models/sdk
                 self.model = genai.GenerativeModel('gemini-pro')
                 self.chat_session = self.model.start_chat(history=[
                     {"role": "user", "parts": [system_prompt]},
                     {"role": "model", "parts": ["Understood. I am ready to assist you with your presentation."]}
                 ])
        else:
            self.model = None
            self.chat_session = None

    def _build_system_prompt(self):
        return f"""
You are an AI presentation assistant helping to build a Marp deck.
Current Presentation: {self.context['name']}
Description: {self.context.get('description', '')}

You can help by outlining slides, writing content, and suggesting visuals.
The user wants to use 'vibe coding', so keep it casual but professional.
"""

    def chat(self, message):
        if not self.chat_session:
            return "Error: GOOGLE_AI_STUDIO_API_KEY or GOOGLE_API_KEY not found. Please set it in your environment."
        
        response = self.chat_session.send_message(message)
        return response.text


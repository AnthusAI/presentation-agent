from features.steps.cli_steps import temporary_environment
from behave import use_fixture
from unittest.mock import patch, MagicMock
import os

def before_scenario(context, scenario):
    use_fixture(temporary_environment, context)
    
    # Clean up any preferences files from previous tests
    from pathlib import Path
    # PreferencesManager uses .deckbot.yaml in project root
    prefs_file = Path('.deckbot.yaml')
    if prefs_file.exists():
        prefs_file.unlink()
    
    # Reset ALL webapp-related state BEFORE each scenario
    import sys
    # Clear any cached presentation managers
    if 'deckbot.webapp' in sys.modules:
        try:
            from deckbot import webapp
            webapp.current_service = None
        except:
            pass
    
    # Mock OLD Google Generative AI SDK to avoid real API calls during tests
    # This prevents "Could not initialize any Gemini model" errors
    context.genai_configure_patch = patch('google.generativeai.configure')
    context.genai_model_patch = patch('google.generativeai.GenerativeModel')
    
    context.mock_configure = context.genai_configure_patch.start()
    context.mock_model_cls = context.genai_model_patch.start()
    
    # Set up default mock behavior for old SDK
    mock_instance = MagicMock()
    mock_chat_session = MagicMock()
    mock_chat_session.send_message.return_value.text = "Mock AI response"
    mock_chat_session.history = []
    mock_instance.start_chat.return_value = mock_chat_session
    context.mock_model_cls.return_value = mock_instance
    
    # Mock NEW Google Generative AI SDK (google.genai) to avoid real API calls
    context.new_genai_client_patch = patch('google.genai.Client')
    context.mock_new_client_cls = context.new_genai_client_patch.start()
    
    # Set up mock behavior for new SDK (used by NanoBananaClient)
    mock_new_client = MagicMock()
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake_image_data"
    mock_response.parts = [mock_part]
    mock_new_client.models.generate_content.return_value = mock_response
    context.mock_new_client_cls.return_value = mock_new_client
    
    # Ensure GOOGLE_API_KEY is set for tests (from .env or set a fake one)
    if not os.getenv('GOOGLE_API_KEY'):
        os.environ['GOOGLE_API_KEY'] = 'test_api_key_for_testing'

def after_scenario(context, scenario):
    # Clean up patches
    if hasattr(context, 'genai_configure_patch'):
        context.genai_configure_patch.stop()
    if hasattr(context, 'genai_model_patch'):
        context.genai_model_patch.stop()
    if hasattr(context, 'new_genai_client_patch'):
        context.new_genai_client_patch.stop()
    
    # Clean up any preferences files created during tests
    from pathlib import Path
    prefs_file = Path('.deckbot.yaml')
    if prefs_file.exists():
        prefs_file.unlink()
    
    # Reset webapp global state
    try:
        from deckbot import webapp
        webapp.current_service = None
    except:
        pass


from features.steps.cli_steps import temporary_environment
from behave import use_fixture
from unittest.mock import patch, MagicMock, PropertyMock
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
    
    # Skip mocking for integration tests (tagged with @integration)
    if 'integration' in scenario.tags:
        return
    
    # Mock Google Generative AI SDK (google.genai) to avoid real API calls
    context.new_genai_client_patch = patch('google.genai.Client')
    context.mock_new_client_cls = context.new_genai_client_patch.start()
    
    # Set up mock behavior for new SDK (used by NanoBananaClient)
    mock_new_client = MagicMock()
    mock_response = MagicMock()
    
    # Create mock part with inline data
    mock_part = MagicMock()
    # Minimal valid 1x1 PNG signature
    valid_png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # Mock the inline_data.data attribute for base64 decoding check
    mock_part.inline_data.data = valid_png_bytes
    # Also ensure inline_data itself is truthy
    type(mock_part).inline_data = PropertyMock(return_value=MagicMock(data=valid_png_bytes))

    # Create mock candidate with content
    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]
    
    # Set candidates on response
    mock_response.candidates = [mock_candidate]
    # Also keep parts for backward compatibility tests if any
    mock_response.parts = [mock_part]
    
    mock_new_client.models.generate_content.return_value = mock_response
    context.mock_new_client_cls.return_value = mock_new_client
    
    # Ensure GOOGLE_API_KEY is set for tests (from .env or set a fake one)
    if not os.getenv('GOOGLE_API_KEY'):
        os.environ['GOOGLE_API_KEY'] = 'test_api_key_for_testing'

def after_scenario(context, scenario):
    # Clean up patches
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


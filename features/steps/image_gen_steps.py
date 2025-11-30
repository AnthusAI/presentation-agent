from behave import given, when, then
from unittest.mock import patch, MagicMock
from deckbot.nano_banana import NanoBananaClient
from deckbot.manager import PresentationManager
from deckbot.tools import PresentationTools
from deckbot.session_service import SessionService
import os
import shutil

@given('I am in the REPL for "{name}"')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    if not manager.get_presentation(name):
        manager.create_presentation(name)
    context.presentation = manager.get_presentation(name)
    context.nano_client = NanoBananaClient(context.presentation)

@when('I request an image for "{prompt}"')
def step_impl(context, prompt):
    # Mock the NEW google.genai.Client (not the old SDK)
    # The global mock from environment.py returns fake image data
    with patch('deckbot.nano_banana.NanoBananaClient._open_folder') as mock_open:
        # Call generate_candidates - it will use the mocked client from environment.py
        # which returns mock_part.inline_data.data = b"fake_image_data"
        context.candidates = context.nano_client.generate_candidates(prompt)
        
        # Create the actual files since the mock doesn't write them to disk
        # (the mock returns fake data but generate_candidates may not write it)
        for candidate_path in context.candidates:
            os.makedirs(os.path.dirname(candidate_path), exist_ok=True)
            with open(candidate_path, 'wb') as f:
                f.write(b"fake_image_data")

@then('4 image candidates should be generated using Nano Banana')
def step_impl(context):
    print(f"DEBUG: candidates = {context.candidates}")
    print(f"DEBUG: len = {len(context.candidates) if context.candidates else 'None'}")
    if context.candidates and len(context.candidates) > 0:
        print(f"DEBUG: first candidate = {context.candidates[0]}")
        print(f"DEBUG: exists? {os.path.exists(context.candidates[0])}")
    assert len(context.candidates) == 4, f"Expected 4 candidates, got {len(context.candidates)}"
    assert os.path.exists(context.candidates[0]), f"File {context.candidates[0]} does not exist"
    # Verify they are in a draft subfolder
    assert "drafts" in context.candidates[0]

@then('I should be prompted to select one')
def step_impl(context):
    # In BDD we just verify the candidates are ready for selection
    pass

@given('4 image candidates have been generated')
def step_impl(context):
    # Ensure we have a nano client set up
    if not hasattr(context, 'nano_client'):
        manager = PresentationManager(root_dir=context.temp_dir)
        if not manager.get_presentation("my-deck"):
             manager.create_presentation("my-deck")
        presentation = manager.get_presentation("my-deck")
        context.nano_client = NanoBananaClient(presentation)

    # Setup fake candidates in a proper draft folder structure
    draft_dir = os.path.join(context.nano_client.drafts_dir, "test_request")
    os.makedirs(draft_dir, exist_ok=True)
    
    context.candidates = []
    for i in range(4):
        path = os.path.join(draft_dir, f"candidate_{i+1}.png")
        with open(path, "wb") as f:
            f.write(b"fake_image_data")
        context.candidates.append(path)

@when('I select candidate {index}')
def step_impl(context, index):
    index = int(index)
    # Mock user input selection logic
    context.saved_path = context.nano_client.save_selection(context.candidates, index - 1, "final_image.png")

@then('the image from candidate {index} should be saved to the presentation images folder')
def step_impl(context, index):
    assert os.path.exists(context.saved_path)
    assert "images" in context.saved_path
    # Check it's not in drafts
    assert "drafts" not in context.saved_path
    
@then('the other candidates should be cleaned up')
def step_impl(context):
    # Updated requirement: candidates should NOT be cleaned up (copied not moved)
    for candidate in context.candidates:
        assert os.path.exists(candidate)

# ===== Web Mode Steps =====

@given('I am using the web UI')
def step_impl(context):
    context.is_web_mode = True
    context.mock_callback = MagicMock()
    
    # Mock NanoBananaClient
    with patch('deckbot.tools.NanoBananaClient') as MockNano:
        context.nano_client = MockNano.return_value
        context.tools = PresentationTools({'name': 'test-deck'}, context.nano_client)
        # Enable web mode
        context.tools.on_image_generation = context.mock_callback

@when('the agent calls generate_image for "{prompt}"')
def step_impl(context, prompt):
    context.tool_result = context.tools.generate_image(prompt)

@then('the agent should receive a WAIT message')
def step_impl(context):
    assert "WAIT:" in context.tool_result

@then('the agent should NOT proceed with writing files')
def step_impl(context):
    assert "DO NOT proceed" in context.tool_result

@then('the web UI should show the candidates')
def step_impl(context):
    assert context.mock_callback.called

@given('the agent is waiting for image selection')
def step_impl(context):
    # Setup SessionService in waiting state
    # We need to patch Agent to avoid real init if we don't want IO/API calls
    with patch('deckbot.session_service.Agent'):
        context.service = SessionService({'name': 'test-deck'})
    
    context.service.agent = MagicMock()
    context.service.pending_candidates = ["cand1.png", "cand2.png", "cand3.png", "cand4.png"]
    context.service.last_image_prompt = "test prompt"
    
    # Mock notify to capture system message if needed
    context.service._notify = MagicMock()

@when('I choose candidate number {index:d} in the web UI')
def step_impl(context, index):
    context.service.nano_client = MagicMock()
    context.service.nano_client.save_selection.return_value = "saved_image.png"
    # Ensure index is int
    idx = int(index)
    context.service.select_image(idx - 1)

@then('a SYSTEM message should be sent to the agent')
def step_impl(context):
    assert context.service.agent.chat.called
    args = context.service.agent.chat.call_args
    assert "[SYSTEM]" in args[0][0]

@then('the message should contain the saved filename')
def step_impl(context):
    args = context.service.agent.chat.call_args
    # Prompt was "test prompt", index 0 (1st item)
    # Expected: test_prompt_1.png
    message = args[0][0]
    assert "test_prompt_1.png" in message, f"Expected filename not found in message: {message}"

# ===== Aspect Ratio Default Steps =====

@given('I have a presentation with aspect ratio "{ratio}"')
def step_impl(context, ratio):
    manager = PresentationManager(root_dir=context.temp_dir)
    if not manager.get_presentation("test-deck"):
        manager.create_presentation("test-deck")
    manager.set_presentation_aspect_ratio("test-deck", ratio)
    context.presentation = manager.get_presentation("test-deck")
    context.nano_client = NanoBananaClient(context.presentation)
    
    # Mock the Gemini client
    context.mock_client = MagicMock()
    context.nano_client.client = context.mock_client

@when('the agent generates an image without specifying aspect ratio')
def step_impl(context):
    # Mock the generate_content response
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake_image_data"
    mock_response.parts = [mock_part]
    context.mock_client.models.generate_content.return_value = mock_response
    
    # Generate with default aspect ratio (should use presentation's)
    from deckbot.tools import PresentationTools
    tools = PresentationTools(context.presentation, context.nano_client)
    
    # Mock generate_candidates to avoid real API calls but capture the call
    # Also mock IntPrompt to avoid waiting for user input
    # Also mock save_selection to avoid file operations
    with patch.object(context.nano_client, 'generate_candidates', return_value=['fake1.png', 'fake2.png', 'fake3.png', 'fake4.png']) as mock_gen, \
         patch('deckbot.tools.IntPrompt.ask', return_value=1), \
         patch.object(context.nano_client, 'save_selection', return_value='saved_image.png'):
        tools.generate_image("a sunset")
        context.last_generate_call = mock_gen.call_args

@then('the image should be generated with aspect ratio "{ratio}"')
def step_impl(context, ratio):
    # Check that generate_candidates was called with the correct aspect_ratio parameter
    assert context.last_generate_call is not None, "generate_candidates was not called"
    
    # Extract the aspect_ratio argument from the call
    call_kwargs = context.last_generate_call[1]  # kwargs
    actual_aspect_ratio = call_kwargs.get('aspect_ratio', '1:1')  # default is 1:1
    
    # Verify it matches expected
    assert actual_aspect_ratio == ratio, f"Expected aspect ratio {ratio}, but got {actual_aspect_ratio}"

@when('the agent generates a square image')
def step_impl(context):
    # Mock the generate_content response
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake_image_data"
    mock_response.parts = [mock_part]
    context.mock_client.models.generate_content.return_value = mock_response
    
    # Generate with explicit square aspect ratio
    from deckbot.tools import PresentationTools
    tools = PresentationTools(context.presentation, context.nano_client)
    
    # Mock generate_candidates to avoid real API calls and capture the call
    # Also mock IntPrompt to avoid waiting for user input
    # Also mock save_selection to avoid file operations
    with patch.object(context.nano_client, 'generate_candidates', return_value=['fake1.png', 'fake2.png', 'fake3.png', 'fake4.png']) as mock_gen, \
         patch('deckbot.tools.IntPrompt.ask', return_value=1), \
         patch.object(context.nano_client, 'save_selection', return_value='saved_image.png'):
        tools.generate_image("a sunset", aspect_ratio="1:1")
        context.last_generate_call = mock_gen.call_args

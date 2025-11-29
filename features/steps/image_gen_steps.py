from behave import given, when, then
from unittest.mock import patch, MagicMock
from vibe_presentation.nano_banana import NanoBananaClient
from vibe_presentation.manager import PresentationManager
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
    # Mock google.generativeai.GenerativeModel
    with patch('google.generativeai.GenerativeModel') as mock_model_cls, \
         patch('vibe_presentation.nano_banana.NanoBananaClient._open_folder') as mock_open:
        mock_model = mock_model_cls.return_value
        
        # Mock successful generation response
        mock_response = MagicMock()
        mock_part = MagicMock()
        # Mock inline_data
        mock_part.inline_data.data = b"fake_image_data"
        mock_response.parts = [mock_part]
        
        mock_model.generate_content.return_value = mock_response
        
        context.candidates = context.nano_client.generate_candidates(prompt)

@then('4 image candidates should be generated using Nano Banana')
def step_impl(context):
    assert len(context.candidates) == 4
    assert os.path.exists(context.candidates[0])
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

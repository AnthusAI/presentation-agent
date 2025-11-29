from behave import given, when, then
from unittest.mock import MagicMock, patch
from vibe_presentation.manager import PresentationManager
from vibe_presentation.nano_banana import NanoBananaClient
import os
import json

@given('a presentation "{name}" exists')
def step_impl(context, name):
    # Use manager to create
    # Ensure temp_dir is set (requires cli_steps fixture or similar)
    # If running via features/branded_image_gen.feature, we need the fixture.
    # Assuming environment.py handles fixture for all features.
    manager = PresentationManager(root_dir=context.temp_dir)
    try:
        manager.create_presentation(name)
    except: pass # Ignore if exists

@given('the presentation "{name}" has image style "{style}"')
def step_impl(context, name, style):
    path = os.path.join(context.temp_dir, name, "metadata.json")
    with open(path, 'r') as f:
        data = json.load(f)
    
    data['image_style'] = {"prompt": style}
    
    with open(path, 'w') as f:
        json.dump(data, f)

@given('the presentation "{name}" has a reference image "{image_name}"')
def step_impl(context, name, image_name):
    path = os.path.join(context.temp_dir, name, "metadata.json")
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Create dummy image file
    img_path = os.path.join(context.temp_dir, name, image_name)
    with open(img_path, 'wb') as f:
        f.write(b"fake image content")
        
    data['image_style'] = {"reference_images": [image_name]}
    
    with open(path, 'w') as f:
        json.dump(data, f)

@when('I request an image "{prompt}" for "{deck_name}"')
def step_impl(context, prompt, deck_name):
    # Load context
    manager = PresentationManager(root_dir=context.temp_dir)
    pres_context = manager.get_presentation(deck_name)
    
    # We need to patch PIL.Image.open because our fake image is invalid
    # Also patch _open_folder to prevent opening files in Finder
    with patch('PIL.Image.open') as mock_open, \
         patch('vibe_presentation.nano_banana.NanoBananaClient._open_folder'):
        mock_image = MagicMock()
        mock_open.return_value = mock_image
        
        client = NanoBananaClient(pres_context)
        
        # Mock the generation model
        with patch('google.generativeai.GenerativeModel') as MockModel:
            mock_instance = MockModel.return_value
            mock_instance.generate_content.return_value = MagicMock() # Dummy response
            
            client.generate_candidates(prompt)
            
            context.mock_generate = mock_instance.generate_content

@then('the image generation prompt should contain "{text}"')
def step_impl(context, text):
    args, _ = context.mock_generate.call_args
    # args[0] could be a string or a list of contents
    content = args[0]
    if isinstance(content, list):
        # Find string part
        text_content = " ".join([str(c) for c in content if isinstance(c, str)])
        assert text in text_content, f"'{text}' not found in prompt list: {content}"
    else:
        assert text in content, f"'{text}' not found in prompt: {content}"

@then('the image generation request should include the reference image "{image_name}"')
def step_impl(context, image_name):
    args, _ = context.mock_generate.call_args
    content = args[0]
    
    assert isinstance(content, list), "Expected content list for multimodal input"
    
    found_image = False
    for item in content:
        # We mocked PIL image, so look for that mock
        if hasattr(item, 'resize') or isinstance(item, MagicMock): 
            # PIL images have resize, or it's our MagicMock
            found_image = True
            
    assert found_image, "No image object found in generation request"


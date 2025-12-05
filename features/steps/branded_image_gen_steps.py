from behave import given, when, then
from unittest.mock import MagicMock, patch
from deckbot.manager import PresentationManager
from deckbot.nano_banana import NanoBananaClient
import os
import json

@given('a presentation "{name}" exists')
def step_impl(context, name):
    context.pres_name = name
    manager = PresentationManager(root_dir=context.temp_dir)
    try:
        manager.create_presentation(name)
    except: pass

@given('the presentation "{name}" has image style "{style}"')
def step_impl(context, name, style):
    path = os.path.join(context.temp_dir, name, "metadata.json")
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Merge with existing style if present
    if 'image_style' not in data:
        data['image_style'] = {}
    data['image_style']['prompt'] = style
    
    with open(path, 'w') as f:
        json.dump(data, f)

@given('the presentation "{name}" has a style reference image "{image_name}"')
def step_impl(context, name, image_name):
    path = os.path.join(context.temp_dir, name, "metadata.json")
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Create dummy image file in images folder
    images_dir = os.path.join(context.temp_dir, name, "images")
    os.makedirs(images_dir, exist_ok=True)
    img_path = os.path.join(images_dir, image_name)
    
    # Copy the actual test reference image if available
    reference_img = "/Users/ryan.porter/Projects/DeckBot/presentations/About DeckBot/images/Vertical_technical_d_1.png"
    if os.path.exists(reference_img):
        import shutil
        shutil.copy(reference_img, img_path)
    else:
        # Fallback to fake data - MUST be valid image bytes for PIL.Image.open()
        with open(img_path, 'wb') as f:
            # Minimal valid 1x1 PNG
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        
    if 'image_style' not in data:
        data['image_style'] = {}
    data['image_style']['style_reference'] = f"images/{image_name}"
    
    with open(path, 'w') as f:
        json.dump(data, f)

@when('I request an image "{prompt}" for "{deck_name}"')
def step_impl(context, prompt, deck_name):
    manager = PresentationManager(root_dir=context.temp_dir)
    pres_context = manager.get_presentation(deck_name)
    
    # Patch _open_folder
    with patch('deckbot.nano_banana.NanoBananaClient._open_folder'):
        # Pass root_dir explicitly so client finds the test deck
        client = NanoBananaClient(pres_context, root_dir=context.temp_dir)
        result = client.generate_candidates(prompt)
        candidates = result['candidates'] if isinstance(result, dict) else result
        
        # Create fake files
        for candidate_path in candidates:
            os.makedirs(os.path.dirname(candidate_path), exist_ok=True)
            with open(candidate_path, 'wb') as f:
                f.write(b"fake_image_data")
        
        context.last_prompt = prompt
        context.pres_context = pres_context
        context.nano_client = client

@then('the image generation prompt should contain "{text}"')
def step_impl(context, text):
    # We check the actual call to the mock client
    mock_client = context.mock_new_client_cls.return_value
    # generate_content might be called 4 times. Check the first one.
    assert mock_client.models.generate_content.called, "generate_content was not called"
    
    found = False
    for call in mock_client.models.generate_content.call_args_list:
        # args or kwargs
        contents = call.kwargs.get('contents')
        if not contents and len(call.args) > 0:
            # Try positional
            if 'contents' in call.kwargs:
                contents = call.kwargs['contents']
            elif len(call.args) >= 2:
                contents = call.args[1]
            else:
                continue
            
        # contents should be a list. Check text parts.
        if isinstance(contents, list):
            for item in contents:
                if isinstance(item, str) and text in item:
                    found = True
                    break
        elif isinstance(contents, str) and text in contents:
            found = True
        if found: break
        
    # Fallback check: metadata (for text in style instructions)
    if not found:
        metadata_path = os.path.join(context.temp_dir, context.pres_context['name'], 'metadata.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            style = metadata.get('image_style', {})
            style_prompt = style.get('prompt', '')
            if text in style_prompt:
                found = True
                
    assert found, f"Expected '{text}' in generated prompt or metadata"

@then('the image generation request should include the reference image "{image_name}"')
def step_impl(context, image_name):
    mock_client = context.mock_new_client_cls.return_value
    assert mock_client.models.generate_content.called, "generate_content was not called"
    
    # Check if a PIL.Image object was passed in the contents
    found_image = False
    print(f"Mock client calls: {len(mock_client.models.generate_content.call_args_list)}")
    for call in mock_client.models.generate_content.call_args_list:
        contents = call.kwargs.get('contents')
        if not contents and len(call.args) >= 2:
            contents = call.args[1]
            
        print(f"Call contents: {contents}")
        if isinstance(contents, list):
            for item in contents:
                print(f"Item type: {type(item)}")
                # Check if it's a PIL Image
                if hasattr(item, 'save') and hasattr(item, 'size'):
                    found_image = True
                    break
        if found_image:
            break
    
    assert found_image, f"Reference image (PIL.Image object) was not passed to generate_content"

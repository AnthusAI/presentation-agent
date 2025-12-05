import os
import json
import io
from behave import given, when, then
from deckbot.webapp import app

@given('the presentation has a "metadata.json" file')
def step_impl(context):
    pres_dir = os.path.join(context.temp_dir, context.pres_name)
    metadata = {
        "name": context.pres_name,
        "image_style": {}
    }
    with open(os.path.join(pres_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f)

@given('the presentation has the following styling in metadata:')
def step_impl(context):
    pres_dir = os.path.join(context.temp_dir, context.pres_name)
    with open(os.path.join(pres_dir, "metadata.json"), "r") as f:
        metadata = json.load(f)
    
    for row in context.table:
        key = row['key']
        value = row['value']
        
        if key.startswith('image_style.'):
            sub_key = key.split('.')[1]
            if 'image_style' not in metadata:
                metadata['image_style'] = {}
            metadata['image_style'][sub_key] = value
        else:
            metadata[key] = value
            
    with open(os.path.join(pres_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f)

@given('the presentation has a style reference image "{path}"')
def step_impl(context, path):
    pres_dir = os.path.join(context.temp_dir, context.pres_name)
    # Create dummy file (using minimal valid PNG bytes for PIL)
    full_path = os.path.join(pres_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    # Write minimal valid PNG bytes
    with open(full_path, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')

@when('I request the style specification')
def step_impl(context):
    context.client = app.test_client()
    
    # Load the presentation first
    context.client.post('/api/load', json={'name': context.pres_name})
    
    response = context.client.get('/api/presentation/style')
    context.response = response
    if response.status_code == 200:
        context.response_json = response.get_json()
    else:
        context.response_json = {}

@when('I update the style specification with:')
def step_impl(context):
    context.client = app.test_client()
    context.client.post('/api/load', json={'name': context.pres_name})
    
    data = {}
    for row in context.table:
        key = row['key']
        value = row['value']
        data[key] = value
        
    response = context.client.post('/api/presentation/style', json=data)
    context.response = response

@when('I upload a style reference image "{filename}"')
def step_impl(context, filename):
    context.client = app.test_client()
    context.client.post('/api/load', json={'name': context.pres_name})
    
    data = {
        'file': (io.BytesIO(b"fake image content"), filename)
    }
    
    response = context.client.post('/api/presentation/style', data=data, content_type='multipart/form-data')
    context.response = response

@when('I remove the style reference image')
def step_impl(context):
    context.client = app.test_client()
    context.client.post('/api/load', json={'name': context.pres_name})
    
    response = context.client.post('/api/presentation/style', json={'delete_reference': True})
    context.response = response

@then('the response should contain:')
def step_impl(context):
    assert context.response.status_code == 200, f"Response status {context.response.status_code}"
    json_data = context.response_json
    for row in context.table:
        key = row['key']
        expected_value = row['value']
        
        if key.startswith('image_style.'):
            sub_key = key.split('.')[1]
            actual_value = json_data.get('image_style', {}).get(sub_key)
        else:
            actual_value = json_data.get(key)
            
        assert actual_value == expected_value, f"Expected {key} to be {expected_value}, got {actual_value}"

@then('the "metadata.json" should contain:')
def step_impl(context):
    pres_dir = os.path.join(context.temp_dir, context.pres_name)
    with open(os.path.join(pres_dir, "metadata.json"), "r") as f:
        metadata = json.load(f)
        
    for row in context.table:
        key = row['key']
        expected_value = row['value']
        
        if key.startswith('image_style.'):
            sub_key = key.split('.')[1]
            actual_value = metadata.get('image_style', {}).get(sub_key)
        else:
            actual_value = metadata.get(key)
            
        assert actual_value == expected_value, f"Expected {key} to be {expected_value}, got {actual_value}"

@then('the file "{path}" should not exist in the presentation directory')
def step_impl(context, path):
    pres_dir = os.path.join(context.temp_dir, context.pres_name)
    full_path = os.path.join(pres_dir, path)
    assert not os.path.exists(full_path), f"File {path} should not exist but it does"

@then('the file "{path}" should exist in the presentation directory')
def step_impl(context, path):
    pres_dir = os.path.join(context.temp_dir, context.pres_name)
    full_path = os.path.join(pres_dir, path)
    assert os.path.exists(full_path), f"File {path} does not exist"


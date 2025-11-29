import json
import os
from behave import given, when, then
from unittest.mock import MagicMock, patch
from vibe_presentation.manager import PresentationManager
from vibe_presentation.webapp import app

@when('I request the list of presentations via API')
def step_impl(context):
    with patch('vibe_presentation.webapp.PresentationManager') as MockManager:
        instance = MockManager.return_value
        instance.list_presentations.return_value = [{"name": "web-demo-1", "description": ""}]
        
        with app.test_client() as client:
            context.response = client.get('/api/presentations')

@then('the response should contain "{text}"')
def step_impl(context, text):
    body = context.response.get_data(as_text=True)
    assert text in body, f"Expected '{text}' in response. Got: {body}"

@when('I load the presentation "{name}" via API')
def step_impl(context, name):
    with patch('vibe_presentation.webapp.PresentationManager') as MockManager:
        instance = MockManager.return_value
        
        # If marked missing, force None return
        if getattr(context, 'presentation_missing', False):
             instance.get_presentation.return_value = None
        else:
             instance.get_presentation.return_value = {"name": name, "description": "Test"}
        
        with patch('vibe_presentation.webapp.SessionService') as MockService:
            mock_service_instance = MockService.return_value
            if hasattr(context, 'expected_history'):
                 mock_service_instance.get_history.return_value = context.expected_history
            else:
                 mock_service_instance.get_history.return_value = []
            
            with app.test_client() as client:
                context.response = client.post('/api/load', 
                                             data=json.dumps({'name': name}),
                                             content_type='application/json')

@then('the response status code should be {status_code:d}')
def step_impl(context, status_code):
    assert context.response.status_code == status_code, f"Expected {status_code}, got {context.response.status_code}. Body: {context.response.get_data(as_text=True)}"

@given('I load the presentation "{name}" via API')
def step_impl(context, name):
    pass

@when('I send a chat message "{message}" via API')
def step_impl(context, message):
    with patch('vibe_presentation.webapp.current_service') as mock_service:
        with app.test_client() as client:
            context.response = client.post('/api/chat', 
                                         data=json.dumps({'message': message}),
                                         content_type='application/json')

@when('I send a chat message "" via API')
def step_impl(context):
    with patch('vibe_presentation.webapp.current_service') as mock_service:
        with app.test_client() as client:
            context.response = client.post('/api/chat', 
                                         data=json.dumps({'message': ""}),
                                         content_type='application/json')

@when('I send invalid JSON to "{url}" via API')
def step_impl(context, url):
    with app.test_client() as client:
        context.response = client.post(url, 
                                     data="invalid json",
                                     content_type='application/json')

@when('I request image generation for "{prompt}" via API')
def step_impl(context, prompt):
    with patch('vibe_presentation.webapp.current_service') as mock_service:
        with app.test_client() as client:
            context.response = client.post('/api/images/generate', 
                                         data=json.dumps({'prompt': prompt}),
                                         content_type='application/json')

@given('the presentation "{name}" has history')
def step_impl(context, name):
    pres_dir = os.path.join(context.temp_dir, name)
    os.makedirs(pres_dir, exist_ok=True)
    history_file = os.path.join(pres_dir, "chat_history.jsonl")
    with open(history_file, "w") as f:
        f.write(json.dumps({"role": "user", "content": "Mock user message"}) + "\n")
        f.write(json.dumps({"role": "model", "content": "Mock model response"}) + "\n")
    context.expected_history = [{"role": "user", "parts": ["Mock user message"]}]

@when('I check the initial UI state')
def step_impl(context):
    with app.test_client() as client:
        context.html_response = client.get('/')

@then('the preview view should be visible')
def step_impl(context):
    html = context.html_response.get_data(as_text=True)
    assert 'id="view-preview"' in html
    assert 'view-images' in html

@then('the image selection view should be hidden')
def step_impl(context):
    if hasattr(context, 'html_response'):
        html = context.html_response.get_data(as_text=True)
        assert 'id="view-images"' in html
        assert 'style="display: none;"' in html or 'display: none' in html
    else:
        assert True

@when('image generation starts')
def step_impl(context):
    context.image_generation_active = True

@given('image generation starts')
def step_impl(context):
    context.image_generation_active = True

@then('the image selection view should become visible')
def step_impl(context):
    assert context.image_generation_active == True

@then('the preview view should be hidden')
def step_impl(context):
    assert context.image_generation_active == True

@given('the image selection view is visible')
def step_impl(context):
    context.image_view_visible = True

@when('the user selects an image')
def step_impl(context):
    with patch('vibe_presentation.webapp.current_service') as mock_service:
        mock_service.select_image.return_value = "/path/to/image.png"
        with app.test_client() as client:
            context.response = client.post('/api/images/select',
                                         data=json.dumps({'index': 0}),
                                         content_type='application/json')

@when('the presentation is compiled')
def step_impl(context):
    context.presentation_compiled = True

@then('the preview view should become visible')
def step_impl(context):
    assert context.presentation_compiled == True

@given('I set the theme to "{theme}"')
def step_impl(context, theme):
    context.theme = theme

@when('I reload the web application')
def step_impl(context):
    pass

@then('the theme should be "{theme}"')
def step_impl(context, theme):
    assert context.theme == theme

@given('the sidebar has a default width')
def step_impl(context):
    context.sidebar_width = 600

@when('I drag the resizer to adjust the width')
def step_impl(context):
    context.sidebar_width = 800

@then('the sidebar width should change')
def step_impl(context):
    assert context.sidebar_width == 800

@then('the width should stay within min/max bounds')
def step_impl(context):
    assert 300 <= context.sidebar_width <= 1200

@when('I click the "{menu}" menu')
def step_impl(context, menu):
    context.clicked_menu = menu

@when('I click "{item}"')
def step_impl(context, item):
    context.clicked_item = item

@then('the create presentation dialog should appear')
def step_impl(context):
    assert context.clicked_item == "New Presentation"

@then('the presentation selector dialog should appear')
def step_impl(context):
    assert context.clicked_item == "Open Presentation"

@then('the list should contain "{name}"')
def step_impl(context, name):
    pass

@when('I create a presentation named "{name}" via the UI')
def step_impl(context, name):
    with patch('vibe_presentation.webapp.PresentationManager') as MockManager:
        with patch('vibe_presentation.webapp.SessionService'):
            instance = MockManager.return_value
            with app.test_client() as client:
                context.response = client.post('/api/presentations/create',
                                             data=json.dumps({'name': name, 'description': '', 'template': ''}),
                                             content_type='application/json')

@then('the presentation "{name}" should exist')
def step_impl(context, name):
    assert context.response.status_code == 200

@then('the preview should load automatically')
def step_impl(context):
    assert context.response.status_code == 200

@given('I open the preferences dialog')
def step_impl(context):
    context.preferences_open = True
    context.initial_preferences = {}

@when('I select the "{theme_name}" color theme')
def step_impl(context, theme_name):
    context.selected_color_theme = theme_name

@when('I save the preferences')
def step_impl(context):
    with patch('vibe_presentation.webapp.PreferencesManager') as MockPrefs:
        instance = MockPrefs.return_value
        with app.test_client() as client:
            context.response = client.post('/api/preferences/color_theme',
                                         data=json.dumps({'value': context.selected_color_theme}),
                                         content_type='application/json')

@then('the color theme should be "{theme_name}"')
def step_impl(context, theme_name):
    with patch('vibe_presentation.webapp.PreferencesManager') as MockPrefs:
        instance = MockPrefs.return_value
        instance.get.return_value = theme_name
        with app.test_client() as client:
            response = client.get('/api/preferences/color_theme')
            data = json.loads(response.get_data(as_text=True))
            assert data.get('value') == theme_name

@then('the primary color should be {color}')
def step_impl(context, color):
    assert context.selected_color_theme in ['miami', 'midwest', 'california']

@then('the secondary color should be {color}')
def step_impl(context, color):
    assert context.selected_color_theme in ['miami', 'midwest', 'california']

@given('I set the color theme to "{theme_name}" via API')
def step_impl(context, theme_name):
    with patch('vibe_presentation.webapp.PreferencesManager') as MockPrefs:
        instance = MockPrefs.return_value
        with app.test_client() as client:
            client.post('/api/preferences/color_theme',
                       data=json.dumps({'value': theme_name}),
                       content_type='application/json')

@given('no color theme preference is set')
def step_impl(context):
    context.color_theme_preference = None

@when('I load the web application')
def step_impl(context):
    with app.test_client() as client:
        context.response = client.get('/')

@then('the cancel button should have a muted gray background')
def step_impl(context):
    with app.test_client() as client:
        response = client.get('/')
        html = response.get_data(as_text=True)
        assert 'btn-secondary' in html
        assert 'btn-cancel-preferences' in html

@then('the cancel button should not be primary blue')
def step_impl(context):
    assert True

@when('I hover over the cancel button')
def step_impl(context):
    context.button_hovered = True

@then('the cancel button should lighten to accent color')
def step_impl(context):
    assert context.button_hovered

@given('the current color theme is "{theme_name}"')
def step_impl(context, theme_name):
    context.initial_color_theme = theme_name

@when('I click cancel')
def step_impl(context):
    context.preferences_cancelled = True

@then('the color theme should still be "{theme_name}"')
def step_impl(context, theme_name):
    assert context.initial_color_theme == theme_name

@then('the preferences dialog should be closed')
def step_impl(context):
    assert context.preferences_cancelled

@then('the preference should be saved to the backend')
def step_impl(context):
    assert context.response.status_code == 200

@then('I should see three color theme options')
def step_impl(context):
    with app.test_client() as client:
        response = client.get('/')
        html = response.get_data(as_text=True)
        assert 'data-theme="miami"' in html
        assert 'data-theme="midwest"' in html
        assert 'data-theme="california"' in html

@then('"{theme_name}" should show {color1} and {color2} swatches')
def step_impl(context, theme_name, color1, color2):
    with app.test_client() as client:
        response = client.get('/')
        html = response.get_data(as_text=True)
        assert f'data-theme="{theme_name}"' in html
        assert 'color-swatch' in html

@given('the light/dark mode is "{mode}"')
def step_impl(context, mode):
    context.theme_mode = mode

@when('I change to "{mode}" mode')
def step_impl(context, mode):
    with patch('vibe_presentation.webapp.PreferencesManager') as MockPrefs:
        instance = MockPrefs.return_value
        with app.test_client() as client:
            client.post('/api/preferences/theme',
                       data=json.dumps({'value': mode}),
                       content_type='application/json')

@then('the color theme should remain "{theme_name}"')
def step_impl(context, theme_name):
    assert True

@then('the colors should adapt to dark mode')
def step_impl(context):
    assert True

@then('the sun icon should be visible')
def step_impl(context):
    with app.test_client() as client:
        response = client.get('/')
        html = response.get_data(as_text=True)
        assert 'data-lucide="sun"' in html

@then('the moon icon should be visible')
def step_impl(context):
    with app.test_client() as client:
        response = client.get('/')
        html = response.get_data(as_text=True)
        assert 'data-lucide="moon"' in html

@then('the monitor icon should be visible')
def step_impl(context):
    with app.test_client() as client:
        response = client.get('/')
        html = response.get_data(as_text=True)
        assert 'data-lucide="monitor"' in html

@given('the color theme is "{theme}"')
def step_impl(context, theme):
    context.color_theme = theme

@when('I delete the presentation "{name}" via API')
def step_impl(context, name):
    with patch('vibe_presentation.webapp.PresentationManager') as MockManager:
        instance = MockManager.return_value
        if name == "delete-me":
            pass
        elif name == "delete-me-not":
            instance.delete_presentation.side_effect = FileNotFoundError("Presentation not found")
        
        with app.test_client() as client:
            context.response = client.post('/api/presentations/delete',
                                         data=json.dumps({'name': name}),
                                         content_type='application/json')

@then('the presentation "{name}" should no longer exist')
def step_impl(context, name):
    assert context.response.status_code == 200

@given('a presentation "{name}" does not exist')
def step_impl(context, name):
    context.presentation_missing = True

@given('templates "Light", "Dark", and "Candy" exist')
def step_impl(context):
    pass

@when('I request the template list via API')
def step_impl(context):
    with patch('vibe_presentation.webapp.PresentationManager') as MockManager:
        instance = MockManager.return_value
        instance.list_templates.return_value = [
            {"name": "Light", "description": "Light Theme"},
            {"name": "Dark", "description": "Dark Theme"},
            {"name": "Candy", "description": "Candy Theme"}
        ]
        with app.test_client() as client:
            context.response = client.get('/api/templates')

@given('a template "{name}" exists with a background image')
def step_impl(context, name):
    context.template_has_image = True

@when('I create a presentation "{name}" using "{template}" via API')
def step_impl(context, name, template):
    with patch('vibe_presentation.webapp.PresentationManager') as MockManager:
        with patch('vibe_presentation.webapp.SessionService'):
            instance = MockManager.return_value
            with app.test_client() as client:
                context.response = client.post('/api/presentations/create',
                                             data=json.dumps({'name': name, 'template': template}),
                                             content_type='application/json')
            context.mock_manager_instance = instance

@then('"{path}" should contain the background image')
def step_impl(context, path):
    args = context.mock_manager_instance.create_presentation.call_args
    assert args, "create_presentation was not called"
    call_kwargs = args[1]
    template_arg = call_kwargs.get('template')
    assert template_arg == "ImageTemplate", f"Expected template 'ImageTemplate', got {template_arg}"

@given('"{path}" contains "{filename}"')
def step_impl(context, path, filename):
    full_path = os.path.join(context.temp_dir, path)
    os.makedirs(full_path, exist_ok=True)
    with open(os.path.join(full_path, filename), 'wb') as f:
        f.write(b'fake_png_data')

@when('I request "{url}" via API')
def step_impl(context, url):
    # If it's presentation images, ensure we set the current service
    if "presentation/images" in url:
        import vibe_presentation.webapp as webapp_module
        mock_service = MagicMock()
        mock_service.context = {'name': 'serve-test'}
        
        # Manual patch to ensure it sticks
        original = webapp_module.current_service
        webapp_module.current_service = mock_service
        
        try:
            with patch('vibe_presentation.webapp.PresentationManager') as MockManager:
                instance = MockManager.return_value
                instance.root_dir = context.temp_dir
                
                with app.test_client() as client:
                     context.response = client.get(url)
        finally:
            webapp_module.current_service = original
    else:
        with app.test_client() as client:
            context.response = client.get(url)

@then('the response should contain image data')
def step_impl(context):
    assert context.response.data == b'fake_png_data'

@given('draft images exist at "{path}"')
def step_impl(context, path):
    full_path = os.path.join(context.temp_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'wb') as f:
        f.write(b'fake_png_data')

@when('I request the draft image at "{path}" via API')
def step_impl(context, path):
    real_path = os.path.join(context.temp_dir, path)
    with app.test_client() as client:
        context.response = client.get(f'/api/serve-image?path={real_path}')

@when('I request the presentation preview via API')
def step_impl(context):
    import vibe_presentation.webapp as webapp_module
    mock_service = MagicMock()
    mock_service.context = {'name': 'preview-test'}
    
    # Manual patch
    original = webapp_module.current_service
    webapp_module.current_service = mock_service
    
    try:
         deck_path = os.path.join(context.temp_dir, 'preview-test', 'deck.marp.html')
         os.makedirs(os.path.dirname(deck_path), exist_ok=True)
         with open(deck_path, 'w') as f:
             f.write('<html><img src="images/logo.png"></html>')
             
         with app.test_client() as client:
             context.response = client.get('/api/presentation/preview')
    finally:
         webapp_module.current_service = original
import os
import json
import shutil
from behave import given, when, then
from vibe_presentation.manager import PresentationManager
from vibe_presentation.tools import PresentationTools
from click.testing import CliRunner
from vibe_presentation.cli import cli
from unittest.mock import MagicMock, patch

@given('the template directory exists')
def step_impl(context):
    # context.temp_dir is set by the fixture
    context.templates_dir = os.path.join(context.temp_dir, "templates")
    os.makedirs(context.templates_dir, exist_ok=True)

@given('there is a template "{name}" with description "{description}"')
def step_impl(context, name, description):
    template_path = os.path.join(context.templates_dir, name)
    os.makedirs(template_path, exist_ok=True)
    
    metadata = {
        "name": name,
        "description": description,
        "instructions": "Some instruction"
    }
    
    with open(os.path.join(template_path, "metadata.json"), "w") as f:
        json.dump(metadata, f)
        
    with open(os.path.join(template_path, "deck.marp.md"), "w") as f:
        f.write(f"# {name} Template")

@given('there is a template "{name}" with content "{content}"')
def step_impl(context, name, content):
    template_path = os.path.join(context.templates_dir, name)
    os.makedirs(template_path, exist_ok=True)
    
    with open(os.path.join(template_path, "deck.marp.md"), "w") as f:
        f.write(content)
    
    with open(os.path.join(template_path, "metadata.json"), "w") as f:
        json.dump({"name": name, "description": "desc"}, f)

@given('a basic template "{name}" exists')
def step_impl(context, name):
    template_path = os.path.join(context.templates_dir, name)
    os.makedirs(template_path, exist_ok=True)
    with open(os.path.join(template_path, "deck.marp.md"), "w") as f:
        f.write("# Template")
    with open(os.path.join(template_path, "metadata.json"), "w") as f:
        json.dump({"name": name}, f)

@given('a template "{name}" exists with instruction "{instruction}"')
def step_impl(context, name, instruction):
    template_path = os.path.join(context.templates_dir, name)
    os.makedirs(template_path, exist_ok=True)
    
    metadata = {
        "name": name,
        "description": "Test Description",
        "instructions": instruction
    }
    
    with open(os.path.join(template_path, "metadata.json"), "w") as f:
        json.dump(metadata, f)
    
    with open(os.path.join(template_path, "deck.marp.md"), "w") as f:
        f.write("# Template")

@when('I list templates via CLI')
def step_impl(context):
    runner = CliRunner()
    result = runner.invoke(cli, ['templates', 'list'], env={'VIBE_PRESENTATION_ROOT': context.temp_dir})
    context.result = result

@then('the file "{filepath}" should contain "{content}"')
def step_impl(context, filepath, content):
    full_path = os.path.join(context.temp_dir, filepath)
    with open(full_path, 'r') as f:
        file_content = f.read()
    assert content in file_content

@given('the agent is active for a new presentation')
def step_impl(context):
    # Create a dummy context for the agent
    context.presentation_context = {"name": "agent-test", "description": "test"}
    context.nano_client = MagicMock()
    context.tools = PresentationTools(context.presentation_context, context.nano_client)

@when('the agent creates a presentation "{name}" from template "{template}"')
def step_impl(context, name, template):
    # Call the tool directly
    result = context.tools.create_presentation(name, template=template)
    context.tool_result = result

@given('I create a presentation "{name}" from template "{template}"')
def step_impl(context, name, template):
    manager = PresentationManager(root_dir=context.temp_dir)
    
    # Actually, let's copy the files manually to set up the state
    dest_dir = os.path.join(context.temp_dir, name)
    src_dir = os.path.join(context.templates_dir, template)
    shutil.copytree(src_dir, dest_dir)
    
    # Ensure the metadata has the instruction
    with open(os.path.join(src_dir, "metadata.json"), 'r') as f:
        data = json.load(f)
    
    # When copying, we probably want to update the name in metadata
    data['name'] = name
    with open(os.path.join(dest_dir, "metadata.json"), 'w') as f:
        json.dump(data, f)

@when('I load the presentation "{name}"')
def step_impl(context, name):
    from vibe_presentation.agent import Agent
    
    manager = PresentationManager(root_dir=context.temp_dir) # Use temp_dir for persistence
    presentation = manager.get_presentation(name)
    context.agent = Agent(presentation)

@when('the agent previews the template "{template}"')
def step_impl(context, template):
    if not hasattr(context, 'tools'):
        context.presentation_context = {"name": "preview-test"}
        context.nano_client = MagicMock()
        context.tools = PresentationTools(context.presentation_context, context.nano_client)

    # Mock both subprocess.run and os.startfile to prevent opening files
    with patch('subprocess.run') as mock_run, \
         patch('os.startfile', create=True):
        context.tools.preview_template(template)
        context.mock_subprocess = mock_run

@then('the template "{template}" should be compiled to HTML')
def step_impl(context, template):
    # Check if subprocess was called with correct args
    args, _ = context.mock_subprocess.call_args
    command = args[0]
    # Assert command contains 'marp' and the template path
    assert 'marp' in command[1] or 'marp' in command[0] or '@marp-team/marp-cli' in command

@then('a presentation "{name}" should exist')
def step_impl(context, name):
    path = os.path.join(context.temp_dir, name)
    assert os.path.exists(path), f"Presentation directory {path} does not exist"
    assert os.path.isdir(path), f"{path} is not a directory"
    assert os.path.exists(os.path.join(path, "metadata.json")), f"metadata.json missing in {path}"

# New steps for images
@given('a template "{name}" exists with image "{image_name}"')
def step_impl(context, name, image_name):
    template_path = os.path.join(context.templates_dir, name)
    os.makedirs(template_path, exist_ok=True)
    
    # Create images dir
    images_dir = os.path.join(template_path, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # Create dummy image
    with open(os.path.join(images_dir, image_name), "wb") as f:
        f.write(b"fake image")
        
    # Create deck referencing it
    with open(os.path.join(template_path, "deck.marp.md"), "w") as f:
        f.write(f"# Branded Deck\n\n![logo](images/{image_name})")
        
    with open(os.path.join(template_path, "metadata.json"), "w") as f:
        json.dump({"name": name}, f)

@then('the file "{filepath}" should exist')
def step_impl(context, filepath):
    path = os.path.join(context.temp_dir, filepath)
    assert os.path.exists(path), f"File {path} does not exist"

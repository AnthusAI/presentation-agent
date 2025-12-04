import os
import time
from behave import given, when, then, step
from unittest.mock import MagicMock, patch
from deckbot.tools import PresentationTools
from deckbot.manager import PresentationManager

@given('I have an auto-compilation test presentation named "{name}"')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    # Clean up if exists
    if os.path.exists(os.path.join(context.temp_dir, name)):
        import shutil
        shutil.rmtree(os.path.join(context.temp_dir, name))
    
    manager.create_presentation(name, "Test description")
    context.current_presentation_name = name
    context.presentation_dir = os.path.join(context.temp_dir, name)
    
    # Initialize tools with mocked dependencies
    context.nano_client = MagicMock()
    presentation = manager.get_presentation(name)
    context.tools = PresentationTools(presentation, context.nano_client, root_dir=context.temp_dir)

@step('I use the tool "{tool_name}" to create "{filename}" with content "{content}"')
def create_file_step(context, tool_name, filename, content):
    # Mock subprocess to avoid actual Marp execution
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:
        
        mock_run.return_value.returncode = 0
        
        if tool_name == "write_file":
            context.last_result = context.tools.write_file(filename, content)
        else:
            raise ValueError(f"Unknown tool {tool_name}")
            
        context.mock_run = mock_run

@when('I use the tool "replace_text" on "{filename}" to replace "{old}" with "{new}"')
def step_impl(context, filename, old, new):
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:
        
        mock_run.return_value.returncode = 0
        context.last_result = context.tools.replace_text(filename, old, new)
        context.mock_run = mock_run

@when('I use the tool "copy_file" to copy "{source}" to "{destination}"')
def step_impl(context, source, destination):
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:
        
        mock_run.return_value.returncode = 0
        context.last_result = context.tools.copy_file(source, destination)
        context.mock_run = mock_run

@when('I use the tool "move_file" to move "{source}" to "{destination}"')
def step_impl(context, source, destination):
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:
        
        mock_run.return_value.returncode = 0
        context.last_result = context.tools.move_file(source, destination)
        context.mock_run = mock_run

@when('I use the tool "delete_file" to delete "{filename}"')
def step_impl(context, filename):
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:
        
        mock_run.return_value.returncode = 0
        context.last_result = context.tools.delete_file(filename)
        context.mock_run = mock_run

@when('I use the tool "generate_image" with prompt "{prompt}"')
def step_impl(context, prompt):
    # Mock NanoClient response
    context.nano_client.generate_candidates.return_value = {
        'candidates': ['/tmp/1.png'],
        'batch_slug': 'test-batch'
    }
    
    # Mock save_selection to return a path in the presentation images dir
    # Needs to be absolute for tools.py to relpath it correctly
    saved_path = os.path.abspath(os.path.join(context.presentation_dir, 'images', 'image_1.png'))
    context.nano_client.save_selection.return_value = saved_path
    
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen, \
         patch('rich.prompt.IntPrompt.ask', return_value=1): # Select first image
        
        mock_run.return_value.returncode = 0
        context.last_result = context.tools.generate_image(prompt)
        context.mock_run = mock_run

@then('the presentation should be compiled to HTML')
def step_impl(context):
    # Verify subprocess.run was called with expected arguments for compilation
    assert context.mock_run.called, "Compilation command was not called"
    
    # Check if any call args match the marp command
    marp_called = False
    for call in context.mock_run.call_args_list:
        args = call[0][0] # First arg of call is the command list
        if "npx" in args and "@marp-team/marp-cli" in args:
            marp_called = True
            break
            
    assert marp_called, "Marp CLI was not invoked"

@when('I use the tool "write_file" to create "{filename}" with valid Marp content')
def step_impl(context, filename):
    content = "---\nmarp: true\n---\n# Slide 1"
    # Call implementation function directly to avoid parsing errors with newlines
    create_file_step(context, "write_file", filename, content)

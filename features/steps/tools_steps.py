from behave import given, when, then
import os
from unittest.mock import MagicMock, patch
from vibe_presentation.tools import PresentationTools
from vibe_presentation.manager import PresentationManager

@given('I have a presentation named "{name}"')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    manager.create_presentation(name, "Test description")
    context.current_presentation_name = name

@given('the presentation contains an empty file "{filename}"')
def step_impl(context, filename):
    path = os.path.join(context.temp_dir, "test-deck", filename)
    with open(path, 'w') as f:
        f.write("") # Empty file

@given('the presentation contains a file "{filename}" with content "{content}"')
def step_impl(context, filename, content):
    # Use 'context.current_presentation_name' if set, else default to 'test-deck'
    # But the previous step 'Given I have a presentation named "{name}"' doesn't set 'current_presentation_name'
    # in this file. It creates it on disk.
    # We need to find which presentation we are talking about.
    # Usually "Given I have a presentation named 'X'" sets up X.
    # If multiple exist, this step is ambiguous unless we track the "active" one.
    
    # Let's assume the most recently created one or try to infer from scenario?
    # Or just check if "test-deck" exists, if not check others.
    
    presentation_name = "test-deck" # Default
    
    # Check if we have explicit name in context
    if hasattr(context, 'current_presentation_name'):
        presentation_name = context.current_presentation_name
    # Else check directories in temp_dir
    elif os.path.exists(os.path.join(context.temp_dir, "test-deck")):
        presentation_name = "test-deck"
    else:
        # Find first dir that looks like a presentation
        dirs = [d for d in os.listdir(context.temp_dir) if os.path.isdir(os.path.join(context.temp_dir, d))]
        if dirs:
            presentation_name = dirs[0]

    path = os.path.join(context.temp_dir, presentation_name, filename)
    # Ensure parent dir exists (for nested files if any, though usually root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w') as f:
        f.write(content)

@when('the agent uses the "list_files" tool')
def step_impl(context):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation("test-deck")
    tools = PresentationTools(presentation, MagicMock())
    context.tool_result = tools.list_files()

@then('the result should contain "{filename}"')
def step_impl(context, filename):
    assert filename in context.tool_result

@when('the agent uses the "read_file" tool for "{filename}"')
def step_impl(context, filename):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation("test-deck")
    tools = PresentationTools(presentation, MagicMock())
    context.tool_result = tools.read_file(filename)

@then('the result should match "{content}"')
def step_impl(context, content):
    assert context.tool_result == content

@when('the agent uses the "write_file" tool for "{filename}" with content "{content}"')
def step_impl(context, filename, content):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation("test-deck")
    tools = PresentationTools(presentation, MagicMock())
    context.tool_result = tools.write_file(filename, content)

@then('the file "{filename}" should exist in the presentation')
def step_impl(context, filename):
    path = os.path.join(context.temp_dir, "test-deck", filename)
    assert os.path.exists(path)

@then('the content of "{filename}" should match "{content}"')
def step_impl(context, filename, content):
    path = os.path.join(context.temp_dir, "test-deck", filename)
    with open(path, 'r') as f:
        assert f.read() == content

@given('Marp CLI is available')
def step_impl(context):
    # We will mock subprocess, so we don't strictly need it installed
    pass

@when('the agent uses the "compile_presentation" tool')
def step_impl(context):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation("test-deck")
    tools = PresentationTools(presentation, MagicMock())
    
    # Mock both subprocess.run and os.startfile to prevent opening files
    with patch('subprocess.run') as mock_run, \
         patch('os.startfile', create=True):
        # Mock successful run
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"Success"
        context.tool_result = tools.compile_presentation()
        context.mock_run = mock_run

@then('the result should indicate success')
def step_impl(context):
    assert "Compilation successful." in context.tool_result

@when('the agent uses the "generate_image" tool with prompt "{prompt}"')
def step_impl(context, prompt):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation("test-deck")
    
    mock_nano = MagicMock()
    mock_nano.generate_candidates.return_value = ["drafts/1.png", "drafts/2.png"]
    mock_nano.save_selection.return_value = os.path.join(context.temp_dir, "test-deck", "images", "selected.png")
    
    tools = PresentationTools(presentation, mock_nano)
    
    # Mock console input for selection
    with patch('rich.prompt.IntPrompt.ask', return_value=1):
        context.tool_result = tools.generate_image(prompt)
        context.mock_nano = mock_nano

@then('the Nano Banana client should generate candidates')
def step_impl(context):
    context.mock_nano.generate_candidates.assert_called()

@then('the result should be a relative file path')
def step_impl(context):
    # We expect "images/selected.png" or similar
    # Since save_selection mocked to return abs path, but generate_image returns relpath
    # The mock needs to be consistent.
    # tools.py: saved_path = self.nano_client.save_selection(...)
    #           rel_path = os.path.relpath(saved_path, self.presentation_dir)
    assert "images" in context.tool_result

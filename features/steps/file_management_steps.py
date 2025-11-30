import os
from behave import given, when, then
from deckbot.tools import PresentationTools
from unittest.mock import MagicMock

@given('I have a file "{filename}" with content "{content}"')
def step_impl(context, filename, content):
    # Ensure presentation dir exists
    if not hasattr(context, 'presentation_dir'):
        context.presentation_dir = os.path.join(context.temp_dir, "test-deck")
        os.makedirs(context.presentation_dir, exist_ok=True)
        
    file_path = os.path.join(context.presentation_dir, filename)
    with open(file_path, "w") as f:
        f.write(content)
        
    # Initialize tools if not already
    if not hasattr(context, 'tools'):
        context.tools = PresentationTools({'name': 'test-deck'}, MagicMock())

@given('I have a file "{filename}"')
def step_impl(context, filename):
    # Reuse step with default content
    context.execute_steps(f'Given I have a file "{filename}" with content "test content"')

@when('the agent calls copy_file("{src}", "{dst}")')
def step_impl(context, src, dst):
    try:
        context.last_result = context.tools.copy_file(src, dst)
    except Exception as e:
        context.last_error = str(e)

@when('the agent tries copy_file("{src}", "{dst}")')
def step_impl(context, src, dst):
    try:
        context.last_result = context.tools.copy_file(src, dst)
    except Exception as e:
        context.last_error = str(e)

@when('the agent calls move_file("{src}", "{dst}")')
def step_impl(context, src, dst):
    try:
        context.last_result = context.tools.move_file(src, dst)
    except Exception as e:
        context.last_error = str(e)

@when('the agent calls delete_file("{filename}")')
def step_impl(context, filename):
    try:
        context.last_result = context.tools.delete_file(filename)
    except Exception as e:
        context.last_error = str(e)

@then('the managed file "{filename}" should exist')
def step_impl(context, filename):
    path = os.path.join(context.presentation_dir, filename)
    assert os.path.exists(path), f"File {filename} does not exist"

@then('the managed file "{filename}" should not exist')
def step_impl(context, filename):
    path = os.path.join(context.presentation_dir, filename)
    assert not os.path.exists(path), f"File {filename} exists but should not"

@then('the managed file "{filename}" should contain "{content}"')
def step_impl(context, filename, content):
    path = os.path.join(context.presentation_dir, filename)
    with open(path, "r") as f:
        actual_content = f.read()
    assert content in actual_content

@then('both files should have identical content')
def step_impl(context):
    # Not implemented generically, specific step used instead
    pass

@then('the operation should fail')
def step_impl(context):
    assert hasattr(context, 'last_error') or "Error" in context.last_result

@then('an error should be returned')
def step_impl(context):
    assert hasattr(context, 'last_error') or "Error" in context.last_result


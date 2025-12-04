from behave import given, when, then
import os
from deckbot.tools import PresentationTools
from unittest.mock import MagicMock

# Reuse context setup logic if needed, or assume it's set up by other steps
# But we need to be safe.

@given('a validation test presentation "{name}" exists')
def step_impl(context, name):
    context.presentation_name = name
    # We use a temp dir for tests usually
    if not hasattr(context, 'temp_dir'):
        # Fallback if not running in full test harness
        import tempfile
        context.temp_dir = tempfile.mkdtemp()
        
    context.presentation_dir = os.path.join(context.temp_dir, name)
    os.makedirs(context.presentation_dir, exist_ok=True)
    
    # Initialize tools
    context.tools = PresentationTools({'name': name}, MagicMock(), root_dir=context.temp_dir)

@when('I update "{filename}" with the following content:')
def step_impl(context, filename):
    content = context.text
    try:
        context.last_result = context.tools.write_file(filename, content)
        context.last_error = None
    except Exception as e:
        context.last_result = None
        context.last_error = str(e)

@then('the file update validation should succeed')
def step_impl(context):
    # Check if result indicates success (starts with "Successfully" usually)
    # or simply didn't raise exception and returned a string not starting with "Error"
    result = getattr(context, 'last_result', "")
    assert result and not result.startswith("Error"), f"Update failed: {result}"

@then('the file update validation should fail')
def step_impl(context):
    result = getattr(context, 'last_result', "")
    error = getattr(context, 'last_error', "")
    
    failed = (result and result.startswith("Error")) or error
    assert failed, "Update succeeded but should have failed"

@then('the tool output should contain "{text}"')
def step_impl(context, text):
    result = getattr(context, 'last_result', "")
    assert text in result, f"Expected '{text}' in response, got: {result}"

@then('the tool error should mention "{text}"')
def step_impl(context, text):
    result = getattr(context, 'last_result', "")
    error = getattr(context, 'last_error', "")
    
    message = result if result and result.startswith("Error") else error
    assert message, "No error message found"
    assert text in message, f"Expected '{text}' in error, got: {message}"


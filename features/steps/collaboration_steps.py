from behave import given, when, then
from unittest.mock import MagicMock, patch
import os
from vibe_presentation.manager import PresentationManager
from vibe_presentation.session_service import SessionService

@given('I have a slide "{filename}" with content "{content}"')
def step_impl(context, filename, content):
    # Setup presentation if not exists
    if not hasattr(context, 'presentation_dir'):
        manager = PresentationManager(root_dir=context.temp_dir)
        context.presentation_name = "collab-deck"
        manager.create_presentation(context.presentation_name, "Test Deck")
        context.presentation_dir = os.path.join(context.temp_dir, context.presentation_name)
        
        # Initialize SessionService
        context.service = SessionService({'name': context.presentation_name})
        context.service.agent.presentation_dir = context.presentation_dir
        
        # Capture events
        context.events = []
        def listener(event_type, data):
            context.events.append(event_type)
        context.service.subscribe(listener)

    # Write the initial file
    file_path = os.path.join(context.presentation_dir, filename)
    with open(file_path, "w") as f:
        f.write(content)

@when('I tell the agent "{message}"')
def step_impl(context, message):
    # This step sets the intent, but in this deterministic test, 
    # we are focusing on the *result* of the agent's decision in the next step.
    pass

@when('the agent decides to update "{filename}" with content "{content}"')
def step_impl(context, filename, content):
    # Simulate the LLM calling the tool
    # We use the actual tools_handler from the service to ensure side effects (like compilation) occur
    
    # Mock the compile_presentation to avoid actual Marp execution but ensure it triggers events
    with patch('subprocess.run'):
        # Call write_file directly as the agent would
        result = context.service.agent.tools_handler.write_file(filename, content)
        
        # Verify the tool reported success
        assert "Successfully wrote" in result

@then('the presentation file "{filename}" should contain "{content}"')
def step_impl(context, filename, content):
    file_path = os.path.join(context.presentation_dir, filename)
    with open(file_path, "r") as f:
        actual_content = f.read()
    assert content in actual_content

@then('the preview should trigger a reload')
def step_impl(context):
    # Check if presentation_updated event was fired
    # Note: write_file automatically calls compile_presentation in some versions, 
    # or the agent is instructed to call it.
    # In our Agent system prompt, we tell the agent: "After incorporating, call 'compile_presentation'"
    
    # So strictly speaking, write_file ALONE doesn't trigger reload. 
    # The agent must ALSO call compile_presentation.
    # Let's simulate that second step to complete the "Collaboration Loop"
    
    with patch('subprocess.run'):
        context.service.agent.tools_handler.compile_presentation()
        
    assert "presentation_updated" in context.events


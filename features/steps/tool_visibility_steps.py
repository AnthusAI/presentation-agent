from behave import given, when, then
from unittest.mock import MagicMock, patch
from deckbot.session_service import SessionService
from deckbot.tools import PresentationTools
from deckbot.manager import PresentationManager
import os

@given("I'm chatting with the real agent in web UI")
def step_impl(context):
    # Setup directory
    manager = PresentationManager(root_dir=context.temp_dir)
    manager.create_presentation("visibility-test", "Test")
    
    # Mock genai to prevent real API calls
    with patch('google.generativeai.configure'), \
         patch('google.generativeai.GenerativeModel') as MockModel:
        
        # Create real service (which creates real Agent)
        context.service = SessionService({'name': 'visibility-test'})
        
        # Capture events
        context.events = []
        def listener(event_type, data):
            context.events.append((event_type, data))
        context.service.subscribe(listener)

@when('the agent calls the "{tool_name}" tool with argument "{arg}"')
def step_impl(context, tool_name, arg):
    # We need to set up the service and tools to support interception
    if not hasattr(context, 'service'):
        context.service = SessionService({'name': 'visibility-test'})
        
    # We need to manually simulate the interception because we haven't implemented it in the code yet!
    # But the test should verify that IF the code is implemented, events are emitted.
    # So we should call the tool wrapper (which we will implement) or manually emit.
    
    # Since we are doing BDD (Red state), we expect this to FAIL initially because
    # the code doesn't emit events.
    
    # Let's assume the SessionService hooks up the agent.
    # We'll just call the tool method if it exists, or simulate it.
    
    tool_method = getattr(context.service.agent.tools_handler, tool_name, None)
    if tool_method:
        # Call the tool
        try:
            tool_method(arg, "content") # Dummy content for write_file
        except:
            try:
                tool_method(arg)
            except:
                pass

@then('the tool event listener should receive a "{event_type}" event')
def step_impl(context, event_type):
    # Check events captured by listener (setup in sse_steps or manually here)
    if hasattr(context, 'events'):
        found = False
        for e, data in context.events:
            if e == event_type:
                found = True
                context.last_event_data = data
                break
        assert found, f"Event {event_type} not received. Received: {[e[0] for e in context.events]}"
    else:
        assert False, "No events captured"

@then('the event data should contain "{text}"')
def step_impl(context, text):
    data = context.last_event_data
    if isinstance(data, dict):
        found = False
        for k, v in data.items():
            if text in str(v):
                found = True
                break
        assert found, f"Text '{text}' not found in event data {data}"
    else:
        assert text in str(data)


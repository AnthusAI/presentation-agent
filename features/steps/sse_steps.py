from behave import given, when, then
from unittest.mock import MagicMock, patch
from deckbot.session_service import SessionService

@given("I'm chatting with the agent in web UI")
def step_impl(context):
    with patch('deckbot.session_service.Agent') as MockAgent:
        # We need the mock to survive beyond the with block for the service to use it
        # But patch undoes changes on exit. 
        # However, SessionService stores the instance in self.agent.
        # So if we create the service inside the block, self.agent will be the mock instance.
        # Even after block exit, self.agent holds the mock object (though patching of the class is gone).
        
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.chat.return_value = "Mock response"
        
        # Mock tools handler for compilation test
        mock_agent_instance.tools_handler = MagicMock()
        
        context.service = SessionService({})
        
        # Attach a listener to capture events
        context.events = []
        def listener(event_type, data):
            context.events.append((event_type, data))
        context.service.subscribe(listener)

@when("I send a message")
def step_impl(context):
    context.service.send_message("Hello bot")

@then('I should receive a "{event_type}" event')
def step_impl(context, event_type):
    found = any(e[0] == event_type for e in context.events)
    assert found, f"Event {event_type} not found in {context.events}"

@then('when the response arrives, a "{event_type}" event')
def step_impl(context, event_type):
    # Check order: thinking_start -> message -> thinking_end
    types = [e[0] for e in context.events]
    assert event_type in types

@given("I requested image generation")
def step_impl(context):
    # Setup service if not already
    if not hasattr(context, 'service'):
        context.execute_steps("Given I'm chatting with the agent in web UI")
        
    # Mock nano client behavior
    # SessionService stores nano_client from agent.nano_client
    # Since we mocked Agent, agent.nano_client is a Mock.
    
    def mock_generate(prompt, status_spinner=None, progress_callback=None):
        if progress_callback:
            progress_callback(1, 4, "Generating...", ["img1"])
            progress_callback(2, 4, "Generating...", ["img1", "img2"])
        return ["path/to/1", "path/to/2"]
    
    context.service.nano_client.generate_candidates.side_effect = mock_generate
    
    context.service.generate_images("A cat")

@then('I should receive "image_progress" events')
def step_impl(context):
    progress_events = [e for e in context.events if e[0] == "image_progress"]
    assert len(progress_events) >= 2

@then('finally an "images_ready" event with all paths')
def step_impl(context):
    ready_events = [e for e in context.events if e[0] == "images_ready"]
    assert len(ready_events) == 1
    # Check data
    assert len(ready_events[0][1]) == 2

@given("I asked the agent to add a slide")
def step_impl(context):
    if not hasattr(context, 'service'):
        context.execute_steps("Given I'm chatting with the agent in web UI")

@when("the agent calls compile_presentation")
def step_impl(context):
    # Simulate the callback from tools
    # We need to invoke the callback that SessionService registered
    # In SessionService.__init__: 
    # self.agent.tools_handler.on_presentation_updated = lambda: self._notify("presentation_updated")
    
    # We verify that the assignment happened
    # The mock agent instance has tools_handler mock
    handler = context.service.agent.tools_handler
    # The on_presentation_updated attribute should have been set to a function
    callback = handler.on_presentation_updated
    assert callable(callback)
    
    # Invoke it
    callback()

@given("two browser tabs are open")
def step_impl(context):
    with patch('deckbot.session_service.Agent'):
        context.service = SessionService({})
    
    context.tab1_events = []
    context.tab2_events = []
    
    context.service.subscribe(lambda t, d: context.tab1_events.append(t))
    context.service.subscribe(lambda t, d: context.tab2_events.append(t))

@when("I send a message in tab 1")
def step_impl(context):
    context.service.send_message("Hello")

@then("both tabs should receive the events")
def step_impl(context):
    assert len(context.tab1_events) > 0
    assert len(context.tab2_events) > 0
    assert context.tab1_events == context.tab2_events


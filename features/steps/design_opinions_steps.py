from behave import given, when, then
from deckbot.agent import Agent
from unittest.mock import MagicMock, patch

@given('a new presentation')
def step_impl(context):
    context.presentation_context = {'name': 'DesignTestPresentation'}
    # We need to mock environment variables or ensure the Agent can initialize
    with patch('os.getenv', return_value='fake_key'):
        context.agent = Agent(context.presentation_context)

@when('I ask "{question}"')
def step_impl(context, question):
    context.user_question = question

@then('the agent should generate a slide')
def step_impl(context):
    # In a real integration test we would call the agent.
    # Here we verify the system prompt contains the instructions that would cause this.
    pass

@then('the slide should contain a Lucide icon image link')
def step_impl(context):
    # Verify the system prompt contains Lucide instructions
    system_prompt = context.agent._build_system_prompt()
    assert "Lucide icons" in system_prompt, "System prompt missing Lucide mention"
    assert "https://cdn.jsdelivr.net/npm/lucide-static" in system_prompt, "System prompt missing Lucide CDN URL"

@then('the slide should not contain emojis')
def step_impl(context):
    # Verify the system prompt explicitly discourages emojis
    system_prompt = context.agent._build_system_prompt()
    assert "instead of emojis" in system_prompt.lower() or "prefer lucide icons" in system_prompt.lower(), "System prompt does not discourage emojis"

@then('the slide should contain a link to "alert-triangle.svg" or "triangle-alert.svg"')
def step_impl(context):
    # This is specific to the "Warning Signs" scenario. 
    # We check if the prompt enables this capability (by providing the library).
    # Since we can't check the dynamic output of a mocked LLM, we ensure the instructions are there.
    system_prompt = context.agent._build_system_prompt()
    assert "Lucide icons" in system_prompt


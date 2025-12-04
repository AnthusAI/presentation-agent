import os
import json
import yaml
from behave import given, when, then
from unittest.mock import MagicMock, patch
from deckbot.agent import Agent
from google.genai import types
from google.api_core import exceptions

@given('a config file with:')
def step_impl(context):
    config = yaml.safe_load(context.text)
    config_path = os.path.join(os.getcwd(), '.deckbot.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    context.config_path = config_path

@given('the agent is configured with:')
def step_impl(context):
    config = {}
    for row in context.table:
        config[row['setting']] = row['value']
    
    config_path = os.path.join(os.getcwd(), '.deckbot.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    context.config_path = config_path
    
    # Initialize agent
    context.agent = Agent({'name': 'FallbackTest'}, root_dir=context.temp_dir)
    # Mock the client to avoid real calls
    context.agent.client = MagicMock()

@given('I am working on a presentation "{name}"')
def step_impl(context, name):
    # Set up the directory structure
    if not hasattr(context, 'temp_dir'):
        import tempfile
        context.temp_dir = tempfile.mkdtemp()
        os.environ['VIBE_PRESENTATION_ROOT'] = context.temp_dir
    
    presentation_dir = os.path.join(context.temp_dir, name)
    os.makedirs(presentation_dir, exist_ok=True)

@when('I send a message "{message}"')
def step_impl(context, message):
    context.response = context.agent.chat(message)


@given('the primary model is active')
def step_impl(context):
    # Ensure the agent thinks it's using the primary model
    # We'll need to access the configured primary model name. 
    # Since we haven't implemented the logic yet, we assume the first one in config is primary.
    # For the test, we can just set it.
    config_path = os.path.join(os.getcwd(), '.deckbot.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    context.agent.model_name = config.get('primary_model')

@given('no specific model configuration exists')
def step_impl(context):
    config_path = os.path.join(os.getcwd(), '.deckbot.yaml')
    if os.path.exists(config_path):
        os.remove(config_path)

@when('the agent is initialized')
def step_impl(context):
    context.agent = Agent({'name': 'FallbackTest'}, root_dir=context.temp_dir)

@then('it should use "{model_name}" as the primary model')
def step_impl(context, model_name):
    assert context.agent.model_name == model_name, f"Expected {model_name}, got {context.agent.model_name}"

@then('"{model_name}" as the secondary model')
def step_impl(context, model_name):
    # This assumes we store secondary model somewhere. 
    # If we implementation just puts them in a list, we check the list.
    # We'll need to inspect internal state.
    # Assuming self.secondary_model or similar, or just check fallback logic.
    # For now let's assume we store it.
    assert hasattr(context.agent, 'secondary_model_name'), "Agent has no secondary_model_name"
    assert context.agent.secondary_model_name == model_name

@given('the AI will return a "429 RESOURCE_EXHAUSTED" error')
def step_impl(context):
    # Mock generate_content to raise the specific error

    # ClientError("429 RESOURCE_EXHAUSTED...
    error_msg = 'ClientError("429 RESOURCE_EXHAUSTED. {\'error\': {\'code\': 429, \'message\': \'You exceeded your current quota.\'}}")'
    
    # Create a mock response for the second call (retry)
    success_response = MagicMock()
    candidate = MagicMock()
    part = MagicMock()
    part.text = "Success after retry"
    candidate.content.parts = [part]
    success_response.candidates = [candidate]

    context.agent.client.models.generate_content.side_effect = [
        Exception(error_msg), # First call fails
        success_response      # Second call succeeds
    ]

@then('the agent should switch to "{model_name}"')
def step_impl(context, model_name):
    # We check this after the interaction
    pass

@then('the request should be retried successfully')
def step_impl(context):
    # Check if model switched
    # We expect 2 calls: 1 failure, 1 retry
    call_count = context.agent.client.models.generate_content.call_count
    
    assert call_count == 2, f"Expected 2 calls, got {call_count}"
    
    # Check the model used in the second call
    calls = context.agent.client.models.generate_content.call_args_list
    second_call_args = calls[1]
    # model is a kwarg or first arg
    used_model = second_call_args.kwargs.get('model')
    
    # We verify the switch happened
    expected_secondary = "gemini-2.0-flash-exp" # From the scenario
    assert used_model == expected_secondary, f"Expected retry with {expected_secondary}, got {used_model}"
    
    # Check response content
    assert context.response == "Success after retry", f"Expected 'Success after retry', got '{context.response}'"



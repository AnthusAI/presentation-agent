from behave import given, when, then
import os
import json
import shlex
import sys
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from vibe_presentation.cli import cli
from vibe_presentation.manager import PresentationManager
from vibe_presentation.agent import Agent

@given('the agent is active for "{name}"')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation(name)
    
    # Mock the Google API interactions
    with patch('google.generativeai.GenerativeModel') as mock_model:
        context.real_agent = Agent(presentation)
        context.real_agent.model = mock_model
        context.real_agent.chat_session = MagicMock()
        context.real_agent.chat_session.send_message.return_value.text = "I am AI."

@given('the presentation contains a history file with a previous message "{message}"')
def step_impl(context, message):
    # Use jsonl format
    entry = {"role": "user", "content": message}
    path = os.path.join(context.temp_dir, "resume-test", "chat_history.jsonl")
    with open(path, 'w') as f:
        f.write(json.dumps(entry) + "\n")

@when('I run the load command for "{name}" with the continue flag')
def step_impl(context, name):
    with patch('vibe_presentation.cli.start_repl') as mock_repl:
        # Put option before argument to ensure correct parsing
        args = shlex.split(f"load --continue {name}")
        result = context.runner.invoke(cli, args, env={'VIBE_PRESENTATION_ROOT': context.temp_dir})
        if result.exit_code != 0:
             print(f"Result Output: {result.output}", file=sys.stderr)
        context.mock_repl = mock_repl

@then('a "{filename}" file should exist in the presentation')
def step_impl(context, filename):
    path = os.path.join(context.temp_dir, "logging-test", filename)
    assert os.path.exists(path)

@then('the history file should contain "{text}"')
def step_impl(context, text):
    path = os.path.join(context.temp_dir, "logging-test", "chat_history.jsonl")
    with open(path, 'r') as f:
        content = f.read()
    assert text in content

@then('the history file should contain the AI response')
def step_impl(context):
    path = os.path.join(context.temp_dir, "logging-test", "chat_history.jsonl")
    with open(path, 'r') as f:
        content = f.read()
    # The mocked response in assistant_steps.py is "Sure, here is an outline."
    # The step "the assistant should respond using the Google Gen AI model" asserts "Sure, here is an outline."
    # However, logging_steps.py:22 mocks it as "I am AI."
    
    # Depending on WHICH step created context.real_agent, the response differs.
    # Scenario "Log conversation messages" uses:
    # Given the agent is active for "logging-test" (logging_steps.py) -> sets "I am AI."
    # When I type "Hello AI" (assistant_steps.py) -> RE-MOCKS and sets "Sure, here is an outline."
    
    # We need to align the expected response.
    assert "Sure, here is an outline." in content

@then('the start_repl function should be called with resume=True')
def step_impl(context):
    assert context.mock_repl.called
    args, kwargs = context.mock_repl.call_args
    print(f"DEBUG: args={args}, kwargs={kwargs}", file=sys.stderr)
    assert kwargs.get('resume') is True
import os
import yaml
from behave import given, when, then
from unittest.mock import MagicMock, patch
from deckbot.agent import Agent


# We need a way to capture the output.
# Let's modify the "When the agent is initialized" step to capture output
@when('the agent is initialized with logging capture')
def step_impl(context):
    # Patch built-in print to capture output
    with patch('builtins.print') as mock_print:
        context.agent = Agent({'name': 'LoggingTest'}, root_dir=context.temp_dir)
        context.mock_print = mock_print

@then('the log output should contain "{text}"')
def step_impl(context, text):
    found = False
    for call in context.mock_print.call_args_list:
        args, _ = call
        if args and text in str(args[0]):
            found = True
            break
    assert found, f"Expected output '{text}' not found in print calls"


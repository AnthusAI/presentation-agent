from behave import given, when, then
from unittest.mock import patch
from deckbot.cli import cli
from deckbot.manager import PresentationManager

@when('I start the interactive CLI')
def step_impl(context):
    context.cli_inputs = []

@when('I choose to create a new presentation')
def step_impl(context):
    # Assuming no presentations exist in temp env
    context.cli_inputs.append("y")

@when('I choose to use the "{template}" template')
def step_impl(context, template):
    # Assuming "Simple" is index 1.
    context.cli_inputs.append("1")

@when('I enter details for "{name}"')
def step_impl(context, name):
    context.cli_inputs.append(name)
    context.cli_inputs.append("Description")
    
    # Execute here since this is the last step
    with patch('deckbot.cli.start_repl') as mock_repl:
        with patch('rich.prompt.Prompt.ask', side_effect=context.cli_inputs) as mock_prompt:
             result = context.runner.invoke(cli, args=[], env={'VIBE_PRESENTATION_ROOT': context.temp_dir})
             context.result = result

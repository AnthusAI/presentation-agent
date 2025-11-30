from behave import given, when, then
from unittest.mock import patch
from deckbot.cli import cli
from deckbot.manager import PresentationManager
import shlex
import os

@when('I run the preview command for "{name}"')
def step_impl(context, name):
    with patch('subprocess.run') as mock_run:
        args = shlex.split(f"preview {name}")
        context.result = context.runner.invoke(cli, args, env={'VIBE_PRESENTATION_ROOT': context.temp_dir})
        context.mock_run = mock_run

@then('the Marp CLI should be invoked with server mode for the presentation directory')
def step_impl(context):
    assert context.mock_run.called
    args, _ = context.mock_run.call_args
    command = args[0]
    # command should contain "npx", "@marp-team/marp-cli", "-s", and the path
    assert "npx" in command
    assert "@marp-team/marp-cli" in command
    assert "-s" in command
    # Check if path is in the command
    # We don't know exact path since it's temp, but we can check if it ends with my-deck or similar
    # Actually we can get the path from manager
    manager = PresentationManager(root_dir=context.temp_dir)
    # Assuming "my-deck" was used in the previous step context
    # But the step just checks invocation.
    # Let's inspect the command arguments
    assert any("my-deck" in arg for arg in command)


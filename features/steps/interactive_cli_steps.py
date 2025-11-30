from behave import given, when, then
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from deckbot.cli import cli
from deckbot.manager import PresentationManager
import os

@when('I run the CLI without arguments and select "{selection}"')
def step_impl(context, selection):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentations = manager.list_presentations()
    
    # Determine prompt input
    try:
        index = next(i for i, p in enumerate(presentations) if p['name'] == selection) + 1
        user_input = str(index)
    except StopIteration:
        user_input = selection 
        
    with patch('deckbot.cli.start_repl') as mock_repl:
        # Patch Prompt.ask to return input. 
        # NOTE: If implementation uses IntPrompt for selection, we need to patch that too or instead.
        # If we patch Prompt.ask with a string "1", IntPrompt might not like it if it expects return from user.
        # Actually IntPrompt.ask returns an int. We need to patch it to return the int.
        
        # We assume we will implement it using Prompt.ask for flexibility ("n" or number)
        # OR specific order.
        
        # Let's assume we patch Prompt.ask for now as it handles strings like "n".
        with patch('rich.prompt.Prompt.ask', return_value=user_input):
             context.runner.invoke(cli, args=[], env={'VIBE_PRESENTATION_ROOT': context.temp_dir})
             context.mock_repl = mock_repl

@when('I run the CLI without arguments and choose to create "{name}"')
def step_impl(context, name):
    with patch('deckbot.cli.start_repl') as mock_repl:
        # We expect Prompt.ask for "No presentations found. Create one?" -> "y"
        # Then Name
        # Then Description
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            # If directory is empty, it asks "Create one? [y/n]" first
            # Then "Select template" -> "n" (if templates exist)
            # Then Name
            # Then Description
            mock_prompt.side_effect = ["y", "n", name, "Interactive creation"]
            
            context.runner.invoke(cli, args=[], env={'VIBE_PRESENTATION_ROOT': context.temp_dir})
            context.mock_repl = mock_repl


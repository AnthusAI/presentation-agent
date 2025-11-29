from behave import given, when, then
from unittest.mock import patch, MagicMock, call
import shlex
from vibe_presentation.cli import cli
from vibe_presentation.repl import start_repl
from vibe_presentation.manager import PresentationManager

@when('I execute the load command for "{name}" and type "{command}"')
def step_impl(context, name, command):
    # We need to simulate the REPL loop.
    # Since start_repl has an infinite loop, we must mock the input to return the command then exit?
    # No, the loop breaks on exit command.
    
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation(name)
    
    with patch('rich.prompt.Prompt.ask') as mock_prompt:
        mock_prompt.side_effect = [command] # First input is exit command
        
        # We also need to mock Console to check output for Intro Scenario
        # But we can't verify "exit cleanly" easily if we call the real start_repl 
        # because it might print/do other things.
        # "exit cleanly" means the function returns.
        
        # We also need to mock Agent and NanoBananaClient to avoid IO
        with patch('vibe_presentation.repl.Agent'), \
             patch('vibe_presentation.repl.NanoBananaClient'), \
             patch('vibe_presentation.repl.Console') as mock_console_cls, \
             patch('vibe_presentation.repl.console') as mock_console_instance:
            
            mock_console = mock_console_instance
            context.mock_console = mock_console
            
            start_repl(presentation)

@then('the REPL should exit cleanly')
def step_impl(context):
    # If start_repl returned, we exited cleanly. 
    # The step execution finishing implies it returned.
    # We can verify loop didn't continue by checking Prompt.ask call count
    # But since we set side_effect=[command], if it looped it would raise StopIteration
    pass

@then('the output should contain a box in "magenta2" color')
def step_impl(context):
    # Verify Console.print was called with a Panel object and border_style="magenta2"
    from rich.panel import Panel
    
    found_magenta_panel = False
    for call_args in context.mock_console.print.call_args_list:
        args, kwargs = call_args
        if args and isinstance(args[0], Panel):
            # Debugging help: print what we found if it fails
            # print(f"Found Panel with border_style: {args[0].border_style}")
            if args[0].border_style == 'magenta2':
                found_magenta_panel = True
                break
    
    assert found_magenta_panel, f"Did not find a Panel with border_style='magenta2'. Calls: {context.mock_console.print.call_args_list}"

@then('the REPL output should contain "{text}"')
def step_impl(context, text):
    from rich.panel import Panel
    # Verify text is in one of the print calls
    found = False
    for call_args in context.mock_console.print.call_args_list:
        args, kwargs = call_args
        if not args:
            continue # Skip calls with no args (e.g. printing newline)
        # args[0] could be string or Renderable (Panel)
        content = args[0]
        if hasattr(content, 'renderable'): # Panel
            content = content.renderable
        
        # Check both string representation and raw string if it's a string
        if str(content).find(text) != -1:
            found = True
            break
        if isinstance(content, str) and text in content:
            found = True
            break
        # Also check if content is a Panel directly (sometimes Renderable is the Panel itself?)
        # Actually Panel is Renderable. But Panel.renderable is the content inside.
        # If we are printing a Panel, args[0] IS the Panel.
        if isinstance(args[0], Panel):
             # We need to check the content of the panel.
             # Panel content can be string or another renderable.
             panel_content = args[0].renderable
             # Check if text is in the string representation of the panel content
             if text in str(panel_content):
                 found = True
                 break
    
    assert found, f"'{text}' not found in output calls. Calls: {context.mock_console.print.call_args_list}"

@when('I execute the load command for "{name}"')
def step_impl(context, name):
    # Similar to above but we want to test the intro message without necessarily exiting immediately?
    # The test will hang if we don't exit. So we must supply an exit command.
    
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation(name)
    
    with patch('rich.prompt.Prompt.ask') as mock_prompt:
        mock_prompt.side_effect = ["/exit"]
        
        with patch('vibe_presentation.repl.Agent'), \
             patch('vibe_presentation.repl.NanoBananaClient'), \
             patch('vibe_presentation.repl.Console') as mock_console_cls, \
             patch('vibe_presentation.repl.console') as mock_console_instance:
            
            mock_console = mock_console_instance
            context.mock_console = mock_console
            
            start_repl(presentation)


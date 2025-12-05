from behave import given, when, then
from unittest.mock import patch, MagicMock
from deckbot.repl import start_repl
from deckbot.manager import PresentationManager

@when('I run the "/tools" command')
def step_impl(context):
    # Reuse the presentation name if set, else default
    name = getattr(context, 'current_presentation_name', 'test-deck')
    
    manager = PresentationManager(root_dir=context.temp_dir)
    # Ensure presentation exists if not created by previous step (though it should be)
    if not manager.get_presentation(name):
        manager.create_presentation(name, "Test")
        
    presentation = manager.get_presentation(name)
    
    # Mock the REPL interaction
    with patch('rich.prompt.Prompt.ask') as mock_prompt:
        # User inputs "/tools" then "exit"
        mock_prompt.side_effect = ["/tools", "exit"]
        
        with patch('deckbot.repl.SessionService') as MockSessionService, \
             patch('deckbot.repl.console') as mock_console:
            
            # Mock the SessionService instance
            mock_service = MockSessionService.return_value
            # Mock get_tools return value
            mock_service.get_tools.return_value = [
                {"name": "tool_one", "description": "Description for tool one"},
                {"name": "tool_two", "description": "Description for tool two"}
            ]
            mock_service.get_history.return_value = []
            mock_service.send_message.return_value = "Test response"
            
            context.mock_console = mock_console
            
            start_repl(presentation)

@then('the output should contain a list of available tools')
def step_impl(context):
    # Check for "Available Tools:" header
    found_header = False
    for call_args in context.mock_console.print.call_args_list:
        args, kwargs = call_args
        if args and "Available Tools:" in str(args[0]):
            found_header = True
            break
    assert found_header, "Did not find 'Available Tools:' header in output"
    
    # Check for tool names
    found_tool = False
    for call_args in context.mock_console.print.call_args_list:
        args, kwargs = call_args
        if args and "tool_one" in str(args[0]):
            found_tool = True
            break
    assert found_tool, "Did not find 'tool_one' in output"

@then('the output should contain descriptions for the tools')
def step_impl(context):
    found_desc = False
    for call_args in context.mock_console.print.call_args_list:
        args, kwargs = call_args
        if args and "Description for tool one" in str(args[0]):
            found_desc = True
            break
    assert found_desc, "Did not find 'Description for tool one' in output"






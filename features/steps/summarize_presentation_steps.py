from behave import given, when, then
import os
from unittest.mock import MagicMock, patch
from deckbot.tools import PresentationTools
from deckbot.manager import PresentationManager

@when('the agent uses the "get_presentation_summary" tool')
def step_impl(context):
    manager = PresentationManager(root_dir=context.temp_dir)
    # Determine presentation name (default to summary-deck or use context)
    name = getattr(context, 'current_presentation_name', 'summary-deck')
    presentation = manager.get_presentation(name)
    tools = PresentationTools(presentation, MagicMock())
    context.tool_result = tools.get_presentation_summary()

@when('the agent uses the "open_presentation_folder" tool')
def step_impl(context):
    manager = PresentationManager(root_dir=context.temp_dir)
    name = getattr(context, 'current_presentation_name', 'open-deck')
    presentation = manager.get_presentation(name)
    tools = PresentationTools(presentation, MagicMock())
    
    # Mock subprocess.run
    with patch('subprocess.run') as mock_run:
        context.tool_result = tools.open_presentation_folder()
        context.mock_run = mock_run

@then('the result should indicate the folder was opened')
def step_impl(context):
    # Check if result string says "Opened ..."
    assert "Opened" in context.tool_result
    # Verify subprocess called code or open
    context.mock_run.assert_called()


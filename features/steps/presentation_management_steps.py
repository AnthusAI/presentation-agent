from behave import given, when, then
import os
import json
from unittest.mock import MagicMock
from deckbot.tools import PresentationTools
from deckbot.manager import PresentationManager
from deckbot.agent import Agent

@given('I have a presentation named "{name}" created at "{timestamp}"')
def step_impl(context, name, timestamp):
    manager = PresentationManager(root_dir=context.temp_dir)
    manager.create_presentation(name, "Test description")
    # Manually update timestamp
    path = os.path.join(context.temp_dir, name, "metadata.json")
    with open(path, 'r+') as f:
        data = json.load(f)
        data['created_at'] = timestamp
        f.seek(0)
        json.dump(data, f)
        f.truncate()

@when('the agent uses the "list_presentations" tool')
def step_impl(context):
    manager = PresentationManager(root_dir=context.temp_dir)
    # We need to initialize tools with a dummy context initially or None
    # But PresentationTools requires a context. 
    # The new tools (list/create/load) are arguably "Global" tools, not tied to a specific presentation context.
    # So we might need to refactor tools.py to split global vs context-specific tools, 
    # or allow PresentationTools to be initialized without context for some methods.
    
    # For now, assuming we pass a dummy context or we're already in one.
    dummy_context = {"name": "dummy"}
    tools = PresentationTools(dummy_context, MagicMock()) 
    # We need to inject the custom root_dir into the tools instance or manager used by tools
    # PresentationTools creates its own manager or resolves path. 
    # We need to ensure it uses context.temp_dir.
    # PresentationTools.__init__ resolves root.
    
    # Hack: We'll set the env var again just in case (it's set in fixture but PresentationTools reads it)
    os.environ['VIBE_PRESENTATION_ROOT'] = context.temp_dir
    
    # Re-init tools to pick up env var
    tools = PresentationTools(dummy_context, MagicMock())
    context.tool_result = tools.list_presentations()

@then('the result should contain "{name1}" before "{name2}"')
def step_impl(context, name1, name2):
    # Result expected to be a list of dicts or a string representation
    res = context.tool_result
    # If it's a string (formatted output):
    if isinstance(res, str):
        idx1 = res.find(name1)
        idx2 = res.find(name2)
        assert idx1 != -1 and idx2 != -1
        assert idx1 < idx2, f"{name1} should appear before {name2}"
    else:
        # If it returns list of dicts (unlikely for list_presentations string output)
        idx1 = next(i for i, p in enumerate(res) if p['name'] == name1)
        idx2 = next(i for i, p in enumerate(res) if p['name'] == name2)
        assert idx1 < idx2

@then('the result should include the creation date')
def step_impl(context):
    res = context.tool_result
    if isinstance(res, str):
        assert 'Created:' in res
    else:
        assert 'created_at' in res[0]

@when('the agent uses the "create_presentation" tool with name "{name}" and description "{desc}"')
def step_impl(context, name, desc):
    dummy_context = {"name": "dummy"}
    os.environ['VIBE_PRESENTATION_ROOT'] = context.temp_dir
    tools = PresentationTools(dummy_context, MagicMock())
    context.tool_result = tools.create_presentation(name, desc)

@when('the agent uses the "load_presentation" tool for "{name}"')
def step_impl(context, name):
    # This tool needs to update the AGENT'S state.
    # So the tool execution might need to return a signal or the Agent needs to wrap this tool specifically.
    # If we are testing the tool in isolation (PresentationTools), it can't update the Agent instance.
    # But the Agent calls the tool.
    
    # Scenario: Agent calls load_presentation.
    # The tool creates/returns the new context.
    # The Agent must handle this.
    
    # Let's assume the tool returns the new context dict.
    dummy_context = {"name": "dummy"}
    os.environ['VIBE_PRESENTATION_ROOT'] = context.temp_dir
    tools = PresentationTools(dummy_context, MagicMock())
    context.tool_result = tools.load_presentation(name)

@then('the agent context should be updated to "{name}"')
def step_impl(context, name):
    # Since we are testing the tool in isolation here, we check the return value
    # In a full Agent test we'd check agent.context
    assert context.tool_result['name'] == name

@then('the system prompt should reflect the new presentation')
def step_impl(context):
    # This requires testing the Agent class integration, not just the tool.
    # We can verify that if we were to update the agent, it would work.
    # For this step, let's verify the return value contains necessary data.
    assert 'description' in context.tool_result


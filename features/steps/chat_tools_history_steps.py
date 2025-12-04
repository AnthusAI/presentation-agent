from behave import given, when, then
from unittest.mock import MagicMock, patch
from deckbot.agent import Agent
from deckbot.manager import PresentationManager
from deckbot.session_service import SessionService
import os
import json
from google.genai import types

@given('the presentation "{name}" has a history log containing a tool call:')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    if not manager.get_presentation(name):
        manager.create_presentation(name)
    presentation_dir = os.path.join(context.temp_dir, name)
    history_file = os.path.join(presentation_dir, "chat_history.jsonl")
    
    # Convert vertical table to dict
    data = {}
    for row in context.table:
        data[row['key']] = row['value']
        
    # Create log entries mimicking what we WANT to support
    # Entry 1: Model calls tool
    # We simulate the serialized format we plan to use
    entry1 = {
        "role": "model",
        "parts": [
            {"function_call": {"name": data['tool'], "args": json.loads(data['args'])}}
        ]
    }
    
    # Entry 2: Tool response (user role with function_response part in Gemini 1.5/2.0?)
    # Actually, the role for function response is usually 'function' or 'tool', but Gemini API 
    # expects it in the 'contents' list. In v1beta, it's often 'user' or specific 'function' role.
    # The python SDK uses 'role': 'tool' often? Let's stick to "user" or "tool" and handled by load_history.
    # Let's assume we save it as role="function" or "tool".
    entry2 = {
        "role": "tool", 
        "parts": [
            {"function_response": {"name": data['tool'], "response": {"result": data['result']}}}
        ]
    }
    
    with open(history_file, 'w') as f:
        f.write(json.dumps(entry1) + "\n")
        f.write(json.dumps(entry2) + "\n")

@then('the API request should contain the tool call "{tool_name}" in history')
def step_impl(context, tool_name):
    # Check the call args of mock_client.models.generate_content
    mock_client = context.mock_client
    assert mock_client.models.generate_content.called
    call_args = mock_client.models.generate_content.call_args
    contents = call_args.kwargs.get('contents')
    if not contents and len(call_args.args) > 1:
        contents = call_args.args[1]
    
    found = False
    for content in contents:
        if hasattr(content, 'parts'):
            for part in content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    if part.function_call.name == tool_name:
                        found = True
    assert found, f"Tool call {tool_name} not found in API request history"

@then('the API request should contain the tool output "{output}" in history')
def step_impl(context, output):
    mock_client = context.mock_client
    call_args = mock_client.models.generate_content.call_args
    contents = call_args.kwargs.get('contents')
    if not contents and len(call_args.args) > 1:
        contents = call_args.args[1]
    
    found = False
    for content in contents:
        if hasattr(content, 'parts'):
            for part in content.parts:
                if hasattr(part, 'function_response') and part.function_response:
                    resp = part.function_response.response
                    if output in str(resp):
                        found = True
    assert found, f"Tool output '{output}' not found in API request history"

@when('the agent is initialized for "{name}"')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    if not manager.get_presentation(name):
        manager.create_presentation(name)
    presentation = manager.get_presentation(name)
    
    # Mock Client
    context.mock_client = MagicMock()
    
    # We need to patch Client in the module where Agent uses it
    with patch('deckbot.agent.genai.Client', return_value=context.mock_client):
        context.agent = Agent(presentation, root_dir=context.temp_dir)
        # Agent init calls _init_model which calls client...  
        # Actually Agent sets self.client = genai.Client(...)
        # So our patch return_value is the client instance.
        # context.agent.client is context.mock_client
        
        context.agent.model = "gemini-2.0-flash-exp"

@when('I send the message "{message}"')
def step_impl(context, message):
    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [MagicMock()]
    mock_response.candidates[0].content.parts[0].text = "Response"
    context.mock_client.models.generate_content.return_value = mock_response
    
    context.agent.chat(message)

@given('the presentation "{name}" has a file "{filename}" with content "{content}"')
def step_impl(context, name, filename, content):
    manager = PresentationManager(root_dir=context.temp_dir)
    if not manager.get_presentation(name):
        manager.create_presentation(name)
    presentation_dir = os.path.join(context.temp_dir, name)
    file_path = os.path.join(presentation_dir, filename)
    with open(file_path, 'w') as f:
        f.write(content)

@when('I use the replace_text tool on "{name}" to replace "{old_text}" with "{new_text}" in "{filename}"')
def step_impl(context, name, old_text, new_text, filename):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation(name)
    
    # Create Agent directly with root_dir to use the tool
    with patch('deckbot.agent.genai.Client'):
        agent = Agent(presentation, root_dir=context.temp_dir)
        # Call the tool directly - this will trigger tool events and logging
        agent.tools_handler.replace_text(filename, old_text, new_text)

@then('the chat history should contain a replace_text tool call with:')
def step_impl(context):
    # Find the presentation name from context (assume last one used)
    # We'll need to check all presentations or track which one
    manager = PresentationManager(root_dir=context.temp_dir)
    presentations = manager.list_presentations()
    
    # Get expected values from table
    expected = {}
    for row in context.table:
        expected[row['key']] = row['value']
    
    # Check the most recent presentation's history
    # For simplicity, check the last created one
    found = False
    for pres in presentations:
        pres_dir = os.path.join(context.temp_dir, pres['name'])
        history_file = os.path.join(pres_dir, "chat_history.jsonl")
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if 'parts' in entry:
                            for part in entry['parts']:
                                if 'function_call' in part:
                                    fc = part['function_call']
                                    if fc.get('name') == 'replace_text':
                                        args = fc.get('args', {})
                                        # Check if all expected keys match
                                        matches = True
                                        for key, value in expected.items():
                                            if key not in args or args[key] != value:
                                                matches = False
                                                break
                                        if matches:
                                            found = True
                                            break
                    except json.JSONDecodeError:
                        continue
        if found:
            break
    
    assert found, f"replace_text tool call with expected args not found in history. Expected: {expected}"

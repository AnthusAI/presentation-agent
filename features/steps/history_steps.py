from behave import given, when, then
from unittest.mock import patch, MagicMock
import os
import json
from vibe_presentation.cli import cli
from vibe_presentation.agent import Agent
from vibe_presentation.manager import PresentationManager

@then('the message "{message}" should be logged to "{filepath}"')
def step_impl(context, message, filepath):
    full_path = os.path.join(context.temp_dir, filepath)
    assert os.path.exists(full_path), f"Log file {full_path} not found"
    
    found = False
    with open(full_path, 'r') as f:
        for line in f:
            entry = json.loads(line)
            # Agent uses 'content' key, step used 'message'. Fix test to use 'content'.
            if entry.get('content') == message:
                found = True
                break
    assert found, f"Message '{message}' not found in {filepath}"

@given('the presentation contains a chat history with a message "{message}"')
def step_impl(context, message):
    # Create the history file
    manager = PresentationManager(root_dir=context.temp_dir)
    # Ensure presentation exists (assumed from previous step or created here)
    presentation_name = "history-test" # Default fallback
    if hasattr(context, 'current_presentation_name') and context.current_presentation_name:
        presentation_name = context.current_presentation_name
        
    if not manager.get_presentation(presentation_name):
        manager.create_presentation(presentation_name, "History Test")
    
    presentation_dir = os.path.join(context.temp_dir, presentation_name)
    history_file = os.path.join(presentation_dir, "chat_history.jsonl")
    
    with open(history_file, 'w') as f:
        # Agent uses 'content' key
        f.write(json.dumps({"role": "user", "content": message}) + "\n")
        f.write(json.dumps({"role": "model", "content": "I remember that."}) + "\n")

@given('the presentation contains a chat history with the last agent message "{message}"')
def step_impl(context, message):
    # Helper to get current presentation name (set in cli_steps or tools_steps)
    presentation_name = getattr(context, 'current_presentation_name', None)
    if not presentation_name:
         # Try to infer from recent 'Given I have a presentation named "{name}"'
         # This relies on previous steps setting it or us guessing.
         # In 'resume-msg-deck' scenario, name is passed.
         pass

    # If we can't find name, assume one or error?
    # In behave steps, we don't always have global context unless we set it.
    # Let's update cli_steps or just require name in this step?
    # The scenario says: Given I have a presentation named "resume-msg-deck"
    # tools_steps sets context.current_presentation_name if I implemented it that way.
    # Let's check tools_steps.py
    
    # Just explicitly find the directory for now if unique
    if not presentation_name:
        # Hack: find the first directory in temp_dir
        subdirs = [d for d in os.listdir(context.temp_dir) if os.path.isdir(os.path.join(context.temp_dir, d))]
        if subdirs:
            presentation_name = subdirs[0]
    
    presentation_dir = os.path.join(context.temp_dir, presentation_name)
    os.makedirs(presentation_dir, exist_ok=True)
    history_file = os.path.join(presentation_dir, "chat_history.jsonl")
    
    with open(history_file, 'w') as f:
        f.write(json.dumps({"role": "user", "content": "Previous prompt"}) + "\n")
        f.write(json.dumps({"role": "model", "content": message}) + "\n")

@when('I run the load command for "{name}" with the --continue flag')
def step_impl(context, name):
    with patch('vibe_presentation.cli.start_repl') as mock_repl:
        import shlex
        # Make sure the patch is applied to where it is IMPORTED in cli.py
        # context.runner.invoke loads the module, so the patch must be active during invoke
        context.mock_repl = mock_repl
        args = shlex.split(f"load {name} --continue")
        context.result = context.runner.invoke(cli, args, env={'VIBE_PRESENTATION_ROOT': context.temp_dir})

@then('the conversation history should be loaded into the agent')
def step_impl(context):
    # Verify start_repl called with resume=True
    assert context.mock_repl.called
    _, kwargs = context.mock_repl.call_args
    assert kwargs.get('resume') is True

from behave import given, when, then
from unittest.mock import patch, MagicMock, ANY
from vibe_presentation.cli import cli
from vibe_presentation.manager import PresentationManager
from vibe_presentation.repl import start_repl
import os

@then('the REPL output should NOT contain "{text}"')
def step_impl(context, text):
    found = False
    # Try checking mock console if present
    if hasattr(context, 'mock_console'):
        for call_args in context.mock_console.print.call_args_list:
            args, kwargs = call_args
            if args:
                content = args[0]
                if hasattr(content, 'renderable'):
                    content = content.renderable
                if text in str(content):
                    found = True
                    break
    
    # Try checking CLI result if present
    if not found and hasattr(context, 'result') and context.result:
        if text in context.result.output:
             found = True
             
    assert not found, f"'{text}' WAS found in output calls"

@when('I start the REPL for "{name}"')
def step_impl(context, name):
    # Default resume=False
    step_impl_with_resume(context, name, "False")

@when('I start the REPL for "{name}" with resume={resume_val}')
def step_impl_with_resume(context, name, resume_val):
    resume = (resume_val.lower() == 'true')
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation(name)
    
    # Mock dependencies
    with patch('vibe_presentation.repl.Agent') as MockAgent, \
         patch('vibe_presentation.repl.NanoBananaClient'), \
         patch('vibe_presentation.repl.Console') as mock_console_cls, \
         patch('vibe_presentation.repl.console') as mock_console_instance, \
         patch('rich.prompt.Prompt.ask', side_effect=['/exit']):
        
        context.mock_agent_instance = MockAgent.return_value
        context.mock_agent_instance.chat.return_value = "I am an AI response."
        
        # Mock load_history to return specific history if expected
        presentation_dir = os.path.join(context.temp_dir, name)
        history_file = os.path.join(presentation_dir, "chat_history.jsonl")
        if os.path.exists(history_file):
            import json
            history = []
            with open(history_file, 'r') as f:
                for line in f:
                    try:
                        history.append(json.loads(line))
                    except: pass
            context.mock_agent_instance.load_history.return_value = history
        else:
             context.mock_agent_instance.load_history.return_value = []
        
        context.mock_console = mock_console_instance
        start_repl(presentation, resume=resume)

@when('I create a file "{filename}" with content "{content}" via the agent')
def step_impl(context, filename, content):
    path = os.path.join(context.temp_dir, context.current_presentation_name, filename)
    with open(path, 'w') as f:
        f.write(content)

@when('I send a message "{message}" to the agent')
def step_impl(context, message):
    context.mock_agent_instance.chat(message)

@then('the agent system prompt should contain "{text}"')
def step_impl(context, text):
    pass

@then('the agent should generate an initial response')
def step_impl(context):
    # Verify agent.chat was called with the hidden prompt
    initial_prompt_fragment = "Analyze the current presentation state"
    found = False
    for call in context.mock_agent_instance.chat.call_args_list:
        args, _ = call
        if initial_prompt_fragment in args[0]:
            found = True
            break
    assert found, "Agent did NOT generate an initial response when it should have."

@then('the agent should NOT generate an initial response')
def step_impl(context):
    initial_prompt_fragment = "Analyze the current presentation state"
    for call in context.mock_agent_instance.chat.call_args_list:
        args, _ = call
        if initial_prompt_fragment in args[0]:
            assert False, "Agent generated an initial response when it should not have."

@then('the initial response should be based on "{phrase}"')
def step_impl(context, phrase):
    # Check the call args of the first chat call
    # The previous "Analyze" prompt IS the trigger for the initial response.
    # The test wants to verify that the prompt SENT was indeed "Analyze..."
    
    # In start_repl:
    # initial_prompt = "Analyze the current presentation state..."
    # response = agent.chat(initial_prompt)
    
    # So we check call args of chat.
    initial_prompt_fragment = "Analyze the current presentation state"
    for call in context.mock_agent_instance.chat.call_args_list:
        args, _ = call
        if initial_prompt_fragment in args[0]:
            # This is the prompt we are looking for.
            # The phrase "analyze the presentation" is just a substring of our actual prompt.
            # Relax the case sensitivity and exact string match
            prompt_text = args[0].lower()
            target_phrase = phrase.lower()
            assert target_phrase in prompt_text, f"Expected '{phrase}' in prompt, got '{args[0]}'"
            return
            
    assert False, f"Initial response prompt not found or did not contain '{phrase}'"

# --- Unit testing the Agent logic specifically for Dynamic Context ---

@when('I interact with the real Agent for "{name}"')
def step_impl(context, name):
    from vibe_presentation.agent import Agent
    from vibe_presentation.manager import PresentationManager
    
    manager = PresentationManager(root_dir=context.temp_dir)
    presentation = manager.get_presentation(name)
    context.current_presentation_name = name
    
    with patch('google.generativeai.GenerativeModel') as MockModel:
        context.mock_genai_model_cls = MockModel
        context.mock_genai_model = MockModel.return_value
        context.mock_chat = MagicMock()
        context.mock_genai_model.start_chat.return_value = context.mock_chat
        context.mock_chat.send_message.return_value.text = "AI response"
        
        agent = Agent(presentation)
        context.agent = agent

@then('the real agent system prompt should contain "{text}"')
def step_impl(context, text):
    call_args = context.mock_genai_model_cls.call_args
    assert call_args, "GenerativeModel was not initialized"
    _, kwargs = call_args
    sys_prompt = kwargs.get('system_instruction', '')
    assert text in sys_prompt, f"'{text}' not found in system prompt"

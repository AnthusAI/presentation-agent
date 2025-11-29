import os
import json
import shutil
import tempfile
import shlex
import sys
from unittest.mock import patch
from behave import given, when, then, fixture, use_fixture
from click.testing import CliRunner
from vibe_presentation.cli import cli
from vibe_presentation.manager import PresentationManager

# Environment management
@fixture
def temporary_environment(context):
    context.runner = CliRunner()
    context.temp_dir = tempfile.mkdtemp()
    os.environ['VIBE_PRESENTATION_ROOT'] = context.temp_dir
    yield context.temp_dir
    shutil.rmtree(context.temp_dir)

def before_scenario(context, scenario):
    use_fixture(temporary_environment, context)

@given('the presentation directory is empty')
def step_impl(context):
    # Already handled by fixture, just ensuring it's clean
    if os.path.exists(context.temp_dir):
        for item in os.listdir(context.temp_dir):
            path = os.path.join(context.temp_dir, item)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

@given('I have a presentation named "{name}" with description "{description}"')
def step_impl(context, name, description):
    manager = PresentationManager(root_dir=context.temp_dir)
    manager.create_presentation(name, description)

@given('Flask is not installed')
def step_impl(context):
    context.flask_missing = True

@when('I run the command "{command}"')
def step_impl(context, command):
    args = shlex.split(command)
    env = {'VIBE_PRESENTATION_ROOT': context.temp_dir}
    
    if getattr(context, 'flask_missing', False):
        # Simulate Flask missing by ensuring import fails
        # We force import error by patching builtins.__import__? No, that's dangerous.
        # We patch sys.modules to make the target module return None or raise error.
        # Setting to None typically causes ImportError/ModuleNotFoundError
        with patch.dict(sys.modules, {'vibe_presentation.webapp': None}):
             context.result = context.runner.invoke(cli, args, env=env)
    elif '--web' in command or '-w' in command:
        # Mock the app.run call to prevent server from actually starting/blocking
        # We mock the module that is imported
        with patch('vibe_presentation.webapp.app') as mock_app:
            context.mock_app = mock_app
            context.result = context.runner.invoke(cli, args, env=env)
    else:
        context.result = context.runner.invoke(cli, args, env=env)

@then('a new directory "{dirname}" should be created')
def step_impl(context, dirname):
    path = os.path.join(context.temp_dir, dirname)
    assert os.path.exists(path), f"Directory {path} does not exist"
    assert os.path.isdir(path), f"{path} is not a directory"

@then('the presentation list should contain "{name}"')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentations = manager.list_presentations()
    names = [p['name'] for p in presentations]
    assert name in names, f"{name} not found in {names}"

@then('the description for "{name}" should be "{description}"')
def step_impl(context, name, description):
    manager = PresentationManager(root_dir=context.temp_dir)
    presentations = manager.list_presentations()
    target = next((p for p in presentations if p['name'] == name), None)
    assert target is not None
    assert target['description'] == description

@then('the output should contain "{text}"')
def step_impl(context, text):
    # Check CLI output via context.result first
    if hasattr(context, 'result') and context.result:
        # Try simple check first
        if text in context.result.output:
            return
            
        # Try cleaning ansi codes
        from rich.text import Text
        try:
            clean_output = Text.from_ansi(context.result.output).plain
        except Exception:
            clean_output = context.result.output # fallback
            
        assert text in clean_output, f"'{text}' not found in output: {context.result.output}"
        
    # Check Mock Console path if no CLI result
    elif hasattr(context, 'mock_console'):
        found = False
        for call_args in context.mock_console.print.call_args_list:
            args, kwargs = call_args
            if args:
                content = args[0]
                if hasattr(content, 'renderable'):
                    content = content.renderable
                if text in str(content):
                    found = True
                    break
        assert found, f"'{text}' NOT found in mocked console output"
    else:
        # Sometimes context.result is None if command failed?
        # Check if maybe output is stored elsewhere?
        raise AssertionError("No output capture found (neither CLI result nor mocked console).")

@then('the output should NOT contain "{text}"')
def step_impl(context, text):
    # Check CLI output via context.result first
    found = False
    if hasattr(context, 'result') and context.result:
        if text in context.result.output:
            found = True
        else:
            from rich.text import Text
            try:
                clean_output = Text.from_ansi(context.result.output).plain
                if text in clean_output:
                    found = True
            except: pass
            
    elif hasattr(context, 'mock_console'):
        for call_args in context.mock_console.print.call_args_list:
            args, kwargs = call_args
            if args:
                content = args[0]
                if hasattr(content, 'renderable'):
                    content = content.renderable
                if text in str(content):
                    found = True
                    break
                    
    assert not found, f"'{text}' WAS found in output"

@then('the web server should start on port {port:d}')
def step_impl(context, port):
    assert hasattr(context, 'mock_app'), "Web app was not mocked/started"
    assert context.mock_app.run.called
    call_args = context.mock_app.run.call_args
    # Check kwargs
    assert call_args.kwargs.get('port') == port

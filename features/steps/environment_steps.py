import os
import sys
from behave import given, when, then
from pathlib import Path

@given('the environment variable "{key}" is set in .env')
def step_env_var_in_dotenv(context, key):
    """Verify the .env file exists and contains the key."""
    dotenv_path = Path(".env")
    context.dotenv_exists = dotenv_path.exists()
    
    if context.dotenv_exists:
        content = dotenv_path.read_text()
        context.key_in_dotenv = f"{key}=" in content
    else:
        context.key_in_dotenv = False

@given('the environment variable "{key}" is set')
def step_env_var_set(context, key):
    """Set a test environment variable."""
    os.environ[key] = "test_api_key_value"
    context.test_key = key

@when('I import the vibe_presentation package')
def step_import_package(context):
    """Import the package which should trigger load_dotenv."""
    # Clear any cached imports
    if 'deckbot' in sys.modules:
        del sys.modules['deckbot']
    
    import deckbot
    context.package_imported = True

@when('I import the webapp module')
def step_import_webapp(context):
    """Import the webapp module which should have access to loaded env vars."""
    # Since __init__.py loads dotenv, importing any module should work
    if 'deckbot' in sys.modules:
        del sys.modules['deckbot']
    if 'deckbot.webapp' in sys.modules:
        del sys.modules['deckbot.webapp']
    
    import deckbot.webapp
    context.webapp_imported = True

@when('I create an Agent instance')
def step_create_agent(context):
    """Create an agent instance for testing."""
    from deckbot.agent import Agent
    
    test_context = {
        'name': 'test-presentation',
        'description': 'Test presentation for environment testing'
    }
    
    # Create test presentation directory if needed
    import tempfile
    test_dir = tempfile.mkdtemp()
    os.environ['VIBE_PRESENTATION_ROOT'] = test_dir
    
    context.agent = Agent(test_context)
    context.test_dir = test_dir

@then('the environment variable "{key}" should be accessible')
def step_env_var_accessible(context, key):
    """Verify the environment variable is accessible."""
    assert os.getenv(key) is not None, f"Environment variable {key} not found"

@then('the agent should have the API key configured')
def step_agent_has_api_key(context):
    """Verify agent has API key set."""
    assert context.agent.api_key is not None, "Agent API key is None"
    assert context.agent.api_key != "", "Agent API key is empty"

@then('the agent should not reference any legacy API key variables')
def step_no_legacy_keys(context):
    """Verify no legacy key references in agent code."""
    from pathlib import Path
    
    # Check agent.py source code
    agent_file = Path("src/deckbot/agent.py")
    agent_content = agent_file.read_text()
    
    assert "GOOGLE_AI_STUDIO_API_KEY" not in agent_content, \
        "Legacy GOOGLE_AI_STUDIO_API_KEY found in agent.py"
    
    # Check nano_banana.py source code
    nano_file = Path("src/deckbot/nano_banana.py")
    nano_content = nano_file.read_text()
    
    assert "GOOGLE_AI_STUDIO_API_KEY" not in nano_content, \
        "Legacy GOOGLE_AI_STUDIO_API_KEY found in nano_banana.py"
    
    # Clean up test directory
    if hasattr(context, 'test_dir'):
        import shutil
        shutil.rmtree(context.test_dir, ignore_errors=True)


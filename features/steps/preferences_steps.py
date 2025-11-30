import os
import yaml
import tempfile
import shutil
from behave import given, when, then
from unittest.mock import patch
from deckbot.preferences import PreferencesManager

@given('I am using DeckBot for the first time')
def step_impl(context):
    """Set up a clean environment with no config file."""
    context.temp_dir = tempfile.mkdtemp()
    context.config_path = os.path.join(context.temp_dir, ".deckbot.yaml")
    # Initialize manager with custom path
    context.prefs = PreferencesManager(config_path=context.config_path)
    # Ensure we start fresh (PreferencesManager creates default file on init)
    # But for "first time" simulation, we want to verify creation behavior.
    # Actually, PreferencesManager() init calls _ensure_config_exists().
    # So by initializing it, we are simulating the first run.
    pass

@when('I check my preferences')
def step_impl(context):
    """Read the preferences."""
    context.current_prefs = context.prefs.get_all()
    context.theme_pref = context.prefs.get('theme')
    context.color_theme_pref = context.prefs.get('color_theme')

@then('the stored theme preference should be "{expected_theme}"')
def step_impl(context, expected_theme):
    """Verify theme preference."""
    # If we haven't read them yet
    if not hasattr(context, 'theme_pref'):
        context.theme_pref = context.prefs.get('theme')
    assert context.theme_pref == expected_theme, f"Expected theme {expected_theme}, got {context.theme_pref}"

@then('the stored color theme preference should be "{expected_theme}"')
def step_impl(context, expected_theme):
    """Verify color theme preference."""
    if not hasattr(context, 'color_theme_pref'):
        context.color_theme_pref = context.prefs.get('color_theme')
    assert context.color_theme_pref == expected_theme, f"Expected color theme {expected_theme}, got {context.color_theme_pref}"

@then('a ".deckbot.yaml" file should exist')
def step_impl(context):
    """Verify config file creation."""
    assert os.path.exists(context.config_path), "Config file was not created"

@given('I have DeckBot configured')
def step_impl(context):
    """Set up environment with existing config."""
    context.temp_dir = tempfile.mkdtemp()
    context.config_path = os.path.join(context.temp_dir, ".deckbot.yaml")
    context.prefs = PreferencesManager(config_path=context.config_path)

@when('I set my theme preference to "{theme}"')
def step_impl(context, theme):
    """Update theme preference."""
    context.prefs.set('theme', theme)

@then('my ".deckbot.yaml" should contain "{content}"')
def step_impl(context, content):
    """Verify file content."""
    with open(context.config_path, 'r') as f:
        file_content = f.read()
    assert content in file_content, f"Expected '{content}' in file, got:\n{file_content}"

@then('subsequent sessions should use the dark theme')
def step_impl(context):
    """Verify persistence across new instances."""
    new_prefs = PreferencesManager(config_path=context.config_path)
    assert new_prefs.get('theme') == 'dark'

@given("I'm working on a corporate presentation")
def step_impl(context):
    """Context setting - implies we want to customize branding."""
    context.execute_steps("Given I have DeckBot configured")

@when('I change my color theme to "{theme}"')
def step_impl(context, theme):
    """Update color theme."""
    context.prefs.set('color_theme', theme)
    context.new_color_theme = theme

@then('my preference should persist across sessions')
def step_impl(context):
    """Verify persistence."""
    new_prefs = PreferencesManager(config_path=context.config_path)
    assert new_prefs.get('color_theme') == context.new_color_theme

@then('the web UI should reflect the new colors')
def step_impl(context):
    """Mock check for web UI integration."""
    # Since this is a unit test for preferences, we trust that the Web UI 
    # reads this preference (covered by web_ui.feature). 
    # Here we verify the data source is correct.
    assert context.prefs.get('color_theme') == context.new_color_theme

@given('I have customized preferences')
def step_impl(context):
    """Setup custom preferences."""
    context.execute_steps("Given I have DeckBot configured")
    context.prefs.set('theme', 'dark')
    context.prefs.set('color_theme', 'midwest')

@when('I delete my theme preference')
def step_impl(context):
    """Delete a preference key."""
    context.prefs.delete('theme')

@then('it should revert to "{default_value}"')
def step_impl(context, default_value):
    """Verify fallback to default logic or None."""
    # PreferencesManager.get() returns None if key missing, 
    # unless we ask for a default.
    # The Manager doesn't automatically re-populate deleted keys with defaults 
    # unless _ensure_config_exists is triggered again or we handle it in get().
    # Let's check what get() returns.
    val = context.prefs.get('theme')
    
    # If logic implies "revert to system default", the application logic handles that fallback.
    # But PreferencesManager.get('theme', 'system') is how app does it.
    # Let's check if the file actually lost the key.
    with open(context.config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # If we deleted it, it should be gone from the file.
    assert 'theme' not in data, "Key 'theme' should have been removed from file"
    
    # And get() with default should return the expected value
    assert context.prefs.get('theme', 'system') == default_value

@then('my other preferences should remain unchanged')
def step_impl(context):
    """Verify isolation of changes."""
    assert context.prefs.get('color_theme') == 'midwest'

@given('my ".deckbot.yaml" becomes corrupted')
def step_impl(context):
    """Simulate file corruption."""
    context.execute_steps("Given I have DeckBot configured")
    with open(context.config_path, 'w') as f:
        f.write("This is not valid yaml: [ { ")

@when('I try to read preferences')
def step_impl(context):
    """Attempt to read corrupted config."""
    # Force a re-read
    try:
        context.read_result = context.prefs._read_config()
    except Exception as e:
        context.read_error = e

@then('I should get default values')
def step_impl(context):
    """Verify graceful failure."""
    # _read_config should return empty dict or handle error, not crash
    # The implementation prints error and returns {}
    assert context.read_result == {}, f"Expected empty dict on error, got {context.read_result}"

@then('the system should not crash')
def step_impl(context):
    """Verify no exception was raised to the caller."""
    assert not hasattr(context, 'read_error'), f"System crashed with: {context.read_error}"


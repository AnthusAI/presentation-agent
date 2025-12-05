from behave import given, when, then, step
from unittest.mock import MagicMock, patch
from deckbot.manager import PresentationManager
from deckbot.tools import PresentationTools
from deckbot.nano_banana import NanoBananaClient
import os

@given('I create a new presentation for aspect ratio testing named "{name}"')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    context.manager = manager
    manager.create_presentation(name)
    context.presentation_name = name
    context.presentation_dir = os.path.join(context.temp_dir, name)

@given('I have a presentation for aspect ratio testing named "{name}"')
def step_impl(context, name):
    manager = PresentationManager(root_dir=context.temp_dir)
    context.manager = manager
    if not manager.get_presentation(name):
        manager.create_presentation(name)
    context.presentation_name = name
    context.presentation_dir = os.path.join(context.temp_dir, name)
    
    # Setup tools
    pres_context = manager.get_presentation(name)
    nano_client = MagicMock(spec=NanoBananaClient)
    context.tools = PresentationTools(pres_context, nano_client)
    # Override tools root dir to use temp dir
    context.tools.manager = manager
    context.tools.presentation_dir = context.presentation_dir

@then('the presentation aspect ratio should be "{ratio}"')
def step_impl(context, ratio):
    pres = context.manager.get_presentation(context.presentation_name)
    assert pres['aspect_ratio'] == ratio

@then('the marp file should contain "{text}"')
def step_impl(context, text):
    marp_path = os.path.join(context.presentation_dir, "deck.marp.md")
    with open(marp_path, "r") as f:
        content = f.read()
    assert text in content

@step('I set the aspect ratio to "{ratio}"')
def step_impl(context, ratio):
    with patch('subprocess.run') as mock_run:
        context.tools.set_aspect_ratio(ratio)

# Note: The "I save the presentation as" step is now defined in save_as_steps.py
# to support additional parameters like description and copy_images
# This maintains backward compatibility with aspect_ratio.feature

@then('I should have a presentation named "{name}"')
def step_impl(context, name):
    assert context.manager.get_presentation(name) is not None

@then('the presentation "{name}" should have aspect ratio "{ratio}"')
def step_impl(context, name, ratio):
    pres = context.manager.get_presentation(name)
    assert pres['aspect_ratio'] == ratio

@then('the presentation "{name}" marp file should contain "{text}"')
def step_impl(context, name, text):
    path = os.path.join(context.temp_dir, name, "deck.marp.md")
    with open(path, "r") as f:
        content = f.read()
    assert text in content

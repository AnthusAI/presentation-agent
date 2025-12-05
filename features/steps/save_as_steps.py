from behave import given, when, then, step, use_step_matcher
from unittest.mock import MagicMock, patch
from deckbot.manager import PresentationManager
from deckbot.tools import PresentationTools
from deckbot.nano_banana import NanoBananaClient
import os
import json
import shutil

# Note: "I have a presentation named" is defined in tools_steps.py

@given('the presentation "{name}" has description "{description}"')
def step_impl(context, name, description):
    manager = PresentationManager(root_dir=context.temp_dir)
    pres = manager.get_presentation(name)
    if pres:
        pres['description'] = description
        metadata_path = os.path.join(context.temp_dir, name, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(pres, f, indent=2)

@given('the presentation "{name}" has an image file "{filename}"')
def step_impl(context, name, filename):
    images_dir = os.path.join(context.temp_dir, name, "images")
    os.makedirs(images_dir, exist_ok=True)
    image_path = os.path.join(images_dir, filename)
    # Create a dummy image file
    with open(image_path, "w") as f:
        f.write("dummy image content")

@given('I have a folder named "{folder_name}"')
def step_impl(context, folder_name):
    folder_path = os.path.join(context.temp_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    # Create a minimal metadata.json to make it a valid presentation folder
    metadata_path = os.path.join(folder_path, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump({
            "name": folder_name,
            "description": "",
            "aspect_ratio": "4:3",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }, f, indent=2)

@given('the presentation "{name}" has a file "{filename}"')
def step_impl(context, name, filename):
    file_path = os.path.join(context.temp_dir, name, filename)
    # Ensure the file exists (it should from create_presentation)
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write("")

@given('I set the aspect ratio of "{name}" to "{ratio}"')
def step_impl(context, name, ratio):
    manager = PresentationManager(root_dir=context.temp_dir)
    manager.set_presentation_aspect_ratio(name, ratio)

# Use regex matcher only for the specific "save as" steps to avoid conflicts
use_step_matcher("re")

def _get_source_presentation_name(context):
    """Helper to get source presentation name from context."""
    source_name = getattr(context, 'presentation_name', getattr(context, 'current_presentation_name', None))
    if source_name is None:
        # Try to get from manager
        if hasattr(context, 'manager'):
            presentations = context.manager.list_presentations()
            if presentations:
                source_name = presentations[0]['name']
    if source_name is None:
        raise ValueError("No source presentation found in context")
    return source_name

@when(r'I save the presentation as "(?P<new_name>[^"]+)" with description "(?P<description>[^"]+)"')
def step_impl(context, new_name, description):
    # Ensure manager is set up (from tools_steps.py)
    if not hasattr(context, 'manager'):
        manager = PresentationManager(root_dir=context.temp_dir)
        context.manager = manager
    source_name = _get_source_presentation_name(context)
    context.manager.duplicate_presentation(source_name, new_name, description=description)
    context.new_presentation_name = new_name

def _get_source_presentation_name(context):
    """Helper to get source presentation name from context."""
    source_name = getattr(context, 'presentation_name', getattr(context, 'current_presentation_name', None))
    if source_name is None:
        # Try to get from manager
        if hasattr(context, 'manager'):
            presentations = context.manager.list_presentations()
            if presentations:
                source_name = presentations[0]['name']
    if source_name is None:
        raise ValueError("No source presentation found in context")
    return source_name

@when(r'I save the presentation as "(?P<new_name>[^"]+)" without description')
def step_impl(context, new_name):
    if not hasattr(context, 'manager'):
        manager = PresentationManager(root_dir=context.temp_dir)
        context.manager = manager
    source_name = _get_source_presentation_name(context)
    context.manager.duplicate_presentation(source_name, new_name, description=None)
    context.new_presentation_name = new_name

@when(r'I save the presentation as "(?P<new_name>[^"]+)" with images')
def step_impl(context, new_name):
    if not hasattr(context, 'manager'):
        manager = PresentationManager(root_dir=context.temp_dir)
        context.manager = manager
    source_name = _get_source_presentation_name(context)
    context.manager.duplicate_presentation(source_name, new_name, copy_images=True)
    context.new_presentation_name = new_name

@when(r'I save the presentation as "(?P<new_name>[^"]+)" without images')
def step_impl(context, new_name):
    if not hasattr(context, 'manager'):
        manager = PresentationManager(root_dir=context.temp_dir)
        context.manager = manager
    source_name = _get_source_presentation_name(context)
    context.manager.duplicate_presentation(source_name, new_name, copy_images=False)
    context.new_presentation_name = new_name

# Reset to parse matcher for other steps
use_step_matcher("parse")

@when('I save the presentation as "{new_name}"')
def step_impl(context, new_name):
    if not hasattr(context, 'manager'):
        manager = PresentationManager(root_dir=context.temp_dir)
        context.manager = manager
    source_name = _get_source_presentation_name(context)
    context.manager.duplicate_presentation(source_name, new_name)
    context.new_presentation_name = new_name

@then('I should have a presentation folder for "{name}"')
def step_impl(context, name):
    # Check if folder exists (may be auto-incremented)
    # First try the exact name, then check for auto-incremented versions
    folder_path = os.path.join(context.temp_dir, name)
    if not os.path.exists(folder_path):
        # Check for auto-incremented versions
        counter = 2
        while os.path.exists(os.path.join(context.temp_dir, f"{name} {counter}")):
            folder_path = os.path.join(context.temp_dir, f"{name} {counter}")
            break
        counter += 1
    
    # At minimum, check that metadata exists somewhere
    found = False
    for item in os.listdir(context.temp_dir):
        item_path = os.path.join(context.temp_dir, item)
        if os.path.isdir(item_path):
            metadata_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    if metadata.get("name") == name:
                        found = True
                        break
    
    assert found, f"Presentation with name '{name}' not found in metadata"

@then('I should have a folder named "{folder_name}"')
def step_impl(context, folder_name):
    folder_path = os.path.join(context.temp_dir, folder_name)
    assert os.path.exists(folder_path), f"Folder '{folder_name}' does not exist"

@then('the presentation "{name}" should have description "{description}"')
def step_impl(context, name, description):
    # Find the folder by checking metadata
    found_folder = None
    for item in os.listdir(context.temp_dir):
        item_path = os.path.join(context.temp_dir, item)
        if os.path.isdir(item_path):
            metadata_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    if metadata.get("name") == name:
                        found_folder = item_path
                        break
    
    assert found_folder is not None, f"Presentation with name '{name}' not found"
    metadata_path = os.path.join(found_folder, "metadata.json")
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    assert metadata.get("description") == description, f"Expected description '{description}', got '{metadata.get('description')}'"

@then('the presentation metadata name should be "{name}"')
def step_impl(context, name):
    # Find any folder with this name in metadata
    found = False
    for item in os.listdir(context.temp_dir):
        item_path = os.path.join(context.temp_dir, item)
        if os.path.isdir(item_path):
            metadata_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    if metadata.get("name") == name:
                        found = True
                        break
    
    assert found, f"No presentation found with metadata name '{name}'"

@then('the presentation "{folder_name}" should have name "{name}" in metadata')
def step_impl(context, folder_name, name):
    folder_path = os.path.join(context.temp_dir, folder_name)
    assert os.path.exists(folder_path), f"Folder '{folder_name}' does not exist"
    metadata_path = os.path.join(folder_path, "metadata.json")
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    assert metadata.get("name") == name, f"Expected metadata name '{name}', got '{metadata.get('name')}'"

@then('the presentation "{name}" should have an image file "{filename}"')
def step_impl(context, name, filename):
    # Find the folder by checking metadata
    found_folder = None
    for item in os.listdir(context.temp_dir):
        item_path = os.path.join(context.temp_dir, item)
        if os.path.isdir(item_path):
            metadata_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    if metadata.get("name") == name:
                        found_folder = item_path
                        break
    
    assert found_folder is not None, f"Presentation with name '{name}' not found"
    image_path = os.path.join(found_folder, "images", filename)
    assert os.path.exists(image_path), f"Image file '{filename}' not found in presentation '{name}'"

@then('the presentation "{name}" should not have an image file "{filename}"')
def step_impl(context, name, filename):
    # Find the folder by checking metadata
    found_folder = None
    for item in os.listdir(context.temp_dir):
        item_path = os.path.join(context.temp_dir, item)
        if os.path.isdir(item_path):
            metadata_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    if metadata.get("name") == name:
                        found_folder = item_path
                        break
    
    assert found_folder is not None, f"Presentation with name '{name}' not found"
    image_path = os.path.join(found_folder, "images", filename)
    assert not os.path.exists(image_path), f"Image file '{filename}' should not exist in presentation '{name}'"

# Note: "the presentation {name} should have aspect ratio {ratio}" is defined in aspect_ratio_steps.py

@then('the presentation "{name}" should have a file "{filename}"')
def step_impl(context, name, filename):
    # Find the folder by checking metadata
    found_folder = None
    for item in os.listdir(context.temp_dir):
        item_path = os.path.join(context.temp_dir, item)
        if os.path.isdir(item_path):
            metadata_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    if metadata.get("name") == name:
                        found_folder = item_path
                        break
    
    assert found_folder is not None, f"Presentation with name '{name}' not found"
    file_path = os.path.join(found_folder, filename)
    assert os.path.exists(file_path), f"File '{filename}' not found in presentation '{name}'"


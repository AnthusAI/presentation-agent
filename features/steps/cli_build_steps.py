import os
from behave import given, when, then
from unittest.mock import patch, MagicMock
import subprocess
from deckbot.cli import cli
from deckbot.manager import PresentationManager

@given('the presentation has a valid "deck.marp.md" file')
def step_impl(context):
    # Ensure the file exists (PresentationManager.create_presentation likely creates it)
    # If we need specific content, we can write it here.
    # Assuming the previous step created the presentation, we just check/ensure the file.
    # The context.temp_dir is set by the fixture in cli_steps.py if we use it.
    # We need to find the presentation directory.
    
    # We need to know the presentation name from the previous step context if possible, 
    # or just find the only directory in temp_dir.
    
    manager = PresentationManager(root_dir=context.temp_dir)
    presentations = manager.list_presentations()
    if not presentations:
        raise Exception("No presentation found to add marp file to")
    
    pres_name = presentations[0]['name']
    pres_dir = os.path.join(context.temp_dir, pres_name)
    marp_file = os.path.join(pres_dir, "deck.marp.md")
    
    if not os.path.exists(marp_file):
        with open(marp_file, "w") as f:
            f.write("---\nmarp: true\n---\n# Slide 1")

@when('I run the deckbot command "{command}"')
def step_impl(context, command):
    # We need to patch subprocess.run to avoid actual execution and simulate output file creation
    with patch('subprocess.run') as mock_run:
        # Configure mock to create the output file if it's a build command
        def side_effect(args, **kwargs):
            # args is likely ["npx", "@marp-team/marp-cli", ...]
            if "npx" in args and "@marp-team/marp-cli" in args:
                # Check output format
                cmd_str = " ".join(args)
                pres_dir = None
                # Find presentation dir in args (it's usually passed as input or -I ?)
                # Our implementation will likely pass the input file or directory.
                # Let's assume implementation uses logic to determine output path.
                
                # We need to simulate the file creation that Marp would do.
                # The CLI implementation needs to pass the output filename to Marp or Marp derives it.
                # If we pass `-o output_file`, we can extract it.
                
                output_file = None
                if "-o" in args:
                    idx = args.index("-o")
                    if idx + 1 < len(args):
                        output_file = args[idx+1]
                elif "--pdf" in args: # Marp CLI options
                    pass 
                
                # However, we are mocking the CALL in the python code.
                # The python code will calculate the path.
                # Let's look at how we implement the CLI.
                pass
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect
        context.mock_subprocess = mock_run
        
        # Reuse the execution logic from cli_steps or duplicate simple invoke
        from click.testing import CliRunner
        import shlex
        
        runner = CliRunner()
        args = shlex.split(command)
        env = {'VIBE_PRESENTATION_ROOT': context.temp_dir}
        
        # We also need to handle the file creation simulation *during* the command execution 
        # OR we assume the command *would* create it and we manually create it in the test 
        # if the command succeeds, but that defeats the purpose of testing the command's logic.
        
        # Better approach: The CLI command calculates the output path and calls subprocess.
        # We verify the subprocess call arguments.
        # AND for the "Then file exists" step, we might need to manually create it in the mock side_effect 
        # IF the python code doesn't verify existence. 
        # But the user wants to verify the file exists.
        
        # Let's define the side_effect to actually create a dummy file if the command looks correct.
        def file_creation_side_effect(args, **kwargs):
            # Parse args to find output file
            # Command: npx @marp-team/marp-cli deck.marp.md -o deck.pdf
            try:
                if "-o" in args:
                    out_idx = args.index("-o") + 1
                    out_path = args[out_idx]
                    # Create dummy file
                    with open(out_path, 'w') as f:
                        f.write("dummy content")
            except ValueError:
                pass
            return MagicMock(returncode=0)
            
        mock_run.side_effect = file_creation_side_effect
        
        context.result = runner.invoke(cli, args, env=env)


@then('the command should exit successfully')
def step_impl(context):
    if context.result.exit_code != 0:
        print(context.result.output)
    assert context.result.exit_code == 0, f"Command failed with exit code {context.result.exit_code}"

@then('a file named "{filename}" should exist in the "{presentation_name}" presentation folder')
def step_impl(context, filename, presentation_name):
    filepath = os.path.join(context.temp_dir, presentation_name, filename)
    assert os.path.exists(filepath), f"File {filepath} does not exist. Directory contents: {os.listdir(os.path.dirname(filepath))}"





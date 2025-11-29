import click
import subprocess
import os
from dotenv import load_dotenv
from rich.console import Console
from vibe_presentation.manager import PresentationManager
from vibe_presentation.repl import start_repl

# Load environment variables from .env file
load_dotenv()

console = Console()

@click.group(invoke_without_command=True)
@click.option('--continue', 'resume', is_flag=True, help='Resume the most recently edited presentation')
@click.pass_context
def cli(ctx, resume):
    """Vibe-Coded Presentation CLI"""
    if ctx.invoked_subcommand is None:
        # If resume flag is set, find most recent and load it
        manager = PresentationManager()
        if resume:
            presentations = manager.list_presentations()
            # list_presentations returns sorted by reverse chronological order (created_at)
            # If we want most recently *edited*, file system check is better, but created_at sort is a good proxy for "last active" usually
            # unless metadata isn't updated.
            # Let's trust the order returned by manager.list_presentations() as it is sorted.
            if presentations:
                latest = presentations[0]
                # Invoke load command directly
                ctx.invoke(load, name=latest['name'], resume=True)
                return
            else:
                console.print("[red]No presentations found to resume.[/red]")
                return

        # Interactive mode if no command provided
        from rich.prompt import Prompt
        manager = PresentationManager()
        presentations = manager.list_presentations()
        
        if not presentations:
            if Prompt.ask("No presentations found. Create one?", choices=["y", "n"], default="y") == "y":
                name = Prompt.ask("Enter presentation name")
                desc = Prompt.ask("Enter description", default="")
                ctx.invoke(create, name=name, description=desc)
                # Then load it
                ctx.invoke(load, name=name)
            return

        console.print("[bold]Select a presentation to load:[/bold]")
        for i, p in enumerate(presentations):
            console.print(f"{i+1}. [bold cyan]{p['name']}[/bold cyan] ({p.get('description', '')})")
        
        console.print("n. [italic]Create new presentation[/italic]")
        
        choice = Prompt.ask("Choice", default="1")
        
        if choice.lower() == 'n':
            name = Prompt.ask("Enter presentation name")
            desc = Prompt.ask("Enter description", default="")
            ctx.invoke(create, name=name, description=desc)
            ctx.invoke(load, name=name, new_presentation=True)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(presentations):
                    name = presentations[idx]['name']
                    ctx.invoke(load, name=name)
                else:
                    console.print("[red]Invalid selection.[/red]")
            except ValueError:
                console.print("[red]Invalid input.[/red]")

@cli.command()
@click.argument('name')
@click.option('--description', '-d', default="", help='Description of the presentation')
def create(name, description):
    """Create a new presentation"""
    manager = PresentationManager()
    try:
        manager.create_presentation(name, description)
        console.print(f"[green]Created presentation '{name}'[/green]")
    except ValueError as e:
        console.print(f"[red]{str(e)}[/red]")

@cli.command()
def list():
    """List all presentations"""
    manager = PresentationManager()
    presentations = manager.list_presentations()
    
    if not presentations:
        console.print("No presentations found.")
        return

    console.print("[bold]Presentations[/bold]")
    
    for p in presentations:
        console.rule()
        console.print(f"[bold cyan]{p['name']}[/bold cyan]")
        console.print(f"[dim green]Created: {p.get('created_at', '')}[/dim green]")
        console.print(f"{p.get('description', '')}")

    console.rule()

@cli.command()
@click.argument('name')
@click.option('--continue', 'resume', is_flag=True, help='Resume the previous chat session')
def load(name, resume):
    """Load a presentation and start the assistant"""
    manager = PresentationManager()
    presentation = manager.get_presentation(name)
    
    if not presentation:
        console.print(f"[red]Presentation '{name}' not found.[/red]")
        return

    start_repl(presentation, resume=resume)

@cli.command()
def open_folder():
    """Open the presentations folder in the file explorer"""
    manager = PresentationManager()
    root_dir = manager.root_dir
    
    if not os.path.exists(root_dir):
        console.print(f"[red]Presentation directory {root_dir} does not exist.[/red]")
        return

    console.print(f"[green]Opening {root_dir}...[/green]")
    
    if os.name == 'nt':  # Windows
        os.startfile(root_dir)
    elif os.name == 'posix':  # macOS/Linux
        # First try to open in VS Code if 'code' is available
        try:
            if subprocess.call(["which", "code"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
                console.print("[dim]Opening in VS Code...[/dim]")
                subprocess.run(["code", root_dir])
                return
        except Exception:
            pass # Fallback to standard opener

        # Check for macOS specific command
        if subprocess.call(["which", "open"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
             subprocess.run(["open", root_dir])
        else:
             subprocess.run(["xdg-open", root_dir])

@cli.command()
@click.argument('name')
def preview(name):
    """Start Marp server to preview the presentation"""
    manager = PresentationManager()
    presentation = manager.get_presentation(name)
    
    if not presentation:
        console.print(f"[red]Presentation '{name}' not found.[/red]")
        return

    # Construct path to presentation directory
    root_dir = manager.root_dir
    presentation_dir = os.path.join(root_dir, name)
    
    console.print(f"[green]Starting Marp preview for {name}...[/green]")
    console.print("Press Ctrl+C to stop.")
    
    try:
        subprocess.run(["npx", "@marp-team/marp-cli", "-s", presentation_dir], check=True)
    except KeyboardInterrupt:
        console.print("\nStopped preview.")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running Marp: {e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: npx not found. Please ensure Node.js and npm are installed.[/red]")

if __name__ == '__main__':
    cli()

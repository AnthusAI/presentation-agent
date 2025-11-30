import click
import subprocess
import os
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from deckbot.manager import PresentationManager
from deckbot.repl import start_repl

console = Console()

def _interactive_create(ctx, manager):
    # 1. Template Selection
    templates = manager.list_templates()
    template_choice = None
    
    if templates:
        console.print("\n[bold]Available Templates:[/bold]")
        for i, t in enumerate(templates):
            console.print(f"{i+1}. [cyan]{t['name']}[/cyan]: {t['description']}")
        console.print("n. [dim]Start from scratch[/dim]")
        
        # Use Prompt instead of IntPrompt to allow 'n'
        choices = [str(i+1) for i in range(len(templates))] + ['n']
        t_choice = Prompt.ask("Select a template", choices=choices, default='n')
        
        if t_choice.lower() != 'n':
            t_idx = int(t_choice)
            template_choice = templates[t_idx-1]['name']

    # 2. Details
    console.print()
    name = Prompt.ask("Enter presentation name")
    desc = Prompt.ask("Enter description", default="")
    
    ctx.invoke(create, name=name, description=desc, template=template_choice)
    ctx.invoke(load, name=name, new_presentation=True)

@click.group(invoke_without_command=True)
@click.option('--continue', 'resume', is_flag=True, help='Resume the most recently edited presentation')
@click.option('--web', '-w', is_flag=True, help='Start the web UI server')
@click.option('--port', default=5555, help='Port for web server (only used with --web)')
@click.pass_context
def cli(ctx, resume, web, port):
    """Vibe-Coded Presentation CLI"""
    if web:
        try:
            from deckbot.webapp import app
            console.print(f"[green]Starting Web UI on http://localhost:{port}[/green]")
            app.run(port=port, debug=True)
        except ImportError:
            console.print("[red]Error: Flask not installed. Please run: pip install flask[/red]")
        except Exception as e:
            console.print(f"[red]Error starting web server: {e}[/red]")
        return

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
        # Imports moved to top
        manager = PresentationManager()
        presentations = manager.list_presentations()
        
        if not presentations:
            if Prompt.ask("No presentations found. Create one?", choices=["y", "n"], default="y") == "y":
                _interactive_create(ctx, manager)
            return

        console.print("[bold]Select a presentation to load:[/bold]")
        for i, p in enumerate(presentations):
            console.print(f"{i+1}. [cyan]{p['name']}[/cyan]: {p.get('description', '')}")
        
        console.print("n. [italic]Create new presentation[/italic]")
        
        choice = Prompt.ask("Choice", default="1")
        
        if choice.lower() == 'n':
            _interactive_create(ctx, manager)
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
@click.option('--template', '-t', default=None, help='Template to use')
def create(name, description, template):
    """Create a new presentation"""
    manager = PresentationManager()
    try:
        manager.create_presentation(name, description, template=template)
        if template:
            console.print(f"[green]Created presentation '{name}' from template '{template}'[/green]")
        else:
            console.print(f"[green]Created presentation '{name}'[/green]")
    except ValueError as e:
        console.print(f"[red]{str(e)}[/red]")

@cli.group()
def templates():
    """Manage templates"""
    pass

@templates.command(name='list')
def list_templates_cmd():
    """List available templates"""
    manager = PresentationManager()
    templates = manager.list_templates()
    
    if not templates:
        console.print("No templates found.")
        return

    console.print("[bold]Templates[/bold]")
    for t in templates:
        console.print(f"[bold cyan]{t['name']}[/bold cyan]: {t['description']}")

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
@click.option('--new', 'new_presentation', is_flag=True, hidden=True)
def load(name, resume, new_presentation):
    """Load a presentation and start the assistant"""
    manager = PresentationManager()
    presentation = manager.get_presentation(name)
    
    if not presentation:
        console.print(f"[red]Presentation '{name}' not found.[/red]")
        return

    start_repl(presentation, resume=resume, new_presentation=new_presentation)

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

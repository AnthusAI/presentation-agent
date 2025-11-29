import click
import subprocess
import os
from rich.console import Console
from rich.table import Table
from vibe_present.manager import PresentationManager
from vibe_present.repl import start_repl

console = Console()

@click.group()
def cli():
    """Vibe-Coded Presentation CLI"""
    pass

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

    table = Table(title="Presentations")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="magenta")
    table.add_column("Created At", style="green")

    for p in presentations:
        table.add_row(p['name'], p.get('description', ''), p.get('created_at', ''))

    console.print(table)

@cli.command()
@click.argument('name')
def load(name):
    """Load a presentation and start the assistant"""
    manager = PresentationManager()
    presentation = manager.get_presentation(name)
    
    if not presentation:
        console.print(f"[red]Presentation '{name}' not found.[/red]")
        return

    start_repl(presentation)

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

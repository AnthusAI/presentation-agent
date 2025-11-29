from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.markdown import Markdown
from rich.panel import Panel
from vibe_presentation.agent import Agent
from vibe_presentation.nano_banana import NanoBananaClient

console = Console()

def start_repl(presentation, resume=False, new_presentation=False):
    agent = Agent(presentation)
    welcome_message = "I can help you make a presentation."
    
    if resume:
        console.print("[dim]Resuming previous session...[/dim]")
        history = agent.load_history()
        if history:
            # Find last model message to show as context
            for msg in reversed(history):
                if msg.get('role') == 'model':
                    # Get content (support 'parts' list or 'content' string if simple)
                    content = msg.get('parts', [])
                    if isinstance(content, list) and content:
                        welcome_message = content[0]
                    elif isinstance(msg.get('content'), str):
                        welcome_message = msg.get('content')
                    break
    elif new_presentation:
        welcome_message = "I've created your new presentation. How would you like to start? I can suggest an outline or we can jump right in."

    welcome_text = f"""
[bold magenta]Presentation Agent[/bold magenta]

[bold green]Working on:[/bold green] {presentation['name']}
[italic]{presentation.get('description', '')}[/italic]

{welcome_message}
"""
    console.print(Panel(welcome_text, title="Vibe Coding", border_style="magenta2"))

    if not resume and not new_presentation:
        # Trigger initial summary/question
        console.print("[bold green]Analyzing presentation...[/bold green]")
        # We send a hidden system-like prompt to trigger the agent's initial behavior
        initial_prompt = "Analyze the current presentation state. If it is empty or has only a title, ask the user what kind of presentation they want to create. If it has content, summarize it briefly and ask what they want to change."
        try:
            # We don't log this "system" trigger to the history file if we can avoid it, 
            # but Agent logs everything. That's okay, it's part of the flow.
            with console.status("[bold green]Thinking...[/bold green]") as status:
                response = agent.chat(initial_prompt, status_spinner=status)
            console.print("[bold magenta]AI[/bold magenta]:")
            console.print(Markdown(response))
            console.print()
        except Exception as e:
            console.print(f"[red]Error generating initial summary: {e}[/red]")

    nano_client = NanoBananaClient(presentation)

    while True:
        console.print() # Vertical whitespace before prompt
        user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        
        if user_input.lower() in ['exit', 'quit', '/exit', '/quit', '/q']:
            break
        
        console.print() # Vertical whitespace
        
        if user_input.startswith('/image'):
            if len(user_input.strip()) <= 6:
                prompt = Prompt.ask("[bold yellow]Enter image prompt[/bold yellow]")
            else:
                prompt = user_input[7:].strip()
            
            if not prompt:
                console.print("[yellow]Image generation cancelled (empty prompt).[/yellow]")
                continue

            candidates = nano_client.generate_candidates(prompt)
            
            console.print("[bold]Generated Candidates:[/bold]")
            for i, path in enumerate(candidates):
                console.print(f"{i+1}. {path}")
                # In a real CLI we might try to display them or open them
            
            selection = IntPrompt.ask("Select an image (1-4) or 0 to cancel", choices=["0", "1", "2", "3", "4"])
            
            if selection > 0:
                filename = Prompt.ask("Enter filename to save as", default="slide_image.png")
                saved_path = nano_client.save_selection(candidates, selection - 1, filename)
                console.print(f"[green]Saved to {saved_path}[/green]")
            else:
                console.print("Cancelled.")
                
            continue

        # console.print("[bold green]Thinking...[/bold green]") # Removed duplicate print
        with console.status("[bold green]Thinking...[/bold green]") as status:
            response = agent.chat(user_input, status_spinner=status)
            
        console.print("[bold magenta]AI[/bold magenta]:")
        console.print(Markdown(response))
        console.print() # Vertical whitespace

from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.markdown import Markdown
from vibe_present.agent import Agent
from vibe_present.nano_banana import NanoBananaClient

console = Console()

def start_repl(presentation):
    console.print(f"[bold green]Loaded presentation: {presentation['name']}[/bold green]")
    console.print(f"[italic]{presentation.get('description', '')}[/italic]")
    console.print("Type 'exit' to quit, '/image <prompt>' to generate images, or ask me anything.")

    agent = Agent(presentation)
    nano_client = NanoBananaClient(presentation)

    while True:
        user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        
        if user_input.lower() in ['exit', 'quit']:
            break
        
        if user_input.startswith('/image '):
            prompt = user_input[7:].strip()
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

        with console.status("[bold green]Thinking...[/bold green]"):
            response = agent.chat(user_input)
            
        console.print("[bold magenta]AI[/bold magenta]:")
        console.print(Markdown(response))


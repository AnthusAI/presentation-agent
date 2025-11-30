<img src="assets/deckbot-logo.png" alt="DeckBot Logo" align="right" width="300">

# DeckBot: Vibe-code your presentations in minutes

This is a CLI AI assistant, similar to tools like Claude Code or the Gemini CLI, but specialized for creating presentation slide decks with **Marp**. Marp is a declarative system that lets you define presentations using Markdown, which can then be viewed as interactive HTML or exported to PDF.

This assistant helps you build these decks by writing content, organizing files, and using **Nano Banana** to generate custom images for your slides.

It shares some goals with tools like NotebookLM—using AI to create presentations—but it adopts a **code-developer perspective**. The single source of truth for your presentation is the source code: the Markdown files and image assets. This approach gives you complete ownership and the ability to fine-tune every detail, treating your deck as a software project.

This project demonstrates two core ideas:

1.  **Everything as Code (EaC)**: A philosophy that treats all aspects of a system as code. In the age of AI, this means if your work can be represented as code, AI agents can read, understand, and collaborate on it with you. By treating slide decks as software projects (Markdown source code), we gain fine-grained control, version control, and the ability to collaborate with AI coding assistants.
2.  **[Give an Agent a Tool](https://anth.us/blog/give-an-agent-a-tool/)**: Instead of trying to pre-program every possible behavior, we give an AI agent the right tools (file editing, image generation, compilation) and let it figure out how to use them to solve your problems.

While tools like NotebookLM are pushing boundaries with instant deck generation, they often act as black boxes: the result might look great, but you can't easily edit the details later. This project is about **ownership and control**. Because your presentation is treated as a software project (Markdown source code), you have complete freedom. You can open the files and tweak every detail manually, or ask the AI assistant to refactor entire sections. You own the source, so you control the output.

## Features

*   **Everything as Code**: Presentations are stored as Markdown files, making them version-control friendly and easy for LLMs to read and edit.
*   **AI Coding Assistant**: A built-in REPL powered by Google's Gemini models that acts as your pair programmer for slides. It can write content, organize structure, and manage files.
*   **Nano Banana Image Generation**: Integrated "Nano Banana" (Google Imagen) support. Just ask for an image, and the agent will generate multiple candidates for you to choose from.
*   **Interactive Workflow**:
    *   **Chat**: Discuss your high-level ideas and let the agent draft the slides.
    *   **Visualize**: Generate custom images on the fly.
    *   **Preview**: Live preview your deck using the Marp CLI.
    *   **Export**: Compile your finished deck to HTML or PDF.

## Behavior Driven Development (BDD)

This project uses **Behavior Driven Development** (using `behave`) as a primary tool for collaboration between humans and AI.

*   **Human-Readable Specs**: BDD feature files (`.feature`) serve as a clear, unambiguous contract between the user and the AI. They describe *what* the software should do in plain English.
*   **Stability & Reusability**: By codifying behavior into tests, we ensure that new features don't break existing ones. This allows us to build reliable, reusable software with the same effort often spent on "throwaway" scripts.
*   **AI Alignment**: For AI-assisted coding, BDD provides a perfect feedback loop. If the behavior specs pass, the implementation is correct, regardless of the underlying code structure. This allows us to focus on desired outcomes and feature stability rather than getting bogged down in implementation details.

### Running Tests

This project has **comprehensive BDD test coverage** for both backend and frontend:

**Run all tests:**
```bash
behave
```

**Backend/CLI tests:**
```bash
behave features/cli.feature          # CLI commands and interactive mode
behave features/templates.feature    # Template system
behave features/export.feature       # PDF export
```

**Frontend/Web UI tests:**
```bash
behave features/web_ui.feature       # Web UI, color themes, preferences, image selection
```

**See test output:**
```bash
behave --no-capture
```

**Test a specific scenario:**
```bash
behave features/web_ui.feature -n "Color Theme Selection"
```

All features are documented in the `features/` directory using Gherkin syntax. Read them to understand exactly how the system behaves!

## Installation

1.  **Clone and Environment Setup:**
    ```bash
    conda create -n deckbot python=3.11
    conda activate deckbot
    pip install -e .
    ```

2.  **External Dependencies:**
    *   **Node.js & npm**: Required for Marp CLI (preview/export).
    *   **Chrome/Chromium**: Required for PDF export.
    *   **VS Code `code` command**: Optional, for opening folders automatically.

3.  **Configuration:**
    Create a `.env` file in the project root with your Google AI API key:
    ```bash
    GOOGLE_API_KEY=your_api_key_here
    ```
    
    Get your API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Usage

### Interactive Mode (Recommended)
Simply run the CLI without arguments to start the interactive launcher:
```bash
deckbot
```
You can select an existing deck or create a new one.

### Commands

*   **Resume Session**: Pick up exactly where you left off.
    ```bash
    deckbot --continue
    ```

*   **Create a Deck**:
    ```bash
    deckbot create my-deck --description "A demo deck"
    ```

*   **Use Templates**:
    List available templates:
    ```bash
    deckbot templates list
    ```
    Create from a template:
    ```bash
    deckbot create my-startup --template Simple
    ```

*   **Start the Assistant**:
    ```bash
    deckbot load my-deck
    ```

*   **Preview Deck**:
    ```bash
    deckbot preview my-deck
    ```

### In the Assistant (REPL)

*   **Chat**: "Add a slide about our Q3 goals."
*   **Generate Images**: "Generate a futuristic cityscape image for the title slide." (or use `/image <prompt>`)
*   **Show Work**: "Show me the deck" (prints a summary).
*   **Preview**: "Preview the presentation" (opens the HTML preview).
*   **Export**: "Export to PDF" (saves a PDF version).

### Web Mode
Prefer a visual interface? Launch the web UI with color themes, visual image selection, and live preview.

```bash
deckbot --web
```
Then open `http://localhost:5555` in your browser.

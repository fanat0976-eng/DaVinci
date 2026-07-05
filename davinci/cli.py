"""DaVinci CLI — your local AI coding assistant."""

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config
from .coordinator import Coordinator

console = Console()


def check_ollama(config: Config) -> bool:
    """Check if Ollama is available."""
    from .llm.client import LLMClient
    client = LLMClient(config.llm.base_url, config.llm.model)
    if client.is_available():
        return True

    console.print("[red]Ollama is not running or model not found.[/red]")
    console.print(f"[dim]Expected: {config.llm.model} at {config.llm.base_url}[/dim]")
    console.print("[yellow]Start Ollama: ollama serve[/yellow]")
    return False


def cmd_init(project_dir: Path):
    """Initialize DaVinci in a project."""
    config = Config(project_dir=project_dir)
    config.save()
    console.print(f"[green]DaVinci initialized in {project_dir}[/green]")
    console.print(f"[dim]Config: {config.davinci_dir / 'config.yaml'}[/dim]")


def cmd_index(project_dir: Path):
    """Index project for RAG."""
    config = Config.load(project_dir)

    if not check_ollama(config):
        sys.exit(1)

    console.print("[bold blue]Indexing project for RAG...[/bold blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Indexing...", total=None)
        coordinator = Coordinator(config)
        count = coordinator.index()
        progress.update(task_id, completed=True)

    console.print(f"[green]Indexed {count} chunks[/green]")
    stats = coordinator.retriever.stats()
    console.print(f"[dim]Total chunks in store: {stats['chunks']}[/dim]")


def cmd_run(task: str, project_dir: Path, stream: bool = True):
    """Run a task."""
    config = Config.load(project_dir)

    if not check_ollama(config):
        sys.exit(1)

    coordinator = Coordinator(config)

    console.print(Panel(
        f"[bold cyan]{task}[/bold cyan]",
        title="DaVinci",
        subtitle="AI Coding Agent",
        border_style="blue",
    ))

    if stream:
        # Stream response
        with console.status("[bold green]Thinking...", spinner="dots"):
            pass  # Status will show while streaming

        console.print()
        full_response = ""
        for token in coordinator.run_stream(task):
            console.print(token, end="", highlight=False)
            full_response += token
        console.print()

        # Parse and show actions
        actions = coordinator.coder.parse_actions(full_response)
        if actions:
            console.print()
            for action in actions:
                if action["type"] == "write":
                    console.print(f"[green]  + Write: {action['path']}[/green]")
                elif action["type"] == "edit":
                    console.print(f"[yellow]  ~ Edit: {action['path']}[/yellow]")
                elif action["type"] == "bash":
                    console.print(f"[blue]  $ Bash: {action['command'][:60]}...[/blue]")
    else:
        # Non-streaming
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task_id = progress.add_task("Working...", total=None)
            result = coordinator.run(task)
            progress.update(task_id, completed=True)

        console.print(Markdown(result["response"]))
        if result["actions"]:
            console.print()
            for action in result["actions"]:
                if action["type"] == "write":
                    console.print(f"[green]  + Write: {action['path']}[/green]")
                elif action["type"] == "edit":
                    console.print(f"[yellow]  ~ Edit: {action['path']}[/yellow]")


def cmd_models(config: Config):
    """List available Ollama models."""
    import requests
    try:
        resp = requests.get(f"{config.llm.base_url}/api/tags", timeout=5)
        models = resp.json().get("models", [])
        console.print("[bold]Available models:[/bold]")
        for m in models:
            name = m["name"]
            size = m.get("size", 0) / (1024**3)
            marker = " [green](active)[/green]" if config.llm.model in name else ""
            console.print(f"  {name} ({size:.1f}GB){marker}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="davinci",
        description="DaVinci — Local AI Coding Agent",
    )
    parser.add_argument("task", nargs="?", help="Task to execute")
    parser.add_argument("--init", action="store_true", help="Initialize DaVinci in current directory")
    parser.add_argument("--index", action="store_true", help="Index project for RAG")
    parser.add_argument("--models", action="store_true", help="List available Ollama models")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    parser.add_argument("--dir", type=str, default=".", help="Project directory")

    args = parser.parse_args()
    project_dir = Path(args.dir).resolve()

    if args.init:
        cmd_init(project_dir)
    elif args.index:
        cmd_index(project_dir)
    elif args.models:
        config = Config.load(project_dir)
        cmd_models(config)
    elif args.task:
        cmd_run(args.task, project_dir, stream=not args.no_stream)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""DaVinci CLI — your local AI coding assistant with Rich TUI."""

import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeElapsedColumn, MofNCompleteColumn,
)
from rich.live import Live
from rich.tree import Tree
from rich.columns import Columns
from rich.markdown import Markdown

from .config import Config
from .coordinator import Coordinator

console = Console()

# Agent colors
AGENT_COLORS = {
    "coordinator": "blue",
    "architect": "magenta",
    "coder": "green",
    "tester": "yellow",
    "reviewer": "red",
}

AGENT_ICONS = {
    "coordinator": "\u2699",
    "architect": "\U0001f3d7",
    "coder": "\U0001f4bb",
    "tester": "\u2705",
    "reviewer": "\U0001f50d",
}


def check_ollama(config: Config) -> bool:
    """Check if Ollama is available."""
    from .llm.client import LLMClient
    client = LLMClient(config.llm.base_url, config.llm.model)
    if client.is_available():
        return True

    console.print(Panel(
        "[red]Ollama is not running or model not found![/red]\n\n"
        f"  Model: [cyan]{config.llm.model}[/cyan]\n"
        f"  URL: [dim]{config.llm.base_url}[/dim]\n\n"
        "[yellow]Start Ollama: ollama serve[/yellow]",
        title="\u26a0 Ollama",
        border_style="red",
    ))
    return False


def cmd_init(project_dir: Path):
    """Initialize DaVinci in a project."""
    config = Config(project_dir=project_dir)
    config.save()

    tree = Tree(f"\U0001f3b5 DaVinci initialized in [cyan]{project_dir}[/cyan]")
    tree.add(f"Config: [dim]{config.davinci_dir / 'config.yaml'}[/dim]")
    tree.add(f"Model: [cyan]{config.llm.model}[/cyan]")
    tree.add(f"LLM URL: [dim]{config.llm.base_url}[/dim]")
    console.print(tree)


def cmd_index(project_dir: Path):
    """Index project for RAG."""
    config = Config.load(project_dir)

    if not check_ollama(config):
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task1 = progress.add_task("[cyan]Scanning files...", total=None)
        coordinator = Coordinator(config)

        # Simulate scanning progress
        time.sleep(0.3)
        progress.update(task1, description="[cyan]Embedding chunks...")
        count = coordinator.index()
        progress.update(task1, completed=count, total=count)

    stats = coordinator.retriever.stats()

    table = Table(title="\U0001f4da RAG Index", border_style="blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Chunks indexed", str(stats["chunks"]))
    table.add_row("Status", "[green]Ready[/green]" if stats["indexed"] else "[red]Not indexed[/red]")
    console.print(table)


def _print_routing(task: str, agent_name: str):
    """Show routing decision."""
    color = AGENT_COLORS.get(agent_name, "white")
    icon = AGENT_ICONS.get(agent_name, "?")
    console.print(f"\n  {icon} Routed to: [bold {color}]{agent_name.upper()}[/bold {color}]")


def _print_actions(actions: list[dict]):
    """Show executed actions in a tree."""
    if not actions:
        return

    tree = Tree("\U0001f4c1 Actions")
    for action in actions:
        if action["type"] == "write":
            tree.add(f"[green]+\uFE0F Write: {action['path']}[/green]")
        elif action["type"] == "edit":
            tree.add(f"[yellow]~\uFE0F Edit: {action['path']}[/yellow]")
        elif action["type"] == "bash":
            tree.add(f"[blue]$\uFE0F Bash: {action['command'][:50]}...[/blue]")
    console.print(tree)


def cmd_run(task: str, project_dir: Path, stream: bool = True, force_agent: str | None = None):
    """Run a task with full TUI."""
    config = Config.load(project_dir)

    if not check_ollama(config):
        sys.exit(1)

    coordinator = Coordinator(config)

    # Header panel
    agent_label = force_agent or "auto"
    console.print(Panel(
        f"[bold]{task}[/bold]",
        title="\U0001f3a8 DaVinci",
        subtitle=f"Agent: [cyan]{agent_label}[/cyan] | Model: [dim]{config.llm.model}[/dim]",
        border_style="blue",
        padding=(0, 2),
    ))

    if stream:
        # Determine agent
        agent_name = force_agent or coordinator.route(task)
        agent = getattr(coordinator, agent_name)
        _print_routing(task, agent_name)

        # Build context
        context = coordinator.context.gather(task)
        rag_info = ""
        if coordinator.retriever.is_indexed():
            rag_context = coordinator.retriever.get_context(task, top_k=3)
            context += f"\n\n{rag_context}"
            rag_info = " | RAG: [green]active[/green]"
        else:
            rag_info = " | RAG: [dim]not indexed[/dim]"

        messages = agent.build_messages(task, context)

        # Streaming response with live status
        console.print()
        full_response = ""
        with Live(console=console, refresh_per_second=10) as live:
            token_count = 0
            for token in coordinator.llm.chat_stream(messages):
                full_response += token
                token_count += 1

                # Show live status
                status = Text()
                status.append(f"\U0001f4ac Generating... ", style="cyan")
                status.append(f"{token_count} tokens", style="dim")
                status.append(rag_info, style="dim")
                live.update(status)

            # Final status
            live.update(Text(f"\u2705 Done — {token_count} tokens{rag_info}", style="green"))

        # Show response
        console.print()
        console.print(Panel(
            Markdown(full_response) if full_response.strip() else Text("(no response)"),
            border_style="dim",
            padding=(0, 1),
        ))

        # Parse and execute actions
        actions = agent.parse_actions(full_response)
        if actions:
            console.print()
            executed = []
            for action in actions:
                result = agent.execute_action(action)
                executed.append((action, result))

            # Show results in table
            table = Table(title="\U0001f680 Executed Actions", border_style="green")
            table.add_column("Type", style="bold")
            table.add_column("Target")
            table.add_column("Status")

            for action, result in executed:
                if action["type"] == "write":
                    status = "[green]\u2705 OK[/green]" if result["ok"] else f"[red]\u274C {result.get('error', '?')}[/red]"
                    table.add_row("Write", action["path"], status)
                elif action["type"] == "edit":
                    status = "[green]\u2705 OK[/green]" if result["ok"] else f"[red]\u274C {result.get('error', '?')}[/red]"
                    table.add_row("Edit", action["path"], status)
                elif action["type"] == "bash":
                    table.add_row("Bash", action["command"][:40], "[dim]run[/dim]")

            console.print(table)
    else:
        # Non-streaming with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Step 1: Routing
            task_route = progress.add_task("[cyan]Routing...", total=1)
            agent_name = force_agent or coordinator.route(task)
            progress.update(task_route, completed=1, description=f"[cyan]Agent: {agent_name}")

            # Step 2: Execute
            task_exec = progress.add_task(f"[green]{agent_name} working...", total=None)
            result = coordinator.run(task, force_agent=force_agent)
            progress.update(task_exec, completed=1, description="[green]Done")

        # Show results
        console.print()
        console.print(Panel(
            Markdown(result["response"]) if result["response"].strip() else Text("(no response)"),
            title=f"\U0001f4ac {agent_name.upper()} Response",
            border_style="dim",
        ))

        if result["actions"]:
            _print_actions(result["actions"])


def cmd_models(config: Config):
    """List available Ollama models."""
    import requests
    try:
        resp = requests.get(f"{config.llm.base_url}/api/tags", timeout=5)
        models = resp.json().get("models", [])

        table = Table(title="\U0001f916 Available Models", border_style="blue")
        table.add_column("Model", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Status")

        for m in models:
            name = m["name"]
            size = m.get("size", 0) / (1024**3)
            is_active = config.llm.model in name
            status = "[green]\u2B50 active[/green]" if is_active else "[dim]available[/dim]"
            table.add_row(name, f"{size:.1f} GB", status)

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def cmd_status(project_dir: Path):
    """Show project status."""
    config = Config.load(project_dir)

    # Check Ollama
    from .llm.client import LLMClient
    client = LLMClient(config.llm.base_url, config.llm.model)
    ollama_ok = client.is_available()

    # Check RAG
    from .rag.retriever import Retriever
    retriever = Retriever(project_dir, config.llm.base_url)
    rag_stats = retriever.stats()

    # Check decisions
    from .memory.decisions import DecisionsMemory
    decisions = DecisionsMemory(config.davinci_dir)

    table = Table(title="\U0001f4cb DaVinci Status", border_style="blue")
    table.add_column("Component", style="cyan")
    table.add_column("Status")

    table.add_row("Project", f"[dim]{project_dir}[/dim]")
    table.add_row("Ollama", "[green]\u2705 Connected[/green]" if ollama_ok else "[red]\u274C Not connected[/red]")
    table.add_row("Model", f"[cyan]{config.llm.model}[/cyan]")
    table.add_row("RAG", f"[green]{rag_stats['chunks']} chunks[/green]" if rag_stats["indexed"] else "[dim]Not indexed[/dim]")

    # Count decisions
    dec_content = decisions.read()
    dec_count = dec_content.count("## [")
    table.add_row("Decisions", f"[yellow]{dec_count}[/yellow]")

    console.print(table)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="davinci",
        description="\U0001f3a8 DaVinci — Local AI Coding Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  davinci --init                      Initialize in current directory
  davinci --index                     Index project for RAG
  davinci "Add email validation"      Run task with auto-routing
  davinci --agent coder "Fix bug"     Force specific agent
  davinci --status                    Show project status
  davinci --models                    List Ollama models
        """,
    )
    parser.add_argument("task", nargs="?", help="Task to execute")
    parser.add_argument("--init", action="store_true", help="Initialize DaVinci")
    parser.add_argument("--index", action="store_true", help="Index project for RAG")
    parser.add_argument("--status", action="store_true", help="Show project status")
    parser.add_argument("--models", action="store_true", help="List Ollama models")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("--agent", type=str, choices=["coder", "architect", "tester", "reviewer"],
                        help="Force specific agent")
    parser.add_argument("--dashboard", action="store_true", help="Start web dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Dashboard port")
    parser.add_argument("--dir", type=str, default=".", help="Project directory")

    args = parser.parse_args()
    project_dir = Path(args.dir).resolve()

    if args.dashboard:
        from .dashboard import cmd_dashboard
        cmd_dashboard(project_dir, args.port)
    elif args.init:
        cmd_init(project_dir)
    elif args.index:
        cmd_index(project_dir)
    elif args.status:
        cmd_status(project_dir)
    elif args.models:
        config = Config.load(project_dir)
        cmd_models(config)
    elif args.task:
        cmd_run(args.task, project_dir, stream=not args.no_stream, force_agent=args.agent)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

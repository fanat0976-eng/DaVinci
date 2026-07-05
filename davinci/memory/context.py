"""Context manager — gathers relevant context for agents."""

from pathlib import Path


class ContextManager:
    """Gathers and formats context for agent prompts."""

    def __init__(self, project_dir: Path, decisions):
        self.project_dir = project_dir
        self.decisions = decisions

    def gather(self, task: str, focus_files: list[str] | None = None) -> str:
        """Gather context relevant to the task."""
        parts = []

        # 1. Project structure overview
        structure = self._get_project_structure()
        if structure:
            parts.append(f"## Project Structure\n```\n{structure}\n```")

        # 2. Focus files (if specified)
        if focus_files:
            for f in focus_files:
                content = self._read_file(f)
                if content:
                    parts.append(f"## File: {f}\n```\n{content[:5000]}\n```")

        # 3. Recent decisions
        decisions = self.decisions.read_recent(3)
        if decisions and len(decisions) > 100:
            parts.append(f"## Recent Decisions\n{decisions}")

        return "\n\n".join(parts)

    def _get_project_structure(self, max_depth: int = 2) -> str:
        """Get project directory structure."""
        lines = []
        count = 0
        for item in sorted(self.project_dir.rglob("*")):
            if count > 50:
                lines.append("  ... (truncated)")
                break
            rel = item.relative_to(self.project_dir)
            depth = len(rel.parts) - 1
            if depth > max_depth:
                continue
            if any(part.startswith(".") for part in rel.parts):
                continue
            if any(part in ("node_modules", "__pycache__", "venv", ".git", "dist", "build")
                   for part in rel.parts):
                continue
            indent = "  " * depth
            name = item.name + "/" if item.is_dir() else item.name
            lines.append(f"{indent}{name}")
            count += 1
        return "\n".join(lines)

    def _read_file(self, path: str) -> str | None:
        """Try to read a file."""
        try:
            p = self.project_dir / path
            if p.exists() and p.is_file():
                return p.read_text(encoding="utf-8")
        except Exception:
            pass
        return None

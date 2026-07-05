"""Decisions memory — shared team brain (like Squad's decisions.md)."""

from datetime import datetime
from pathlib import Path


class DecisionsMemory:
    """Manages the decisions.md file — shared memory for agents."""

    def __init__(self, davinci_dir: Path):
        self.file_path = davinci_dir / "decisions.md"
        self._ensure_file()

    def _ensure_file(self):
        """Create decisions.md if it doesn't exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text(
                "# DaVinci Team Decisions\n\n"
                "> Shared memory for all agents. Every architectural decision is recorded here.\n\n",
                encoding="utf-8",
            )

    def add(self, title: str, content: str, agent: str = "coordinator"):
        """Add a new decision entry."""
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        entry = (
            f"\n## [{timestamp}] {title}\n"
            f"**Agent**: {agent}\n\n"
            f"{content}\n"
        )
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def read(self) -> str:
        """Read all decisions."""
        return self.file_path.read_text(encoding="utf-8")

    def read_recent(self, n: int = 5) -> str:
        """Read the last N decisions."""
        content = self.read()
        sections = content.split("\n## ")
        if len(sections) <= 1:
            return content
        # First section is header, rest are decisions
        header = sections[0]
        recent = sections[-n:]
        return header + "\n## ".join(recent)

    def clear(self):
        """Clear all decisions (keep header)."""
        self.file_path.write_text(
            "# DaVinci Team Decisions\n\n"
            "> Shared memory for all agents. Every architectural decision is recorded here.\n\n",
            encoding="utf-8",
        )

"""Repo indexer — scans and chunks project files for RAG."""

from pathlib import Path
from dataclasses import dataclass


@dataclass
class Chunk:
    """A chunk of code/text from a file."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
        }


class RepoIndexer:
    """Indexes project files into chunks for embedding."""

    EXTENSION_MAP = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "tsx", ".jsx": "jsx", ".rs": "rust", ".go": "go",
        ".java": "java", ".kt": "kotlin", ".cpp": "cpp", ".c": "c",
        ".h": "c", ".hpp": "cpp", ".html": "html", ".css": "css",
        ".scss": "scss", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        ".toml": "toml", ".md": "markdown", ".txt": "text",
        ".sh": "bash", ".bat": "batch", ".ps1": "powershell",
        ".sql": "sql", ".xml": "xml",
    }

    SKIP_DIRS = {
        ".git", ".davinci", "__pycache__", "node_modules",
        "venv", ".venv", "dist", "build", ".pytest_cache",
        "egg-info", ".mypy_cache", ".ruff_cache",
    }

    def __init__(self, project_dir: Path, chunk_size: int = 50, chunk_overlap: int = 10):
        self.project_dir = project_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def index(self) -> list[Chunk]:
        """Index all project files into chunks."""
        chunks = []
        for file_path in self._scan_files():
            file_chunks = self._chunk_file(file_path)
            chunks.extend(file_chunks)
        return chunks

    def _scan_files(self) -> list[Path]:
        """Scan project for indexable files."""
        files = []
        for item in sorted(self.project_dir.rglob("*")):
            if not item.is_file():
                continue
            # Skip ignored directories
            parts = item.relative_to(self.project_dir).parts
            if any(part in self.SKIP_DIRS for part in parts):
                continue
            if any(part.startswith(".") for part in parts[:-1]):
                continue
            # Check extension
            if item.suffix.lower() in self.EXTENSION_MAP:
                files.append(item)
        return files

    def _chunk_file(self, file_path: Path) -> list[Chunk]:
        """Split a file into chunks."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            return []

        lines = content.split("\n")
        if not lines:
            return []

        language = self.EXTENSION_MAP.get(file_path.suffix.lower(), "text")
        rel_path = str(file_path.relative_to(self.project_dir))

        chunks = []
        start = 0
        while start < len(lines):
            end = min(start + self.chunk_size, len(lines))
            chunk_lines = lines[start:end]
            chunk_content = "\n".join(chunk_lines)

            if chunk_content.strip():  # Skip empty chunks
                chunks.append(Chunk(
                    content=chunk_content,
                    file_path=rel_path,
                    start_line=start + 1,
                    end_line=end,
                    language=language,
                ))

            next_start = end - self.chunk_overlap
            if next_start <= start or next_start >= len(lines):
                break
            start = next_start

        return chunks

    def get_file_content(self, file_path: str) -> str | None:
        """Read a specific file's content."""
        try:
            full_path = self.project_dir / file_path
            if full_path.exists() and full_path.is_file():
                return full_path.read_text(encoding="utf-8")
        except Exception:
            pass
        return None

    def get_structure(self, max_depth: int = 3) -> str:
        """Get project structure as text."""
        lines = []
        for item in sorted(self.project_dir.rglob("*")):
            rel = item.relative_to(self.project_dir)
            depth = len(rel.parts) - 1
            if depth > max_depth:
                continue
            parts = rel.parts
            if any(part in self.SKIP_DIRS for part in parts):
                continue
            if any(part.startswith(".") for part in parts[:-1]):
                continue
            indent = "  " * depth
            name = item.name + "/" if item.is_dir() else item.name
            lines.append(f"{indent}{name}")
        return "\n".join(lines[:100])  # Limit to 100 lines

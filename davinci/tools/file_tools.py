"""File tools for DaVinci agents."""

import os
import subprocess
from pathlib import Path


class FileTools:
    """File system operations for agents."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def _resolve(self, path: str) -> Path:
        """Resolve path relative to project directory with containment check."""
        p = Path(path)
        if not p.is_absolute():
            p = self.project_dir / p
        resolved = p.resolve()
        # Security: ensure resolved path is within project directory
        if not resolved.is_relative_to(self.project_dir.resolve()):
            raise ValueError(f"Path traversal blocked: {path} resolves outside project")
        return resolved

    def read_file(self, path: str) -> str:
        """Read file content."""
        resolved = self._resolve(path)
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not resolved.is_file():
            raise IsADirectoryError(f"Not a file: {path}")
        return resolved.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> str:
        """Write content to file, creating directories if needed."""
        resolved = self._resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return str(resolved)

    def edit_file(self, path: str, old: str, new: str) -> str:
        """Replace old text with new text in file."""
        resolved = self._resolve(path)
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = resolved.read_text(encoding="utf-8")
        if old not in content:
            raise ValueError(f"Text not found in {path}:\n{old[:100]}...")

        new_content = content.replace(old, new, 1)
        resolved.write_text(new_content, encoding="utf-8")
        return str(resolved)

    def list_files(self, pattern: str = "**/*") -> list[str]:
        """List files matching pattern."""
        results = []
        for p in self.project_dir.glob(pattern):
            if p.is_file():
                # Skip hidden dirs and common ignores
                rel = p.relative_to(self.project_dir)
                parts = rel.parts
                if any(part.startswith(".") for part in parts[:-1]):
                    continue
                if any(part in ("node_modules", "__pycache__", "venv", ".git", "dist", "build")
                       for part in parts):
                    continue
                results.append(str(rel))
        return sorted(results)

    BLOCKED_COMMANDS = [
        "rm -rf", "rmdir /s", "Format-Volume", "Remove-Item -Recurse",
        "del /f /s /q", "cipher /w", "shutdown", "restart-computer",
    ]

    def run_bash(self, command: str, timeout: int = 30) -> str:
        """Run a bash command and return output."""
        # Security: block dangerous commands
        cmd_lower = command.lower().strip()
        for blocked in self.BLOCKED_COMMANDS:
            if blocked.lower() in cmd_lower:
                return f"[BLOCKED] Command contains dangerous pattern: {blocked}"

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            return output.strip()
        except subprocess.TimeoutExpired:
            return f"[TIMEOUT] Command timed out after {timeout}s"
        except Exception as e:
            return f"[ERROR] {e}"

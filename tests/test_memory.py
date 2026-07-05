"""Tests for memory system."""

import tempfile
from pathlib import Path

from davinci.memory.decisions import DecisionsMemory
from davinci.memory.context import ContextManager


def test_decisions_create_file():
    """Decisions memory creates file on init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = DecisionsMemory(Path(tmpdir))
        assert mem.file_path.exists()
        content = mem.read()
        assert "DaVinci Team Decisions" in content


def test_decisions_add_and_read():
    """Can add and read decisions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = DecisionsMemory(Path(tmpdir))
        mem.add("Test Decision", "- Use Python\n- Use SQLite")
        content = mem.read()
        assert "Test Decision" in content
        assert "Use Python" in content


def test_decisions_read_recent():
    """Read recent decisions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = DecisionsMemory(Path(tmpdir))
        for i in range(10):
            mem.add(f"Decision {i}", f"Content {i}")
        recent = mem.read_recent(3)
        assert "Decision 9" in recent
        assert "Decision 8" in recent


def test_decisions_clear():
    """Clear decisions keeps header."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = DecisionsMemory(Path(tmpdir))
        mem.add("Test", "Content")
        mem.clear()
        content = mem.read()
        assert "DaVinci Team Decisions" in content
        assert "Test" not in content


def test_context_gather():
    """Context manager gathers project info."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        (project / "main.py").write_text("print('hello')")
        (project / "utils.py").write_text("def helper(): pass")

        mem = DecisionsMemory(project / ".davinci")
        ctx = ContextManager(project, mem)

        context = ctx.gather("test task")
        assert "main.py" in context
        assert "utils.py" in context


def test_context_with_focus_files():
    """Context includes focus file contents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        (project / "app.py").write_text("from flask import Flask")

        mem = DecisionsMemory(project / ".davinci")
        ctx = ContextManager(project, mem)

        context = ctx.gather("task", focus_files=["app.py"])
        assert "from flask import Flask" in context

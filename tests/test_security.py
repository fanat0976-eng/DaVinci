"""Tests for security fixes."""

import tempfile
from pathlib import Path

from davinci.tools.file_tools import FileTools
from davinci.agents.base import BaseAgent
from davinci.agents.coder import CoderAgent
from unittest.mock import MagicMock


def test_path_traversal_blocked():
    """Path traversal outside project is blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        try:
            tools.write_file("../../etc/passwd", "evil")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "traversal" in str(e).lower()


def test_path_traversal_absolute_blocked():
    """Absolute paths outside project are blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        try:
            tools.write_file("/tmp/evil.py", "evil")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "traversal" in str(e).lower()


def test_path_traversal_relative_ok():
    """Relative paths within project are allowed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        tools.write_file("src/module.py", "print('ok')")
        assert Path(tmpdir, "src/module.py").exists()


def test_bash_dangerous_blocked():
    """Dangerous bash commands are blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        result = tools.run_bash("rm -rf /")
        assert "BLOCKED" in result

        result = tools.run_bash("Format-Volume -DriveLetter C")
        assert "BLOCKED" in result


def test_bash_safe_allowed():
    """Safe bash commands are allowed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        result = tools.run_bash("echo hello")
        assert "hello" in result


def test_history_limit():
    """History is limited to MAX_HISTORY."""
    with tempfile.TemporaryDirectory() as tmpdir:
        llm = MagicMock()
        llm.chat.return_value = "response"
        agent = CoderAgent(llm, Path(tmpdir))

        # Run many tasks
        for i in range(15):
            agent.run(f"task {i}")

        # History should be limited
        assert len(agent.history) <= BaseAgent.MAX_HISTORY * 2


def test_clean_content_wrapped():
    """_clean_content removes wrapping code blocks."""
    content = '```python\nprint("hello")\n```'
    cleaned = BaseAgent._clean_content(content)
    assert cleaned == 'print("hello")'


def test_clean_content_partial():
    """_clean_content preserves partial code blocks."""
    content = 'Some text with ```code``` inside'
    cleaned = BaseAgent._clean_content(content)
    assert "```code```" in cleaned


def test_clean_content_no_blocks():
    """_clean_content passes plain text."""
    content = "Just plain text"
    cleaned = BaseAgent._clean_content(content)
    assert cleaned == "Just plain text"

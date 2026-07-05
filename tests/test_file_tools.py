"""Tests for file tools."""

import tempfile
from pathlib import Path

from davinci.tools.file_tools import FileTools


def test_write_and_read():
    """Write and read a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        tools.write_file("test.py", "print('hello')")
        content = tools.read_file("test.py")
        assert content == "print('hello')"


def test_edit_file():
    """Edit a file by replacing text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        tools.write_file("test.py", "old code")
        tools.edit_file("test.py", "old code", "new code")
        assert tools.read_file("test.py") == "new code"


def test_edit_file_not_found_text():
    """Edit raises error if text not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        tools.write_file("test.py", "content")
        try:
            tools.edit_file("test.py", "nonexistent", "new")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


def test_list_files():
    """List files in project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        tools.write_file("a.py", "x")
        tools.write_file("b.py", "y")
        tools.write_file(".hidden/secret", "z")
        tools.write_file("__pycache__/cache.pyc", "w")

        files = tools.list_files()
        assert "a.py" in files
        assert "b.py" in files
        assert ".hidden/secret" not in files
        assert "__pycache__/cache.pyc" not in files


def test_read_file_not_found():
    """Read raises error for missing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        try:
            tools.read_file("nonexistent.py")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass


def test_create_nested_dirs():
    """Write creates nested directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tools = FileTools(Path(tmpdir))
        tools.write_file("src/module/file.py", "x")
        assert Path(tmpdir, "src/module/file.py").exists()

"""Tests for coordinator and agents."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from davinci.config import Config
from davinci.coordinator import Coordinator
from davinci.agents.coder import CoderAgent


def test_coder_system_prompt():
    """Coder agent has a proper system prompt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        llm = MagicMock()
        agent = CoderAgent(llm, Path(tmpdir))
        prompt = agent.system_prompt()
        assert "DaVinci Coder" in prompt
        assert "[FILE:" in prompt


def test_parse_actions_file():
    """Parse file write action from response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        llm = MagicMock()
        agent = CoderAgent(llm, Path(tmpdir))

        response = '[FILE: test.py]\n```python\nprint("hello")\n```'
        actions = agent.parse_actions(response)
        assert len(actions) == 1
        assert actions[0]["type"] == "write"
        assert actions[0]["path"] == "test.py"
        assert "print" in actions[0]["content"]


def test_parse_actions_edit():
    """Parse edit action from response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        llm = MagicMock()
        agent = CoderAgent(llm, Path(tmpdir))

        response = '[EDIT: test.py]\nold code\n->\nnew code'
        actions = agent.parse_actions(response)
        assert len(actions) == 1
        assert actions[0]["type"] == "edit"
        assert actions[0]["old"] == "old code"
        assert actions[0]["new"] == "new code"


def test_parse_actions_bash():
    """Parse bash action from response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        llm = MagicMock()
        agent = CoderAgent(llm, Path(tmpdir))

        response = '[BASH]\necho hello'
        actions = agent.parse_actions(response)
        assert len(actions) == 1
        assert actions[0]["type"] == "bash"
        assert actions[0]["command"] == "echo hello"


def test_parse_actions_multiple():
    """Parse multiple actions from response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        llm = MagicMock()
        agent = CoderAgent(llm, Path(tmpdir))

        response = """[FILE: a.py]
print("a")

[FILE: b.py]
print("b")

[BASH]
echo done"""

        actions = agent.parse_actions(response)
        assert len(actions) == 3
        assert actions[0]["type"] == "write"
        assert actions[1]["type"] == "write"
        assert actions[2]["type"] == "bash"


def test_execute_action_write():
    """Execute write action creates file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        llm = MagicMock()
        agent = CoderAgent(llm, Path(tmpdir))

        action = {"type": "write", "path": "test.py", "content": "print('hello')"}
        result = agent.execute_action(action)
        assert result["ok"]
        assert Path(tmpdir, "test.py").exists()


def test_coordinator_init():
    """Coordinator initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(project_dir=Path(tmpdir))
        coordinator = Coordinator(config)
        assert coordinator.coder is not None
        assert coordinator.llm is not None

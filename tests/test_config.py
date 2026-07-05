"""Tests for DaVinci config."""

import tempfile
from pathlib import Path

from davinci.config import Config, LLMConfig


def test_config_defaults():
    """Config has correct defaults."""
    config = Config()
    assert config.llm.model == "qwen2.5:14b"
    assert config.llm.base_url == "http://127.0.0.1:11434"
    assert config.agent.max_iterations == 5


def test_config_load_creates_davinci_dir():
    """Loading config creates .davinci directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config.load(Path(tmpdir))
        assert config.davinci_dir.exists()
        assert config.davinci_dir.name == ".davinci"


def test_config_save_and_load():
    """Config saves and loads correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        config = Config(project_dir=project)
        config.llm.model = "deepseek-coder:6.7b"
        config.save()

        loaded = Config.load(project)
        assert loaded.llm.model == "deepseek-coder:6.7b"

"""DaVinci configuration."""

import os
from pathlib import Path
from dataclasses import dataclass, field

import yaml


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:14b"
    embedding_model: str = "nomic-embed-text"
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: int = 120


@dataclass
class AgentConfig:
    """Agent behavior configuration."""
    max_iterations: int = 5
    max_file_size: int = 100_000  # chars
    allowed_extensions: list[str] = field(default_factory=lambda: [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go",
        ".java", ".kt", ".cpp", ".c", ".h", ".hpp",
        ".html", ".css", ".scss", ".json", ".yaml", ".yml",
        ".toml", ".md", ".txt", ".sh", ".bat", ".ps1",
        ".sql", ".xml", ".env", ".gitignore",
    ])


@dataclass
class Config:
    """Main DaVinci configuration."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    project_dir: Path = field(default_factory=lambda: Path.cwd())
    davinci_dir: Path = field(default=None)

    def __post_init__(self):
        if self.davinci_dir is None:
            self.davinci_dir = self.project_dir / ".davinci"
        self.davinci_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls, project_dir: Path | None = None) -> "Config":
        """Load config from project directory."""
        if project_dir is None:
            project_dir = Path.cwd()

        config = cls(project_dir=project_dir)

        # Try loading from .davinci/config.yaml
        config_file = config.davinci_dir / "config.yaml"
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                if "llm" in data:
                    for k, v in data["llm"].items():
                        if hasattr(config.llm, k):
                            setattr(config.llm, k, v)
                if "agent" in data:
                    for k, v in data["agent"].items():
                        if hasattr(config.agent, k):
                            setattr(config.agent, k, v)
            except Exception:
                pass

        # Environment overrides
        if url := os.environ.get("OLLAMA_BASE_URL"):
            config.llm.base_url = url
        if model := os.environ.get("DAVINCI_MODEL"):
            config.llm.model = model

        return config

    def save(self):
        """Save config to .davinci/config.yaml."""
        config_file = self.davinci_dir / "config.yaml"
        data = {
            "llm": {
                "base_url": self.llm.base_url,
                "model": self.llm.model,
                "embedding_model": self.llm.embedding_model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
            },
            "agent": {
                "max_iterations": self.agent.max_iterations,
            },
        }
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

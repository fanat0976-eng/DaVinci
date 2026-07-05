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

    def validate(self) -> list[str]:
        """Validate LLM config. Returns list of errors."""
        errors = []
        if not self.base_url.startswith("http"):
            errors.append(f"Invalid base_url: {self.base_url}")
        if not self.model:
            errors.append("Model name is required")
        if not (0.0 <= self.temperature <= 2.0):
            errors.append(f"Temperature must be 0.0-2.0, got {self.temperature}")
        if not (1 <= self.max_tokens <= 1_000_000):
            errors.append(f"max_tokens must be 1-1000000, got {self.max_tokens}")
        if not (1 <= self.timeout <= 600):
            errors.append(f"Timeout must be 1-600s, got {self.timeout}")
        return errors


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

    def validate(self) -> list[str]:
        """Validate agent config. Returns list of errors."""
        errors = []
        if not (1 <= self.max_iterations <= 20):
            errors.append(f"max_iterations must be 1-20, got {self.max_iterations}")
        if not (100 <= self.max_file_size <= 10_000_000):
            errors.append(f"max_file_size must be 100-10000000, got {self.max_file_size}")
        return errors


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
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid config.yaml: {e}")

        # Environment overrides
        if url := os.environ.get("OLLAMA_BASE_URL"):
            config.llm.base_url = url
        if model := os.environ.get("DAVINCI_MODEL"):
            config.llm.model = model

        # Validate
        errors = config.validate()
        if errors:
            raise ValueError(f"Config validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        return config

    def validate(self) -> list[str]:
        """Validate all config sections."""
        errors = []
        errors.extend(self.llm.validate())
        errors.extend(self.agent.validate())
        return errors

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

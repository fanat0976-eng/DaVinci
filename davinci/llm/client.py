"""Ollama LLM client for DaVinci.

IMPORTANT: Use requests, NOT httpx — httpx has a bug with Ollama.
Always use 127.0.0.1, NOT localhost — localhost is intercepted by proxy.
"""

import json
import requests
from typing import Generator


class LLMClient:
    """Ollama LLM client with streaming support."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: str = "qwen2.5:14b", timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(self, messages: list[dict], temperature: float = 0.3,
             max_tokens: int = 4096) -> str:
        """Send chat completion request and return full response."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def chat_stream(self, messages: list[dict], temperature: float = 0.3,
                    max_tokens: int = 4096) -> Generator[str, None, None]:
        """Stream chat completion response token by token."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
            stream=True,
        )
        resp.raise_for_status()

        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
                if chunk.get("done"):
                    break

    def embed(self, text: str) -> list[float]:
        """Get embedding vector for text."""
        payload = {
            "model": "nomic-embed-text",
            "input": text,
        }
        resp = requests.post(
            f"{self.base_url}/api/embeddings",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    def is_available(self) -> bool:
        """Check if Ollama is running and model is accessible."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                return False
            models = [m["name"] for m in resp.json().get("models", [])]
            return any(self.model in m for m in models)
        except Exception:
            return False

"""Ollama LLM client for DaVinci.

IMPORTANT: Use requests, NOT httpx — httpx has a bug with Ollama.
Always use 127.0.0.1, NOT localhost — localhost is intercepted by proxy.
"""

import json
import time
import requests
from typing import Generator


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, max_calls: int = 10, per_seconds: float = 1.0):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self.calls: list[float] = []

    def wait(self):
        """Wait if rate limit exceeded."""
        now = time.monotonic()
        # Remove old entries
        self.calls = [t for t in self.calls if now - t < self.per_seconds]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.per_seconds - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.calls.append(time.monotonic())


class LLMClient:
    """Ollama LLM client with streaming support and rate limiting."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: str = "qwen2.5:14b", timeout: int = 120,
                 rate_limit: int = 10):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._limiter = RateLimiter(max_calls=rate_limit, per_seconds=1.0)

    def chat(self, messages: list[dict], temperature: float = 0.3,
             max_tokens: int = 4096) -> str:
        """Send chat completion request and return full response."""
        self._limiter.wait()
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
        self._limiter.wait()
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

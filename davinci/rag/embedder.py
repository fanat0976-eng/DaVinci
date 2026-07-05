"""Embedder — generates embeddings using Ollama."""

import requests


class Embedder:
    """Generates embeddings using Ollama nomic-embed-text."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        payload = {
            "model": self.model,
            "input": text,
        }
        resp = requests.post(
            f"{self.base_url}/api/embeddings",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        # Ollama doesn't have native batch embedding,
        # so we do it sequentially
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
        return embeddings

    def is_available(self) -> bool:
        """Check if embedding model is available."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                return False
            models = [m["name"] for m in resp.json().get("models", [])]
            return any(self.model in m for m in models)
        except Exception:
            return False

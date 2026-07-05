"""Tests for Retriever and Embedder."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from davinci.rag.retriever import Retriever
from davinci.rag.embedder import Embedder


@patch("davinci.rag.embedder.requests.post")
def test_embedder_embed(mock_post):
    """Embedder returns embedding vector."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    embedder = Embedder()
    result = embedder.embed("test text")
    assert result == [0.1, 0.2, 0.3]


@patch("davinci.rag.embedder.requests.post")
def test_embedder_batch(mock_post):
    """Embedder batch returns multiple embeddings."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"embedding": [0.1, 0.2]}
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    embedder = Embedder()
    results = embedder.embed_batch(["text1", "text2"])
    assert len(results) == 2
    assert mock_post.call_count == 2


@patch("davinci.rag.embedder.requests.get")
def test_embedder_available(mock_get):
    """Embedder checks model availability."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "nomic-embed-text"}]}
    mock_get.return_value = mock_resp

    embedder = Embedder()
    assert embedder.is_available() is True


@patch("davinci.rag.retriever.Retriever.__init__", lambda self, *a, **k: None)
def test_retriever_stats_empty():
    """Retriever stats when empty."""
    retriever = Retriever.__new__(Retriever)
    retriever.store = MagicMock()
    retriever.store.count.return_value = 0

    stats = retriever.stats()
    assert stats["chunks"] == 0
    assert stats["indexed"] is False


@patch("davinci.rag.retriever.Retriever.__init__", lambda self, *a, **k: None)
def test_retriever_stats_indexed():
    """Retriever stats when indexed."""
    retriever = Retriever.__new__(Retriever)
    retriever.store = MagicMock()
    retriever.store.count.return_value = 42

    stats = retriever.stats()
    assert stats["chunks"] == 42
    assert stats["indexed"] is True


@patch("davinci.rag.retriever.Retriever.__init__", lambda self, *a, **k: None)
def test_retriever_get_context_empty():
    """Retriever context when no results."""
    retriever = Retriever.__new__(Retriever)
    retriever.store = MagicMock()
    retriever.embedder = MagicMock()
    retriever.embedder.embed.return_value = [0.1]
    retriever.store.search.return_value = []

    context = retriever.get_context("test query")
    assert context == ""


@patch("davinci.rag.retriever.Retriever.__init__", lambda self, *a, **k: None)
def test_retriever_get_context_results():
    """Retriever context with results."""
    retriever = Retriever.__new__(Retriever)
    retriever.store = MagicMock()
    retriever.embedder = MagicMock()
    retriever.embedder.embed.return_value = [0.1]

    from davinci.rag.store import SearchResult
    retriever.store.search.return_value = [
        SearchResult(content="def foo(): pass", file_path="a.py",
                    start_line=1, end_line=5, language="python", score=0.95),
    ]

    context = retriever.get_context("test query")
    assert "def foo(): pass" in context
    assert "a.py" in context

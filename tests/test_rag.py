"""Tests for RAG pipeline."""

import tempfile
from pathlib import Path

from davinci.rag.indexer import RepoIndexer, Chunk
from davinci.rag.store import VectorStore


def test_indexer_finds_files():
    """Indexer finds Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        (project / "main.py").write_text("def hello(): pass")
        (project / "utils.py").write_text("x = 1")
        (project / "readme.md").write_text("# Hello")

        indexer = RepoIndexer(project)
        chunks = indexer.index()
        assert len(chunks) >= 2
        files = {c.file_path for c in chunks}
        assert "main.py" in files


def test_indexer_skips_ignored():
    """Indexer skips __pycache__, .git, etc."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        (project / "main.py").write_text("x = 1")
        (project / "__pycache__").mkdir()
        (project / "__pycache__" / "cache.pyc").write_text("cached")
        (project / ".git").mkdir()
        (project / ".git" / "config").write_text("git config")

        indexer = RepoIndexer(project)
        chunks = indexer.index()
        files = {c.file_path for c in chunks}
        assert "main.py" in files
        assert "__pycache__/cache.pyc" not in files
        assert ".git/config" not in files


def test_indexer_chunking():
    """Indexer splits large files into chunks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        lines = [f"line {i}" for i in range(100)]
        (project / "big.py").write_text("\n".join(lines))

        indexer = RepoIndexer(project, chunk_size=20, chunk_overlap=5)
        chunks = indexer.index()
        assert len(chunks) > 1
        # Check chunks have proper line ranges
        for chunk in chunks:
            assert chunk.start_line >= 1
            assert chunk.end_line > chunk.start_line


def test_indexer_get_structure():
    """Indexer returns project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        (project / "src").mkdir()
        (project / "src" / "main.py").write_text("x = 1")
        (project / "tests").mkdir()
        (project / "tests" / "test_main.py").write_text("y = 2")

        indexer = RepoIndexer(project)
        structure = indexer.get_structure()
        assert "src/" in structure
        assert "main.py" in structure


def test_store_add_and_search():
    """Vector store add and search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(Path(tmpdir) / "test.db")

        # Add some chunks with fake embeddings
        store.add("def hello(): pass", "main.py", [1.0, 0.0, 0.0])
        store.add("x = 42", "utils.py", [0.0, 1.0, 0.0])
        store.add("print('hi')", "app.py", [0.0, 0.0, 1.0])

        # Search should find most similar
        results = store.search([1.0, 0.0, 0.0], top_k=1)
        assert len(results) == 1
        assert results[0].file_path == "main.py"
        assert results[0].score > 0.9


def test_store_file_filter():
    """Vector store file filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(Path(tmpdir) / "test.db")

        store.add("code in main", "src/main.py", [1.0, 0.0])
        store.add("code in test", "tests/test_main.py", [1.0, 0.0])

        # Filter to src only
        results = store.search([1.0, 0.0], file_filter="src")
        assert len(results) == 1
        assert "src" in results[0].file_path


def test_store_count():
    """Vector store count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(Path(tmpdir) / "test.db")
        assert store.count() == 0

        store.add("a", "a.py", [1.0])
        store.add("b", "b.py", [1.0])
        assert store.count() == 2


def test_store_clear():
    """Vector store clear."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(Path(tmpdir) / "test.db")
        store.add("a", "a.py", [1.0])
        store.clear()
        assert store.count() == 0


def test_chunk_to_dict():
    """Chunk to_dict."""
    chunk = Chunk(content="x = 1", file_path="a.py",
                  start_line=1, end_line=5, language="python")
    d = chunk.to_dict()
    assert d["content"] == "x = 1"
    assert d["language"] == "python"

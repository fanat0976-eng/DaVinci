"""Retriever — combines indexer, embedder, and store for RAG."""

from pathlib import Path

from .indexer import RepoIndexer
from .embedder import Embedder
from .store import VectorStore, SearchResult


class Retriever:
    """RAG retriever that indexes project and retrieves relevant context."""

    def __init__(self, project_dir: Path, base_url: str = "http://127.0.0.1:11434"):
        self.project_dir = project_dir
        self.indexer = RepoIndexer(project_dir)
        self.embedder = Embedder(base_url)
        self.store = VectorStore(project_dir / ".davinci" / "vectors.db")

    def index_project(self) -> int:
        """Index the entire project. Returns number of chunks indexed."""
        chunks = self.indexer.index()
        if not chunks:
            return 0

        # Clear existing index
        self.store.clear()

        # Embed and store chunks
        for chunk in chunks:
            embedding = self.embedder.embed(chunk.content)
            self.store.add(
                content=chunk.content,
                file_path=chunk.file_path,
                embedding=embedding,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                language=chunk.language,
            )

        return len(chunks)

    def retrieve(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Retrieve relevant chunks for a query."""
        embedding = self.embedder.embed(query)
        return self.store.search(embedding, top_k)

    def get_context(self, query: str, top_k: int = 5) -> str:
        """Get formatted context string for a query."""
        results = self.retrieve(query, top_k)
        if not results:
            return ""

        parts = ["## Relevant Code Context\n"]
        for r in results:
            parts.append(
                f"### {r.file_path}:{r.start_line}-{r.end_line} "
                f"(score: {r.score:.3f})\n"
                f"```{r.language}\n{r.content}\n```\n"
            )
        return "\n".join(parts)

    def is_indexed(self) -> bool:
        """Check if project has been indexed."""
        return self.store.count() > 0

    def stats(self) -> dict:
        """Get indexing statistics."""
        return {
            "chunks": self.store.count(),
            "indexed": self.is_indexed(),
        }

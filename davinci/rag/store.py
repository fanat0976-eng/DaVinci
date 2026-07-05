"""Vector store — SQLite-based vector storage with cosine similarity."""

import sqlite3
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SearchResult:
    """A search result with similarity score."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    score: float

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "score": self.score,
        }


class VectorStore:
    """SQLite-based vector store with cosine similarity search."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    start_line INTEGER,
                    end_line INTEGER,
                    language TEXT,
                    embedding BLOB NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path ON chunks(file_path)
            """)
            conn.commit()
        finally:
            conn.close()

    def add(self, content: str, file_path: str, embedding: list[float],
            start_line: int = 0, end_line: int = 0, language: str = "text"):
        """Add a chunk with its embedding."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "INSERT INTO chunks (content, file_path, start_line, end_line, language, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (content, file_path, start_line, end_line, language,
                 json.dumps(embedding))
            )
            conn.commit()
        finally:
            conn.close()

    def search(self, query_embedding: list[float], top_k: int = 5,
               file_filter: str | None = None) -> list[SearchResult]:
        """Search for similar chunks using cosine similarity."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            if file_filter:
                rows = conn.execute(
                    "SELECT content, file_path, start_line, end_line, language, embedding "
                    "FROM chunks WHERE file_path LIKE ?",
                    (f"%{file_filter}%",)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT content, file_path, start_line, end_line, language, embedding "
                    "FROM chunks"
                ).fetchall()
        finally:
            conn.close()

        # Calculate cosine similarity
        results = []
        query_norm = self._normalize(query_embedding)
        for content, file_path, start_line, end_line, language, emb_json in rows:
            embedding = json.loads(emb_json)
            emb_norm = self._normalize(embedding)
            score = self._cosine_similarity(query_norm, emb_norm)
            results.append(SearchResult(
                content=content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language=language,
                score=score,
            ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def clear(self):
        """Clear all chunks."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("DELETE FROM chunks")
            conn.commit()
        finally:
            conn.close()

    def count(self) -> int:
        """Get total number of chunks."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            result = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
            return result[0]
        finally:
            conn.close()

    def _normalize(self, vec: list[float]) -> list[float]:
        """Normalize a vector."""
        norm = sum(x * x for x in vec) ** 0.5
        if norm == 0:
            return vec
        return [x / norm for x in vec]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two normalized vectors."""
        return sum(x * y for x, y in zip(a, b))

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from intelligence.schemas.knowledge import KnowledgeResult


class KnowledgeChunk(BaseModel):
    """A searchable chunk of operational knowledge."""

    content: str
    source: str
    chunk_id: str


class KnowledgeService:
    """
    Local retrieval service for SentinelAI operational procedures.

    The service:
    1. Loads Markdown knowledge documents.
    2. Splits them into searchable sections.
    3. Builds a TF-IDF representation.
    4. Retrieves the most relevant chunks for a query.

    This keeps the RAG layer local and deterministic for the MVP.
    The public retrieve_procedures() contract can later be backed by
    Azure AI Search or another vector store without changing the agent.
    """

    def __init__(
        self,
        knowledge_dir: str | Path | None = None,
    ) -> None:
        if knowledge_dir is None:
            knowledge_dir = (
                Path(__file__).resolve().parents[2]
                / "data"
                / "knowledge"
            )

        self.knowledge_dir = Path(knowledge_dir)
        self.chunks: list[KnowledgeChunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.document_matrix = None

        self._load_knowledge()

    def _load_knowledge(self) -> None:
        """Load and index all Markdown knowledge documents."""

        if not self.knowledge_dir.exists():
            raise FileNotFoundError(
                f"Knowledge directory does not exist: {self.knowledge_dir}"
            )

        markdown_files = sorted(self.knowledge_dir.glob("*.md"))

        if not markdown_files:
            raise FileNotFoundError(
                f"No Markdown knowledge documents found in "
                f"{self.knowledge_dir}"
            )

        chunks: list[KnowledgeChunk] = []

        for path in markdown_files:
            text = path.read_text(encoding="utf-8").strip()

            if not text:
                continue

            chunks.extend(
                self._chunk_document(
                    text=text,
                    source=path.name,
                )
            )

        if not chunks:
            raise ValueError(
                f"Knowledge documents were found in {self.knowledge_dir}, "
                "but they contained no usable content."
            )

        self.chunks = chunks

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )

        self.document_matrix = self.vectorizer.fit_transform(
            chunk.content for chunk in self.chunks
        )

    def _chunk_document(
        self,
        text: str,
        source: str,
    ) -> list[KnowledgeChunk]:
        """
        Split a Markdown document into meaningful sections.

        Headings are retained as part of each chunk so that retrieval
        has useful semantic context even with lightweight TF-IDF search.
        """

        sections = re.split(
            r"\n(?=##?\s+)",
            text,
        )

        chunks: list[KnowledgeChunk] = []

        for index, section in enumerate(sections):
            section = section.strip()

            if not section:
                continue

            # Ignore extremely small fragments.
            words = section.split()

            if len(words) < 8:
                continue

            chunks.append(
                KnowledgeChunk(
                    content=section,
                    source=source,
                    chunk_id=f"{source}:{index}",
                )
            )

        # If the document had no Markdown headings, treat the whole
        # document as one chunk.
        if not chunks:
            chunks.append(
                KnowledgeChunk(
                    content=text,
                    source=source,
                    chunk_id=f"{source}:0",
                )
            )

        return chunks

    def retrieve_procedures(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[KnowledgeResult]:
        """
        Retrieve the most relevant operational procedures.

        Args:
            query: Natural-language description of the situation.
            top_k: Maximum number of results to return.

        Returns:
            Ranked KnowledgeResult objects.

        Raises:
            ValueError: If the query is empty or top_k is invalid.
        """

        if not query or not query.strip():
            raise ValueError("Knowledge retrieval query cannot be empty.")

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        if self.vectorizer is None or self.document_matrix is None:
            raise RuntimeError("Knowledge index has not been initialized.")

        query_vector = self.vectorizer.transform([query.strip()])

        scores = cosine_similarity(
            query_vector,
            self.document_matrix,
        )[0]

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        results: list[KnowledgeResult] = []

        for index in ranked_indices[:top_k]:
            score = float(scores[index])

            # Don't return completely unrelated documents.
            if score <= 0:
                continue

            chunk = self.chunks[index]

            results.append(
                KnowledgeResult(
                    content=chunk.content,
                    source=chunk.source,
                    relevance_score=round(score, 4),
                )
            )

        return results

    def reload(self) -> None:
        """
        Rebuild the knowledge index from disk.

        Useful during development when procedure documents are changed.
        """

        self.chunks = []
        self.vectorizer = None
        self.document_matrix = None
        self._load_knowledge()

    def list_sources(self) -> list[str]:
        """Return the unique knowledge-document filenames currently indexed."""

        return sorted(
            {
                chunk.source
                for chunk in self.chunks
            }
        )
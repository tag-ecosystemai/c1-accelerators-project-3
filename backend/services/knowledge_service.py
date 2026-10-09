from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb


BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma"

COLLECTION_NAME = "sentinelai_knowledge"
MAX_DISTANCE = 0.7


class KnowledgeService:
    """
    Tenant-aware semantic retrieval for SentinelAI knowledge.

    Documents can belong to:
    - global: shared SentinelAI knowledge
    - a company: private company knowledge

    Retrieval always includes global knowledge and, when supplied,
    knowledge belonging to the requesting company only.
    """

    def __init__(
        self,
        chroma_dir: Path | None = None,
    ) -> None:
        self.chroma_dir = chroma_dir or CHROMA_DIR
        self.chroma_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _collection(self):
        client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
        )

        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def retrieve(
        self,
        query: str,
        company_id: int | None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            return []

        collection = self._collection()

        if collection.count() == 0:
            return []

        result = collection.query(
            query_texts=[query],
            n_results=min(
                max(top_k * 2, top_k),
                collection.count(),
            ),
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        results: list[dict[str, Any]] = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):
            metadata = metadata or {}

            tenant_scope = metadata.get(
                "tenant_scope",
                "global",
            )

            if tenant_scope != "global":
                if company_id is None:
                    continue

                if str(metadata.get("company_id")) != str(company_id):
                    continue

            if distance > MAX_DISTANCE:
                continue

            results.append(
                {
                    "content": document,
                    "score": round(
                        1.0 - float(distance),
                        4,
                    ),
                    "source": metadata.get(
                        "source_name",
                        "unknown",
                    ),
                    "tenant_scope": tenant_scope,
                    "metadata": metadata,
                }
            )

            if len(results) >= top_k:
                break

        return results
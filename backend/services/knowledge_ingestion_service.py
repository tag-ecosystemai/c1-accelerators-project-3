from __future__ import annotations

from pathlib import Path

import chromadb


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_KNOWLEDGE_DIR = BASE_DIR / "intelligence" / "knowledge"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
COLLECTION_NAME = "sentinelai_knowledge"


class KnowledgeIngestionService:
    """
    Ingests SentinelAI knowledge into Chroma.

    Knowledge can be:
    - global: shared SentinelAI knowledge
    - company: private company knowledge

    Tenant metadata is stored with every chunk so retrieval can enforce
    company-level isolation.
    """

    def __init__(
        self,
        knowledge_dir: Path | None = None,
        chroma_dir: Path | None = None,
    ) -> None:
        self.knowledge_dir = knowledge_dir or DEFAULT_KNOWLEDGE_DIR
        self.chroma_dir = chroma_dir or CHROMA_DIR
        self.chroma_dir.mkdir(parents=True, exist_ok=True)

    def _collection(self):
        client = chromadb.PersistentClient(path=str(self.chroma_dir))

        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _chunk_text(text: str) -> list[str]:
        return [
            chunk.strip()
            for chunk in text.split("\n\n")
            if chunk.strip()
        ]

    def ingest_global_documents(self) -> int:
        """
        Ingest Markdown/TXT files from the global SentinelAI knowledge directory.
        """

        if not self.knowledge_dir.exists():
            return 0

        collection = self._collection()

        files = sorted(
            path
            for path in self.knowledge_dir.iterdir()
            if path.is_file()
            and path.suffix.lower() in {".md", ".txt"}
        )

        ingested = 0

        for path in files:
            text = path.read_text(encoding="utf-8").strip()

            if not text:
                continue

            for chunk_index, chunk in enumerate(self._chunk_text(text)):
                document_id = f"global-{path.name}-{chunk_index}"

                collection.upsert(
                    ids=[document_id],
                    documents=[chunk],
                    metadatas=[
                        {
                            "document_id": document_id,
                            "tenant_scope": "global",
                            "source_name": path.name,
                            "chunk_id": str(chunk_index),
                            "file_type": path.suffix.lower().lstrip("."),
                        }
                    ],
                )

                ingested += 1

        return ingested

    def ingest_company_document(
        self,
        *,
        company_id: int,
        filename: str,
        content: bytes,
    ) -> int:
        """
        Ingest one private company document into Chroma.

        Company documents are isolated using tenant metadata.
        """

        suffix = Path(filename).suffix.lower()

        if suffix not in {".md", ".txt"}:
            raise ValueError("Only .md and .txt knowledge documents are supported.")

        text = content.decode("utf-8").strip()

        if not text:
            raise ValueError("The knowledge document is empty.")

        collection = self._collection()

        document_id = f"company-{company_id}-{Path(filename).name}"

        chunks = self._chunk_text(text)

        for chunk_index, chunk in enumerate(chunks):
            chunk_id = f"{document_id}-{chunk_index}"

            collection.upsert(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[
                    {
                        "document_id": document_id,
                        "tenant_scope": "company",
                        "company_id": str(company_id),
                        "source_name": Path(filename).name,
                        "chunk_id": str(chunk_index),
                        "file_type": suffix.lstrip("."),
                    }
                ],
            )

        return len(chunks)
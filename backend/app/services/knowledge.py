from pathlib import Path

# This file lives at backend/app/services/knowledge.py
# parents[3] is the project root, parents[2] is backend/
KNOWLEDGE_DIR = Path(__file__).resolve().parents[3] / "intelligence" / "knowledge"
CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_store"
COLLECTION = "knowledge"
MAX_DISTANCE = 0.7   


def _client():
    import chromadb
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def build_index() -> int:
    """Read every .md file, split it into pieces, and store the pieces."""
    client = _client()
    try:
        client.delete_collection(COLLECTION)   # start fresh each time
    except Exception:
        pass
    collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    ids, documents, metadatas = [], [], []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        pieces = [p.strip() for p in text.split("\n\n") if p.strip()]
        for i, piece in enumerate(pieces):
            ids.append(f"{path.name}-{i}")
            documents.append(piece)
            metadatas.append({"source": path.name})

    if documents:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(documents)

def search_knowledge(query: str, k: int = 2) -> dict:
    """Return the pieces of the notes closest in meaning to the query."""
    try:
        collection = _client().get_collection(COLLECTION)
        count = collection.count()
        if count == 0:
            return {"available": False, "reason": "knowledge index is empty"}
        result = collection.query(query_texts=[query], n_results=min(k, count))
        passages = [
            {"text": text, "source": meta["source"], "distance": round(dist, 3)}
            for text, meta, dist in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0]
            )
            if dist <= MAX_DISTANCE
        ]
        return {"available": True, "passages": passages}
    except Exception as e:
        return {"available": False, "reason": str(e)}
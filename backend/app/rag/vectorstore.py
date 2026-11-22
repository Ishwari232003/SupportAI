import chromadb
from app.core import config

_client = None


def client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    return _client


def collection(model_key=None):
    return client().get_or_create_collection(f"support_{model_key or config.DEFAULT_EMBED}",
                                             metadata={"hnsw:space": "cosine"})


def reset_collections():
    for c in client().list_collections():
        client().delete_collection(c if isinstance(c, str) else c.name)


def delete_document(doc_id):
    for k in config.EMBED_MODELS:
        collection(k).delete(where={"doc_id": doc_id})


def deactivate_document(doc_id):
    """Mark every chunk of a document as inactive (old policy version) but keep it."""
    for k in config.EMBED_MODELS:
        col = collection(k)
        got = col.get(where={"doc_id": doc_id})
        if got["ids"]:
            col.update(ids=got["ids"], metadatas=[{**m, "is_active": False} for m in got["metadatas"]])
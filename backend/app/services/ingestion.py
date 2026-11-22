from datetime import date
from pathlib import Path

from app.db.models import SessionLocal, Document, ParentChunk
from app.rag.loaders import load_file
from app.rag.chunking import chunk_sections
from app.rag.embeddings import embed_texts
from app.rag import vectorstore


def ingest_file(path, meta, models=("bge",), size=None, overlap=None):
    """meta keys: doc_type, policy_name, version, effective_date, is_active, product_category,
    region, customer_type, seller, warehouse, order_status"""
    path = Path(path)
    s = SessionLocal()
    try:
        # a new active version deactivates older versions of the same policy (kept for comparison)
        if meta.get("is_active", True):
            for old in s.query(Document).filter(Document.policy_name == meta["policy_name"],
                                                Document.is_active == True):  # noqa: E712
                old.is_active = False
                vectorstore.deactivate_document(old.id)
            s.commit()

        eff = meta.get("effective_date")
        doc = Document(name=path.name, doc_type=meta["doc_type"], policy_name=meta["policy_name"],
                       version=str(meta.get("version", "1")),
                       effective_date=date.fromisoformat(eff) if isinstance(eff, str) and eff else None,
                       is_active=bool(meta.get("is_active", True)), meta=meta)
        s.add(doc)
        s.commit()

        sections = load_file(path)
        parents, children = chunk_sections(sections, doc.id, size, overlap)
        s.add_all([ParentChunk(id=p["id"], document_id=doc.id, section=p["section"],
                               page=int(p["page"]) if p["page"] is not None else None, text=p["text"])
                   for p in parents])
        s.commit()

        if children:
            md = [{
                "doc_id": doc.id, "doc_name": path.name, "doc_type": meta["doc_type"],
                "policy_name": meta["policy_name"], "section": c["section"] or "General",
                "page": int(c["page"] or 0), "parent_id": c["parent_id"],
                "version": str(meta.get("version", "1")),
                "effective_date": str(meta.get("effective_date") or ""),
                "is_active": bool(meta.get("is_active", True)),
                "product_category": meta.get("product_category", "all"), "region": meta.get("region", "all"),
                "customer_type": meta.get("customer_type", "all"), "seller": meta.get("seller", "all"),
                "warehouse": meta.get("warehouse", "all"), "order_status": meta.get("order_status", "all"),
            } for c in children]
            texts = [c["text"] for c in children]
            ids = [c["id"] for c in children]
            for m in models:
                vectorstore.collection(m).add(ids=ids, documents=texts, metadatas=md,
                                              embeddings=embed_texts(texts, m))
        return {"doc_id": doc.id, "parents": len(parents), "children": len(children)}
    finally:
        s.close()
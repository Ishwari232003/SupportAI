from app.rag import vectorstore
from app.rag.embeddings import embed_texts

c = vectorstore.collection("bge")
print("chunks in index:", c.count())
for q in ["refund delayed", "return window for Product X", "warranty period Product ABC"]:
    r = c.query(query_embeddings=embed_texts([q], "bge"), n_results=3)
    print("\nQ:", q)
    for m in r["metadatas"][0]:
        print("  ", m["doc_name"], "|", m["section"], "| page", m["page"])
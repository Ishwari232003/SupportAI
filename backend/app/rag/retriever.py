import re
from collections import defaultdict

from rank_bm25 import BM25Okapi

from app.core import config
from app.db.models import SessionLocal, ParentChunk
from app.rag import vectorstore
from app.rag.embeddings import embed_texts
from app.rag.llm import chat_json

TOKEN = re.compile(r"[a-z0-9\-]+")
_bm25 = {}          # model_key -> (bm25, ids, docs, metas)
_reranker = None


def tok(t):
    return TOKEN.findall(t.lower())


# ---------------- 1. query expansion ----------------
def expand_query(q, n=4):
    try:
        out = chat_json([
            {"role": "system", "content": "You rewrite customer-support search queries for an e-commerce "
             f"knowledge base. Return JSON: {{\"queries\": [..{n} short alternative search queries..]}}. "
             "Use different wording and related policy terms. Keep product names and IDs unchanged."},
            {"role": "user", "content": q}])
        qs = [x for x in out.get("queries", []) if isinstance(x, str)][:n]
    except Exception:
        qs = []
    return [q] + qs


# ---------------- 2. metadata filter ----------------

# ---------------- category detection ----------------
def detect_category(query):
    q = query.lower()

    if "product x" in q:
        return "Electronics"

    if "product abc" in q:
        return "Appliances"

    if "home products" in q or "home product" in q:
        return "Home"

    return None

def build_where(f):
    """f: dict of metadata filters. Active-only by default; 'all' chunks always match."""
    conds = []
    if f.get("include_inactive") is not True:
        conds.append({"is_active": True})
    for key in ["doc_type", "policy_name", "version", "product_category", "region",
                "customer_type", "seller", "warehouse", "order_status", "effective_date"]:
        v = f.get(key)
        if not v:
            continue
        if key in ("doc_type", "policy_name", "version", "effective_date"):
            conds.append({key: v})
        else:
            conds.append({key: {"$in": [v, "all"]}})
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"$and": conds}


def _passes(meta, f):
    if f.get("include_inactive") is not True and not meta.get("is_active", True):
        return False
    for key in ["doc_type", "policy_name", "version", "effective_date"]:
        if f.get(key) and meta.get(key) != f[key]:
            return False
    for key in ["product_category", "region", "customer_type", "seller", "warehouse", "order_status"]:
        if f.get(key) and meta.get(key) not in (f[key], "all"):
            return False
    return True


# ---------------- 3. vector + BM25 search ----------------
def vector_search(q, model_key, f, k=15):
    col = vectorstore.collection(model_key)
    where = build_where(f)
    r = col.query(query_embeddings=embed_texts([q], model_key), n_results=k, where=where)
    return [(i, d, m) for i, d, m in zip(r["ids"][0], r["documents"][0], r["metadatas"][0])]


def _load_bm25(model_key):
    if model_key not in _bm25:
        got = vectorstore.collection(model_key).get()
        _bm25[model_key] = (BM25Okapi([tok(d) for d in got["documents"]]),
                            got["ids"], got["documents"], got["metadatas"])
    return _bm25[model_key]


def reset_bm25():
    _bm25.clear()


def bm25_search(q, model_key, f, k=15):
    bm, ids, docs, metas = _load_bm25(model_key)
    scores = bm.get_scores(tok(q))
    order = sorted(range(len(ids)), key=lambda i: scores[i], reverse=True)
    out = []
    for i in order:
        if scores[i] <= 0:
            break
        if _passes(metas[i], f):
            out.append((ids[i], docs[i], metas[i]))
        if len(out) >= k:
            break
    return out


# ---------------- 4. fusion (Reciprocal Rank Fusion) ----------------
def rrf(result_lists, k=60):
    score, keep = defaultdict(float), {}
    for lst in result_lists:
        for rank, (cid, doc, meta) in enumerate(lst):
            score[cid] += 1.0 / (k + rank + 1)
            keep[cid] = (cid, doc, meta)
    return [keep[c] for c in sorted(score, key=score.get, reverse=True)]


# ---------------- 5. re-ranking (cross-encoder) ----------------
def rerank(q, cands, top_k=5):
    global _reranker
    if not cands:
        return []
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(config.RERANK_MODEL)
    scores = _reranker.predict([(q, c[1]) for c in cands])
    ranked = sorted(zip(cands, scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [(c, float(s)) for c, s in ranked]


# ---------------- 6. parent expansion ----------------
def expand_parents(ranked):
    """Swap small chunks for their full sections; dedupe; keep best score per parent."""
    s = SessionLocal()
    try:
        seen, out = {}, []
        for (cid, doc, meta), score in ranked:
            pid = meta["parent_id"]
            if pid in seen:
                continue
            p = s.get(ParentChunk, pid)
            seen[pid] = True
            out.append({"parent_id": pid, "text": p.text if p else doc, "child_text": doc,
                        "score": score, "meta": meta})
        return out
    finally:
        s.close()


# ---------------- full pipeline (each stage can be switched off for the ablation) ----------------
def retrieve(query, filters=None, model_key=None, top_k=5, use_expansion=True, use_bm25=True,
             use_rerank=True, use_parent=True, trace=None):

    f = filters.copy() if filters else {}

    if "product_category" not in f:
        category = detect_category(query)

    if category:
        f["product_category"] = category

    mk = model_key or config.DEFAULT_EMBED
    queries = expand_query(query) if use_expansion else [query]
    lists = []
    for q in queries:
        lists.append(vector_search(q, mk, f))
        if use_bm25:
            lists.append(bm25_search(q, mk, f))
    fused = rrf(lists)[:30]
    ranked = rerank(query, fused, top_k) if use_rerank else [(c, 1.0 / (i + 1)) for i, c in enumerate(fused[:top_k])]
    if trace is not None:
        trace.update({"queries": queries, "candidates": len(fused)})
    if use_parent:
        return expand_parents(ranked)
    return [{"parent_id": c[2]["parent_id"], "text": c[1], "child_text": c[1], "score": s, "meta": c[2]}
            for c, s in ranked]
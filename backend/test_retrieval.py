from app.rag.retriever import retrieve

for q, f in [("refund delayed", {}),
             ("return window for Product X", {"doc_type": "Return Policy"}),
             ("Where do delayed shipments in South come from", {"region": "South"})]:
    trace = {}
    res = retrieve(q, f, trace=trace)
    print("\nQ:", q, "| filters:", f)
    print("  expanded:", trace.get("queries"))
    for r in res:
        m = r["meta"]
        print(f"  {r['score']:.2f}  {m['doc_name']} | {m['section']} | page {m['page']}")
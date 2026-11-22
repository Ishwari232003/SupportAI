
from app.rag.retriever import retrieve

questions = [
    "What is the warranty period for Product X?",
    "What is the return window for Product X?",
    "What is the warranty period for Product ABC?",
    "How can I track my refund?",
    "What is the warranty period for Home products?"
]

for question in questions:

    results = retrieve(
        question,
        filters=None
    )

    print("\n" + "=" * 70)
    print("QUESTION:", question)
    print("=" * 70)

    for i, result in enumerate(results, 1):
        meta = result["meta"]

        print(f"\nResult {i}")
        print("Score:", round(result["score"], 3))
        print("Document:", meta["doc_name"])
        print("Section:", meta["section"])
        print("Full Metadata:", meta)
        print("Content:", result["text"][:200])

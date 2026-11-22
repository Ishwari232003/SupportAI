
from app.rag.retriever import retrieve

question = "What is the return window for Product X?"

results = retrieve(question, top_k=10)

print("\n========== RETRIEVAL RANKING ==========\n")

for rank, result in enumerate(results, 1):
    meta = result["meta"]

    print(f"Rank: {rank}")
    print("Score:", round(result["score"], 3))
    print("Document:", meta["doc_name"])
    print("Section:", meta["section"])
    if meta["doc_name"] == "warranty_matrix.xlsx":
        print("CHUNK CONTENT:")
        print(result["child_text"])
        print("FULL PARENT CONTENT:")
        print(result["text"])

    print("-" * 50)

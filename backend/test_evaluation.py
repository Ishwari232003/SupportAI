
import json

from app.rag.retriever import retrieve


# Load evaluation test cases
with open("test_cases.json", "r", encoding="utf-8") as file:
    test_cases = json.load(file)


total_precision = 0
total_recall = 0

print("\n========== RAG RETRIEVAL EVALUATION ==========\n")


for test in test_cases:

    question = test["question"]
    expected_sources = set(test["expected_sources"])

    # Retrieve documents for the question
    results = retrieve(question)
    results = retrieve(question, top_k=8)

    retrieved_sources = {
        result["meta"]["doc_name"]
        for result in results
    }

    # Calculate source precision and recall
    relevant_sources = expected_sources.intersection(
        retrieved_sources
    )

    precision = (
        len(relevant_sources) / len(retrieved_sources)
        if retrieved_sources else 0
    )

    recall = (
        len(relevant_sources) / len(expected_sources)
        if expected_sources else 0
    )

    total_precision += precision
    total_recall += recall

    print("=" * 60)
    print("QUESTION:", question)

    print("\nExpected sources:", len(expected_sources))
    print("Retrieved sources:", len(retrieved_sources))
    print("Relevant sources found:", len(relevant_sources))

    print(f"\nSource Precision: {precision:.2%}")
    print(f"Source Recall:    {recall:.2%}")

    print("\nRetrieved documents:")
    for source in sorted(retrieved_sources):
        print(" -", source)

    print("\nMissing expected documents:")
    missing = expected_sources - retrieved_sources

    if missing:
        for source in sorted(missing):
            print(" -", source)
    else:
        print("None")


# Calculate average metrics
count = len(test_cases)

if count:
    print("\n" + "=" * 60)
    print("OVERALL EVALUATION")
    print("=" * 60)

    print(f"Total test cases: {count}")
    print(f"Average Source Precision: {total_precision / count:.2%}")
    print(f"Average Source Recall:    {total_recall / count:.2%}")

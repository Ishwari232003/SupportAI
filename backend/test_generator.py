from app.rag.generator import generate_answer

questions = [
    "What is the warranty period for Product X?",
    "What is the return window for Product X?",
    "What is the warranty period for Product ABC?",
    "How can I track my refund?",
    "What is the warranty period for Home products?"
]

for question in questions:

    result = generate_answer(question)

    print("\n" + "=" * 70)
    print("QUESTION:", question)
    print("=" * 70)

    print("\nANSWER:")
    print(result["answer"])

    print("\nSELECTED SOURCES:")

    for source in result["sources"]:
        print(source["document"], "|", source["section"])
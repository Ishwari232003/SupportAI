
from app.rag.retriever import retrieve
from app.rag.llm import chat

question = "My refund has been approved, but I haven't received the money. What should I do?"

# 1. Retrieve relevant documents
results = retrieve(
    question,
    filters=None
)

# 2. Prepare context from retrieved documents
context_parts = []

for i, result in enumerate(results, 1):
    meta = result["meta"]

    context_parts.append(
        f"""
Source {i}:
Document: {meta['doc_name']}
Section: {meta['section']}
Page: {meta['page']}

Content:
{result['text']}
"""
    )

context = "\n".join(context_parts)

print("\nRETRIEVED DOCUMENTS:")

for result in results:
    meta = result["meta"]
    print(
        meta["doc_name"],
        "|",
        meta["section"],
        "| Page:",
        meta["page"]
    )

# 3. Generate answer using Groq
messages = [
    {
        "role": "system",
        "content": """
You are an e-commerce customer support assistant.

Answer the customer's question using ONLY the provided context.

Rules:
1. Do not invent information.
2. If the answer is missing, say you cannot find it in the available documents.
3. Give a clear and helpful answer.
4. Mention the source document, section and page.
"""
    },
    {
        "role": "user",
        "content": f"""
Customer question:
{question}

Retrieved context:
{context}

Provide the answer with source references.
"""
    }
]

answer = chat(messages, temperature=0.0)

print("\nCUSTOMER QUESTION:")
print(question)

print("\nAI GENERATED ANSWER:")
print(answer)

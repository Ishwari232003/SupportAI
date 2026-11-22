
from app.rag.retriever import retrieve
from app.rag.llm import chat, chat_json


def rewrite_question(question, history=None):

    if not history:
        return question

    messages = [
        {
            "role": "system",
            "content": """
You rewrite customer follow-up questions into standalone search queries.

Rules:
1. Use conversation history to understand references.
2. Preserve the customer's original meaning.
3. Do not answer the question.
4. Return JSON:
{"standalone_question": "rewritten question"}
"""
        }
    ]

    messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": f"Rewrite this question:\n{question}"
    })

    try:
        result = chat_json(messages)
        rewritten = result.get("standalone_question", "")
        return rewritten.strip() if rewritten.strip() else question

    except Exception:
        return question


def select_sources(question, results):

    source_data = []

    for i, result in enumerate(results, 1):
        meta = result["meta"]

        source_data.append({
            "id": i,
            "document": meta["doc_name"],
            "section": meta["section"],
            "page": meta["page"],
            "content": result["text"]
        })

    messages = [
        {
            "role": "system",
            "content": """
You are an evidence evaluator for an e-commerce support assistant.

Identify sources that directly support answering the customer's question.

Rules:
1. Select sources containing relevant factual evidence.
2. Exclude unrelated products, categories and topics.
3. Supporting sources may be selected if they genuinely help answer.
4. Do not select a source merely because it contains similar words.
5. If no source supports the answer, return an empty list.
6. Return valid JSON in this format:
{"selected_ids": [1, 2]}
"""
        },
        {
            "role": "user",
            "content": f"""
Customer question:
{question}

Available sources:
{source_data}

Select the relevant source IDs.
"""
        }
    ]

    try:
        result = chat_json(messages)
        selected_ids = result.get("selected_ids", [])

        valid_ids = {
            i for i in selected_ids
            if isinstance(i, int) and 1 <= i <= len(results)
        }

        selected = [
            result for i, result in enumerate(results, 1)
            if i in valid_ids
        ]

        return selected

    except Exception:
        # Keep original results if source selection fails.
        return results


def generate_answer(question, filters=None, history=None):

    # 1. Rewrite follow-up question
    search_question = rewrite_question(question, history)

    print("Original question:", question)
    print("Search question:", search_question)

    # 2. Retrieve documents
    results = retrieve(
        search_question,
        filters=filters
    )

    if not results:
        return {
            "answer": "I couldn't find relevant information in the available documents.",
            "sources": []
        }

    # 3. Select relevant evidence
    results = select_sources(search_question, results)

    if not results:
        return {
            "answer": "I couldn't find sufficient relevant information in the available documents.",
            "sources": []
        }

    # 4. Prepare context and source references
    context_parts = []
    sources = []

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

        source = {
            "document": meta["doc_name"],
            "section": meta["section"],
            "page": meta["page"]
        }

        if source not in sources:
            sources.append(source)

    context = "\n".join(context_parts)

    # 5. Generate grounded answer
    messages = [
        {
            "role": "system",
            "content": """
You are an e-commerce customer support assistant.

Answer using ONLY the provided evidence.

Rules:
1. Never invent information.
2. If the answer is unavailable, clearly say so.
3. Give clear and helpful answers.
4. Do not make unsupported promises.
5. Cite only the provided source documents and sections.
6. Use conversation history to understand follow-up questions.
7. Use retrieved evidence as the factual source of answers.
"""
        }
    ]

    if history:
        messages.extend(history)

    messages.append({
        "role": "user",
        "content": f"""
Customer question:
{question}

Search query:
{search_question}

Selected evidence:
{context}

Answer the customer using only this evidence.
"""
    })

    answer = chat(messages, temperature=0.0)

    return {
        "answer": answer,
        "sources": sources
    }

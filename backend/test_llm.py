from app.rag.llm import chat
print(chat([{"role": "user", "content": "Say hello in 3 words"}]))
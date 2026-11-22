
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4

from app.rag.generator import generate_answer

router = APIRouter()

# Temporary in-memory conversation storage
conversation_history = {}


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


@router.post("/chat")
def chat_endpoint(request: ChatRequest):

    try:
        # 1. Get or create session ID
        session_id = request.session_id or str(uuid4())

        # 2. Get previous conversation
        history = conversation_history.get(session_id, [])

        # 3. Generate answer
        result = generate_answer(
            request.question,
            history=history
        )

        # 4. Store current conversation
        history.append({
            "role": "user",
            "content": request.question
        })

        history.append({
            "role": "assistant",
            "content": result["answer"]
        })

        # Keep only the latest 10 messages
        conversation_history[session_id] = history[-10:]

        # 5. Return response
        return {
            "session_id": session_id,
            "question": request.question,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

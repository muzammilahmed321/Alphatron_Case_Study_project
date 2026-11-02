from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.routes.documents import retriever
from app.services.rag.generator import AnswerGenerator

router = APIRouter(prefix="/chat", tags=["chat"])

generator = AnswerGenerator()


class Question(BaseModel):
    question: str
    top_k: int = 4


@router.post("/ask")
def ask_question(body: Question):
    # 1. Find the most relevant chunks
    chunks = retriever.search(body.question, body.top_k)
    if not chunks:
        raise HTTPException(status_code=404, detail="Upload a document first")

    # 2. Let Gemini answer from those chunks
    try:
        result = generator.answer(body.question, chunks)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Gemini error: {error}")

    # 3. Return the answer plus the sources used
    return {
        "question": body.question,
        "answer": result["answer"],
        "sources": [
            {"source": c["source"], "page": c["page"], "score": c["score"]}
            for c in chunks
        ],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "seconds": result["seconds"],
    }
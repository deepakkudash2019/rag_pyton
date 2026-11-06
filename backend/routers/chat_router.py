import logging
from fastapi import APIRouter, HTTPException
from schemas.chat_schema import ChatRequest
from services.rag_service import RAGService

router = APIRouter()
@router.post("")
def chat(request: ChatRequest):
    try: return RAGService().ask(request.question, request.top_k)
    except RuntimeError as exc: raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logging.exception("Chat request failed")
        raise HTTPException(502, "Chat request failed. Check your API key, network, and backend logs.") from exc


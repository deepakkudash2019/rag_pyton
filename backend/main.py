"""FastAPI entry point for the local document RAG application."""
from pathlib import Path
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
from routers.document_router import router as document_router
from routers.chat_router import router as chat_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Local RAG Chatbot API", version="1.0.0", description="Upload documents, index them in FAISS, and ask grounded questions.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(document_router, prefix="/api/documents", tags=["documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

@app.get("/api/health")
def health():
    """Report service availability without exposing secrets."""
    return {"status": "ok", "service": "rag-chatbot"}


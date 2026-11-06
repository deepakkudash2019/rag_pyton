import os, logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from services.vector_store_service import VectorStoreService

log = logging.getLogger(__name__)
PROMPT = ChatPromptTemplate.from_messages([("system", "Answer only from the supplied document context. If context does not contain the answer, say you could not find it in the uploaded documents. Do not make up facts. Cite source names/pages in your answer when useful.\n\nContext:\n{context}"), ("human", "{question}")])

class RAGService:
    def __init__(self, vectors=None): self.vectors = vectors or VectorStoreService()
    def ask(self, question: str, top_k: int | None = None):
        if not os.getenv("OPENAI_API_KEY"): raise RuntimeError("OPENAI_API_KEY is missing. Configure .env to chat.")
        k = top_k or int(os.getenv("TOP_K", "5")); matches = self.vectors.search(question, k)
        if not matches: return {"answer": "I could not find relevant information in the uploaded documents.", "sources": []}
        # Top-K limits context to the strongest matching passages, keeping answers grounded and prompts concise.
        docs = [doc for doc, _score in matches]
        context = "\n\n".join(f"[{d.metadata.get('document_name')} page {d.metadata.get('page_number') or 'n/a'}]\n{d.page_content}" for d in docs)
        llm = ChatOpenAI(model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"), temperature=0)
        response = (PROMPT | llm).invoke({"context": context, "question": question})
        sources = [{"document_name": d.metadata.get("document_name", "unknown"), "page_number": d.metadata.get("page_number"), "content": d.page_content} for d in docs]
        return {"answer": response.content, "sources": sources}


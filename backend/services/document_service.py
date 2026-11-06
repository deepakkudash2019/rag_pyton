import os, uuid, logging
from datetime import datetime, timezone
from langchain_core.documents import Document
from utils.pdf_utils import extract_pages
from utils.text_utils import split_text
from services.vector_store_service import VectorStoreService

log = logging.getLogger(__name__)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500")); CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

class DocumentService:
    def __init__(self, vectors=None): self.vectors = vectors or VectorStoreService()
    def ingest(self, filename: str, payload: bytes):
        pages = extract_pages(filename, payload); document_id = str(uuid.uuid4()); chunks = []
        for page_number, text in pages:
            # Split each PDF page independently so its source page remains accurate.
            for content in split_text(text, CHUNK_SIZE, CHUNK_OVERLAP):
                chunks.append(Document(page_content=content, metadata={"document_id": document_id, "document_name": filename, "page_number": page_number}))
        if not chunks: raise ValueError("No text could be chunked from this document.")
        record = {"document_id": document_id, "document_name": filename, "chunk_count": len(chunks), "uploaded_at": datetime.now(timezone.utc).isoformat()}
        self.vectors.add(chunks, record)
        return record


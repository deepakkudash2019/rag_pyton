import os, logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.document_service import DocumentService
from services.vector_store_service import VectorStoreService

router = APIRouter(); ALLOWED = {".pdf", ".docx", ".txt"}; MAX_BYTES = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024

@router.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    if not files: raise HTTPException(400, "Select at least one document.")
    validated = []
    for file in files:
        name = file.filename or ""
        if os.path.splitext(name)[1].lower() not in ALLOWED: raise HTTPException(415, f"Unsupported file type: {name}")
        payload = await file.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES: raise HTTPException(413, f"{name} exceeds the {MAX_BYTES // (1024*1024)} MB upload limit.")
        validated.append((name, payload))
    # Validate every file before constructing OpenAI clients or indexing any file.
    service = DocumentService(); results = []
    for name, payload in validated:
        try: results.append(service.ingest(name, payload))
        except ValueError as exc: raise HTTPException(422, f"{name}: {exc}") from exc
        except Exception as exc:
            logging.exception("Document ingestion failed for %s", name)
            raise HTTPException(502, f"Could not index {name}. Check API key and service logs.") from exc
    return {"status": "success", "documents": results}

@router.get("")
def list_documents():
    try: return {"documents": VectorStoreService().list_documents()}
    except RuntimeError as exc: raise HTTPException(503, str(exc)) from exc

@router.delete("/{document_id}")
def delete_document(document_id: str):
    try: deleted = VectorStoreService().delete(document_id)
    except Exception as exc:
        logging.exception("Document deletion failed")
        raise HTTPException(500, "Could not update the local vector index.") from exc
    if not deleted: raise HTTPException(404, "Document not found.")
    return {"status": "deleted", "document_id": document_id}


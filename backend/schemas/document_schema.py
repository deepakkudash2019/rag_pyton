from pydantic import BaseModel

class DocumentInfo(BaseModel):
    document_id: str
    document_name: str
    chunk_count: int
    uploaded_at: str

class UploadResult(BaseModel):
    status: str
    documents: list[DocumentInfo]


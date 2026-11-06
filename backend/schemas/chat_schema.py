from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)

class Source(BaseModel):
    document_name: str
    page_number: int | None = None
    content: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


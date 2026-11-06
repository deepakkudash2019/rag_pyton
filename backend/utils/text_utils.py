import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_text(text: str) -> str:
    """Normalize extracted whitespace while preserving paragraph boundaries."""
    text = text.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Create searchable passages. Overlap retains boundary facts split between chunks."""
    if chunk_size < 1 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("Require chunk_size > 0 and 0 <= chunk_overlap < chunk_size")
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True)
    return [d.page_content for d in splitter.create_documents([clean_text(text)]) if d.page_content.strip()]


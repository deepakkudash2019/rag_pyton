import os
from langchain_openai import OpenAIEmbeddings

def get_embeddings() -> OpenAIEmbeddings:
    """Build the shared embedding client; queries and passages use the same model."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing. Copy .env.example to .env and configure it.")
    return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))


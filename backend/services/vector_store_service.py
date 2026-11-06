import json, logging, os
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from .embedding_service import get_embeddings

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / os.getenv("VECTOR_STORE_DIR", "backend/vector_store")
REGISTRY = STORE / "documents.json"

class VectorStoreService:
    """Manages a local FAISS index. Pickle loading is enabled only for this app's local index."""
    def __init__(self): self.embeddings = get_embeddings()
    def _read_registry(self):
        if not REGISTRY.exists(): return {}
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    def _write_registry(self, registry):
        STORE.mkdir(parents=True, exist_ok=True)
        REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    def load(self):
        if not (STORE / "index.faiss").exists(): return None
        # LangChain's FAISS docstore is pickle-backed; trust only files generated in this controlled local directory.
        return FAISS.load_local(str(STORE), self.embeddings, allow_dangerous_deserialization=True)
    def add(self, documents: list[Document], record: dict):
        store = self.load()
        if store is None: store = FAISS.from_documents(documents, self.embeddings, normalize_L2=True)
        else: store.add_documents(documents)
        STORE.mkdir(parents=True, exist_ok=True); store.save_local(str(STORE))
        registry = self._read_registry(); registry[record["document_id"]] = record; self._write_registry(registry)
    def list_documents(self): return list(self._read_registry().values())
    def search(self, query: str, top_k: int):
        store = self.load()
        if store is None: return []
        # FAISS uses normalized vectors and inner product, equivalent to cosine similarity.
        return store.similarity_search_with_score(query, k=top_k)
    def delete(self, document_id: str):
        registry = self._read_registry()
        if document_id not in registry: return False
        del registry[document_id]
        docs = []
        store = self.load()
        if store:
            for doc in store.docstore._dict.values():
                if doc.metadata.get("document_id") != document_id: docs.append(doc)
        if docs:
            rebuilt = FAISS.from_documents(docs, self.embeddings, normalize_L2=True)
            rebuilt.save_local(str(STORE))
        else:
            for filename in ("index.faiss", "index.pkl"):
                (STORE / filename).unlink(missing_ok=True)
        self._write_registry(registry)
        return True


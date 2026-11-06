import unittest
from unittest.mock import patch
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from services.document_service import DocumentService
from services.embedding_service import get_embeddings
from services.vector_store_service import VectorStoreService

class FakeEmbeddings(Embeddings):
    """Deterministic vectors for testing FAISS without OpenAI calls or API charges."""
    def embed_documents(self, texts):
        return [[float(len(t)), float(t.lower().count("apple") + 1), 1.0] for t in texts]
    def embed_query(self, text): return [float(len(text)), float(text.lower().count("apple") + 1), 1.0]

class ServiceTests(unittest.TestCase):
    @patch.dict("os.environ", {"OPENAI_API_KEY":"test-key", "OPENAI_EMBEDDING_MODEL":"text-embedding-3-small"})
    @patch("services.embedding_service.OpenAIEmbeddings")
    def test_embedding_client_uses_configured_model(self, factory):
        get_embeddings()
        factory.assert_called_once_with(model="text-embedding-3-small")

    def test_faiss_add_and_retrieve_persisted_index(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp, patch("services.vector_store_service.STORE", Path(tmp)), patch("services.vector_store_service.REGISTRY", Path(tmp) / "documents.json"), patch.object(VectorStoreService, "__init__", lambda self: setattr(self, "embeddings", FakeEmbeddings())):
            service = VectorStoreService()
            service.add([Document(page_content="An apple policy", metadata={"document_id":"d1", "document_name":"a.txt", "page_number":None})], {"document_id":"d1", "document_name":"a.txt", "chunk_count":1, "uploaded_at":"now"})
            results = service.search("apple policy", 1)
            self.assertEqual(results[0][0].metadata["document_name"], "a.txt")
            self.assertEqual(service.list_documents()[0]["document_id"], "d1")

    @patch("services.document_service.VectorStoreService")
    def test_ingestion_chunks_and_preserves_metadata(self, vector_factory):
        service = DocumentService(vector_factory.return_value)
        with patch("services.document_service.CHUNK_SIZE", 12), patch("services.document_service.CHUNK_OVERLAP", 3):
            record = service.ingest("brief.txt", b"A sufficiently long text document for multiple chunks.")
        stored_docs = vector_factory.return_value.add.call_args.args[0]
        self.assertGreater(len(stored_docs), 1)
        self.assertTrue(all(doc.metadata["document_id"] == record["document_id"] for doc in stored_docs))

if __name__ == "__main__": unittest.main()

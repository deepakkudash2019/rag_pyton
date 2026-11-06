import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

class APITests(unittest.TestCase):
    def setUp(self): self.client = TestClient(app)
    def test_health(self): self.assertEqual(self.client.get("/api/health").json()["status"], "ok")
    def test_upload_rejects_bad_extension(self):
        response = self.client.post("/api/documents/upload", files=[("files", ("x.exe", b"x", "application/octet-stream"))])
        self.assertEqual(response.status_code, 415)
    @patch("routers.document_router.DocumentService")
    def test_upload_api_returns_chunk_count(self, service_factory):
        service_factory.return_value.ingest.return_value = {"document_id":"id", "document_name":"x.txt", "chunk_count":2, "uploaded_at":"2026-01-01T00:00:00Z"}
        response = self.client.post("/api/documents/upload", files=[("files", ("x.txt", b"hello", "text/plain"))])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["documents"][0]["chunk_count"], 2)
    @patch("routers.chat_router.RAGService")
    def test_chat_route(self, _mock):
        _mock.return_value.ask.return_value = {"answer":"grounded", "sources":[]}
        response = self.client.post("/api/chat", json={"question":"What is in the docs?", "top_k":3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "grounded")

if __name__ == "__main__": unittest.main()


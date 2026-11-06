# Atlas / Local — RAG chatbot

A local learning project: upload PDF, DOCX, and TXT files, index text passages with OpenAI embeddings in a persistent FAISS store, and chat against retrieved passages with source references. The React interface and FastAPI service run on your computer; OpenAI receives extracted text for embedding and chat completion. The API key stays in the backend `.env` file.

## Architecture and request flow

```text
Browser (React/Vite) -- multipart upload --> FastAPI
                                      ├─ PyPDF / python-docx / UTF-8 extraction
                                      ├─ whitespace cleanup + recursive text splitting
                                      ├─ OpenAI text-embedding-3-small
                                      └─ normalized vectors + passage metadata --> backend/vector_store

Browser -- question/top_k --> FastAPI --> embed query --> FAISS cosine-equivalent search
                                                   --> top passages + source metadata --> OpenAI chat model
Browser <-- answer + source passages/page numbers --------------------------------------┘
```

### Ingestion, step by step

The upload route validates extension and byte size, then reads each PDF page separately (page numbers are one-based); DOCX and TXT are indexed as a single body. Text cleanup removes null bytes and excess whitespace. `RecursiveCharacterTextSplitter` divides the text into configurable passages; overlap repeats a small tail at the next passage's start, preserving statements that straddle boundaries. Each passage becomes a LangChain `Document` with document ID, filename, and page metadata. The shared embeddings client makes vectors, then LangChain FAISS persists the index under `backend/vector_store/`.

### Query, retrieval, answer

The chat route embeds the question with the same configured embedding model. FAISS compares normalized vectors by inner product, equivalent to cosine similarity, and returns the highest-scoring Top-K passages. Normalization makes vector length irrelevant so angular similarity determines ranking. The prompt includes those passages and directs the model to say when the answer is absent. The API returns the answer and the exact retrieved text with filenames/page numbers for inspection. You can set `top_k` per request (1–20), or configure the default in `.env`.

Example: after indexing `policy.pdf`, ask “What is the approval process?” The response contains a grounded summary and a source entry such as `policy.pdf`, page 5, with its retrieved passage. When the index is empty, the app returns a clear no-relevant-information answer without calling the chat model.

## Stack and structure

Python 3.11+, FastAPI/Uvicorn, LangChain, OpenAI embeddings/chat, FAISS CPU, PyPDF, python-docx, dotenv; React 18, Vite, Axios, React Markdown.

```text
backend/       API routers, schemas, ingestion/RAG/vector services, extraction utilities
frontend/      React application, API client, styling
backend/documents/       reserved for optional original-file storage (currently files are processed in memory)
backend/vector_store/    persistent FAISS index and document registry (created when first file is indexed)
.env.example             configuration template; copy to .env
```

## Setup on Windows

Install Python 3.11+ and Node.js 20+; confirm `py -3.11 --version` and `node --version` work. From the project root in CMD:

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate
cd backend
pip install -r requirements.txt
cd ..
copy .env.example .env
notepad .env
```

Put your real key in `.env` as `OPENAI_API_KEY=...`. Never put it in frontend code. The sample model is `gpt-4o-mini`; change `OPENAI_CHAT_MODEL` to a model available to your account. Embeddings default to `text-embedding-3-small`.

Start the backend in one CMD window:

```cmd
cd backend
..\.venv\Scripts\activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in another CMD window:

```cmd
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Backend: <http://127.0.0.1:8000>; Swagger: <http://127.0.0.1:8000/docs>.

Configuration in `.env`: `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `MAX_UPLOAD_MB`, `VECTOR_STORE_DIR`, and `DOCUMENTS_DIR`. Set overlap smaller than chunk size. The current uploader supports files up to 20 MB each.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Service status |
| POST | `/api/documents/upload` | Multipart `files` field; accepts multiple PDF/DOCX/TXT files. Returns each ID and chunk count. |
| GET | `/api/documents` | Indexed file list and chunk totals |
| DELETE | `/api/documents/{document_id}` | Remove a file's vectors and registry record (rebuilds the index) |
| POST | `/api/chat` | JSON `{"question":"What is the approval process?","top_k":5}`; returns `answer` and source filename/page/content entries |

## Learning notes

**Embeddings** map text into numeric vectors where semantically related passages tend to be nearby. The question must use the same embedding model and vector dimensions as indexed text. **Chunking** keeps each embedding focused and makes retrieval useful for long files; overlap prevents a fact divided by a boundary from becoming hard to retrieve. **FAISS** stores and searches vectors efficiently on CPU. Here vectors are L2-normalized and inner-product ranking corresponds to cosine similarity. **Top-K** means “send the K best matching passages”; increasing K gives broader context but can add noise and consume more model context.

FAISS persistence uses LangChain's local pickle-backed docstore. The application enables LangChain deserialization only for the app-managed `backend/vector_store` path; never copy an untrusted index into that directory. Rebuilding on delete keeps the example simple and correct for small learning collections, though large libraries benefit from a deletion-capable index strategy. Original uploads are currently processed in memory rather than retained.

## Tests and troubleshooting

Run from `backend` after installing requirements: `python -m unittest discover -s tests`. The tests cover cleanup/chunk overlap, TXT extraction, API health/upload validation, and a mocked chat response. Real embedding/indexing and OpenAI calls incur API usage; exercise them manually with your own key.

- **Missing key / 503:** create `.env` from `.env.example`, set the key, restart Uvicorn.
- **No text in a PDF:** this parser needs a text PDF; scanned pages need OCR (not included).
- **Upload errors:** only PDF/DOCX/TXT, within `MAX_UPLOAD_MB`; check the Uvicorn log for extraction or OpenAI errors.
- **FAISS or dependency install errors:** use 64-bit Python 3.11+ and install from `backend/requirements.txt` in the active virtual environment.
- **Frontend cannot connect:** start FastAPI on port 8000; inspect browser console and the backend log.
- **Answers lack detail:** verify the file appears in the library and increase `top_k` carefully; inspect the returned source passages.


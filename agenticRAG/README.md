# Agentic RAG (NVIDIA NIM)

This folder contains a self-contained FastAPI service that demonstrates a simple agentic RAG loop built on NVIDIA NIM deployments.

## Features

- FastAPI + automatic Swagger UI (`/docs`).
- Loads PDF manuals from `agenticRAG/resources/`, chunks them, and stores them in an in-memory FAISS index.
- Retrieval → Plan → Response pipeline using a single Nemotron 9B v2 deployment (no task-specific prompt engineering yet).
- Uses NVIDIA embedding NIM for vectorization by default (or any compatible endpoint you configure).

## Setup

1. Install dependencies (preferably inside a virtual environment):

   ```bash
   pip install -r agenticRAG/requirements.txt
   ```

2. Configure environment variables:

   ```bash
   cp agenticRAG/.env.example agenticRAG/.env
   # edit agenticRAG/.env with your Brev/NIM deployments
   ```

   The app automatically loads `agenticRAG/.env` on startup. You can still override values via shell exports (they will win when provided). Set `NIM_USE_LEXICAL=true` if your deployment does not expose an embeddings endpoint.

3. Start the service:

   ```bash
   uvicorn agenticRAG.main:app --reload --port 9000
   ```

4. Open http://localhost:9000/docs to try the `/rag/query` endpoint directly in Swagger.

## API Overview

| Endpoint                 | Method | Description                                               |
| ------------------------ | ------ | --------------------------------------------------------- |
| `/`                      | GET    | Service metadata and quick links.                         |
| `/health`                | GET    | Confirms the index is built and returns counts.           |
| `/rag/query`             | POST   | Runs the agentic RAG pipeline.                            |
| `/rag/work-order`        | POST   | Accepts incident JSON (summary/description/etc.) and returns a work order. |
| `/resources`             | GET    | Lists PDFs found under `resources/` with page counts.     |
| `/resources/refresh`     | POST   | Re-reads PDFs and rebuilds the FAISS index.               |
| `/resources/ingest-text` | POST   | Sends raw text to be chunked and appended to the index.   |

### `/rag/query` schema

```json
{
  "question": "string",
  "top_k": 4
}
```

Response body includes the original question, the intermediate plan, the final answer, and the references pulled from the manuals.

## Adding More Documents

Drop PDF files into `agenticRAG/resources/`. Call `POST /resources/refresh` (or restart the server) to rebuild the index so the new documents become queryable. Use `GET /resources` to confirm they were detected. To ingest ad-hoc text without touching the filesystem, call `POST /resources/ingest-text` with `{ "text": "...", "source": "manual" }`.

## Notes

- The agent intentionally uses a neutral system prompt; tailor it later once you define the desired behavior.
- If you prefer a different embedding or chat deployment, override the environment variables accordingly.
### `/rag/work-order` schema

```json
{
  "summary": "GPU overheat on rack B2",
  "description": "GPU 4 ...",
  "priority": "High",
  "status": "To Do",
  "assignee": "Brian",
  "updated": "2025-11-09T04:03:55.387-0600",
  "top_k": 4
}
```

Returns the ticket echo, intermediate plan, structured `work_order`, and references used.

## Testing the Dynamic Work Orders stack

This guide shows how to validate the end‑to‑end flow: Jira → priority queue → LangGraph work order → technician updates.

### Prereqs
- Python 3.10+
- `backend/.env` configured for Jira and Brev (OpenAI‑compatible) keys
- Node 18+ for the frontend (optional)

### Backend smoke test

1. Install deps and run the API
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
2. In a new terminal, run the smoke script
   ```bash
   python -m backend.scripts.smoke_rag
   ```
   The script will:
   - POST `/workorders/refresh`
   - If the queue is empty, seed two manual tickets via `/rag/ingest/manual`
   - GET `/workorders/queue` and pick the top item
   - POST `/rag/work-orders` using the top `issue_id`
   - Mark the first step done and add a note
   - GET the work order detail and print a summary

Set a custom API base with `API_BASE=http://localhost:8001`.

### Manual curl flow

```bash
# Refresh registry
curl -X POST http://localhost:8000/workorders/refresh

# Check queue
curl http://localhost:8000/workorders/queue | jq .

# Generate a work order by numeric Jira id
curl -X POST http://localhost:8000/rag/work-orders \
  -H "Content-Type: application/json" \
  -d '{"issue_id":"10029","operator_notes":"Fans cleaned, still throttling"}' | jq .

# Update a step and add a note
curl -X POST http://localhost:8000/workorders/10029/steps -H 'Content-Type: application/json' -d '{"index":0,"status":"done"}'
curl -X POST http://localhost:8000/workorders/10029/notes -H 'Content-Type: application/json' -d '{"author":"Tech","note":"Loop flushed"}'
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # proxy forwards /workorders and /rag to backend
```
Open http://localhost:5173 and confirm:
- Queue loads from `/workorders/queue`
- Detail panel shows steps and notes; toggling a step calls `/workorders/{id}/steps`
- Assistant input posts to `/rag/work-orders` and appends responses


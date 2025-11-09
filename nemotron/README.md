# Nemotron Agentic RAG

This folder hosts a LangChain‑based agent that uses NVIDIA’s Nemotron‑4 9B v2 foundation model to convert Jira incidents and DGX user guides into executable work orders.

## 1. Prerequisites

1. Python 3.10+.
2. NVIDIA Cloud API key with access to Nemotron and embedding endpoints.
3. Existing backend (FastAPI) providing `/jira/list` or similar retrieval output.

Install dependencies:

```bash
cd nemotron
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Populate `.env`:

```
NVIDIA_API_KEY=nvapi-***
NVIDIA_NEMOTRON_MODEL=nvidia/nemotron-4-qa-9b-v2
NVIDIA_EMBED_MODEL=nvidia/nv-embedqa-e5-v5
```

## 2. Resources

`resources/` already contains DGX user guides (A100, H100, GB200). Add additional SOPs or PDFs here and re-run ingestion (`agent.ingest_guides(refresh=True)`).

## 3. Usage

```python
from agentic_rag import WorkOrderAgent, JiraBackendClient

agent = WorkOrderAgent()
agent.ingest_guides()

jira_client = JiraBackendClient(base_url="http://localhost:8000")
tickets = jira_client.list_recent(max_results=10)

result = agent.generate_work_order(
    tickets,
    operator_notes="Need fix before 18:00 UTC; ensure redundant GPU pool online."
)
print(result["work_order"])
```

### Updating instructions with user text

When technicians provide new context, call:

```python
agent.ingest_user_instruction("Liquid loop kit swapped to rev B...")  # persists to retriever
response = agent.interactive_update("Pressure dropped to 0.6 bar after flush.")
```

## 4. Data Flow

1. **Jira Retrieval Backend** → `JiraBackendClient` pulls incidents and `set_jira_context` caches them.
2. **Guide Corpus** → `ingest_guides` loads PDFs, splits, and stores vectors in Chroma.
3. **Agent Tools**  
   - `HardwareGuideSearch`: RetrievalQA over the vector store.  
   - `JiraContext`: On-demand dump of the latest tickets.  
4. **Nemotron Agent** (Zero-Shot ReAct) reasons across both tools and emits structured JSON.

## 5. Extending / Training

See `docs/RAG_SETUP.md` for broader training guidance. To specialize Nemotron 9B v2 on your ticket-to-work-order pairs, export JSONL prompts (ticket + notes) and responses (final work order) and fine-tune via NeMo/QLoRA, then set `NVIDIA_NEMOTRON_MODEL` to your custom endpoint.

## 6. CLI Entry Point

Run the module directly to test end-to-end:

```bash
python agentic_rag.py
```

The script will ingest guides (if not already persisted), fetch recent Jira tickets, and print a JSON work order.

"""End-to-end smoke test for the Dynamic Work Orders backend.

This script exercises:
- /workorders/refresh
- /workorders/queue
- /rag/work-orders (by issue_id if available, otherwise seeds manual data)
- /workorders/{id}/steps and /workorders/{id}/notes

Usage:
  python -m backend.scripts.smoke_rag  # API_BASE defaults to http://localhost:8000
  API_BASE=http://localhost:8001 python -m backend.scripts.smoke_rag
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import requests


API_BASE = os.getenv("API_BASE", "http://localhost:8000").rstrip("/")


def _post(path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    resp = requests.post(url, json=payload) if payload is not None else requests.post(url)
    if not resp.ok:
        print(f"ERROR {resp.status_code} for {path}:", resp.text)
    resp.raise_for_status()
    return resp.json()


def _get(path: str) -> Dict[str, Any] | List[Any]:
    url = f"{API_BASE}{path}"
    resp = requests.get(url)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:  # pragma: no cover
        return {"text": resp.text}


def ensure_seed_if_empty() -> None:
    """If queue is empty, seed two manual tickets to allow smoke to proceed."""
    queue = _get("/workorders/queue")
    if (isinstance(queue, dict) and queue.get("count", 0) > 0) or (
        isinstance(queue, list) and len(queue) > 0
    ):
        return
    print("Queue empty; seeding manual tickets ...")
    tickets = [
        {
            "key": "DWOS-SMOKE-1",
            "summary": "GPU rack A12 thermal drift",
            "description": "Sensors at 92C on boards 3–6. Bubbles in coolant.",
            "priority": "High",
            "status": "In Progress",
            "assignee": "Smoke Tester",
        },
        {
            "key": "DWOS-SMOKE-2",
            "summary": "Guide: liquid loop maintenance SOP",
            "description": "Bleed loop; replace QD seals; rebalance flow.",
            "priority": "Medium",
            "status": "Done",
            "assignee": "Smoke Tester",
        },
    ]
    _post("/rag/ingest/manual", {"tickets": tickets})
    _post("/workorders/refresh")


def main() -> int:
    print(f"API_BASE = {API_BASE}")
    # 1) Refresh registry
    refresh = _post("/workorders/refresh")
    print("/workorders/refresh →", refresh)

    # 2) Seed if needed
    ensure_seed_if_empty()

    # 3) Pull queue and pick top
    queue = _get("/workorders/queue")
    print("/workorders/queue →", json.dumps(queue, indent=2)[:800], "...")
    results = queue.get("results", []) if isinstance(queue, dict) else queue
    if not results:
        print("No work orders available after seeding; aborting.")
        return 1
    top = results[0]
    issue_id = top.get("jira_id") or top.get("id") or top.get("key")
    print("Top issue id:", issue_id)

    # 4) Generate work order via RAG
    gen = _post("/rag/work-orders", {"issue_id": issue_id, "operator_notes": "Smoke test notes"})
    print("/rag/work-orders →", json.dumps(gen, indent=2)[:800], "...")

    # 5) Toggle first step to done
    step_update = _post(f"/workorders/{issue_id}/steps", {"index": 0, "status": "done"})
    print("/workorders/{id}/steps →", step_update)

    # 6) Append a technician note
    note = _post(f"/workorders/{issue_id}/notes", {"author": "Smoke", "note": "Completed step 1"})
    print("/workorders/{id}/notes →", note)

    # 7) Show detail
    detail = _get(f"/workorders/{issue_id}")
    print("/workorders/{id} →", json.dumps(detail, indent=2)[:800], "...")
    print("Smoke test completed ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())

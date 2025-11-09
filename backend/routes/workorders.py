"""Routes for prioritised work order retrieval."""
from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/workorders", tags=["Work Orders"])

INTERNAL_API_BASE = os.getenv("INTERNAL_API_BASE_URL", "http://localhost:8000")
LIST_ENDPOINT = f"{INTERNAL_API_BASE.rstrip('/')}/jira/list"

PRIORITY_RANK = {
    "blocker": 0,
    "highest": 0,
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "lowest": 4,
}


def _fetch_all_issues() -> List[Dict[str, Any]]:
    try:
        response = requests.get(LIST_ENDPOINT, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network failure path
        raise HTTPException(status_code=502, detail=f"Failed to reach Jira list endpoint: {exc}") from exc
    payload = response.json()
    issues = payload.get("issues", payload)
    if not isinstance(issues, list):
        raise HTTPException(status_code=500, detail="Unexpected payload from /jira/list endpoint.")
    return issues


def _extract_priority_label(issue: Dict[str, Any]) -> str:
    if "priority" in issue:
        priority = issue["priority"]
    else:
        priority = issue.get("fields", {}).get("priority", {})
    if isinstance(priority, dict):
        return str(priority.get("name", "")).lower()
    return str(priority or "").lower()


def _priority_value(issue: Dict[str, Any]) -> int:
    return PRIORITY_RANK.get(_extract_priority_label(issue), len(PRIORITY_RANK))


@router.get("/sorted")
def fetch_sorted_workorders():
    """Fetch every Jira issue, sort by priority, and return the ordered list (id included)."""
    issues = _fetch_all_issues()
    ordered = sorted(issues, key=_priority_value)
    return {"count": len(ordered), "issues": ordered}


@router.get("/highest-priority-id")
def highest_priority_issue_id():
    """Return only the ID for the highest-priority issue."""
    issues = _fetch_all_issues()
    if not issues:
        raise HTTPException(status_code=404, detail="No Jira issues available.")
    highest = min(issues, key=_priority_value)
    issue_id = highest.get("id")
    if not issue_id:
        raise HTTPException(status_code=500, detail="Highest-priority issue is missing an ID.")
    return {"id": issue_id, "issue": highest}

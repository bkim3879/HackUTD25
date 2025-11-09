"""Work order enrichment, scoring, and technician updates."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from services import xjira_service

REQUIRED_FIELDS = ["summary", "description", "priority", "assignee"]

BASE_PRIORITY_WEIGHT = {
    "blocker": 1.0,
    "highest": 0.95,
    "critical": 0.9,
    "high": 0.8,
    "medium": 0.5,
    "low": 0.25,
    "lowest": 0.1,
}

KEYWORD_WEIGHTS = {
    "gpu": 0.3,
    "cool": 0.25,
    "thermal": 0.2,
    "power": 0.15,
    "network": 0.1,
    "maintenance": 0.05,
}

BASELINE_STEPS = [
    "Inspect sensor telemetry and confirm alert thresholds.",
    "Power cycle the affected server or sled if safe to do so.",
    "Verify airflow paths and clear obstructions.",
    "Validate coolant/air loop pressures before ramping load.",
]


def _keyword_score(text: str | None) -> float:
    if not text:
        return 0.0
    lowered = text.lower()
    return sum(weight for keyword, weight in KEYWORD_WEIGHTS.items() if keyword in lowered)


@dataclass
class WorkOrderRecord:
    key: str
    summary: str
    description: Optional[str]
    priority: Optional[str]
    status: Optional[str]
    assignee: Optional[str]
    updated: Optional[str]
    jira_id: Optional[str] = None
    missing_fields: List[str] = field(default_factory=list)
    score: float = 0.0
    steps: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[Dict[str, str]] = field(default_factory=list)
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "jira_id": self.jira_id,
            "summary": self.summary,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "assignee": self.assignee,
            "updated": self.updated,
            "missing_fields": self.missing_fields,
            "score": self.score,
            "steps": self.steps,
            "notes": self.notes,
            "completed": self.completed,
        }

    def context_text(self) -> str:
        blocks = [
            f"Ticket: {self.key}",
            f"Summary: {self.summary}",
            f"Priority: {self.priority}",
            f"Status: {self.status}",
        ]
        if self.assignee:
            blocks.append(f"Assignee: {self.assignee}")
        if self.description:
            blocks.append(f"Description: {self.description}")
        return "\n".join(blocks)


WORK_ORDER_REGISTRY: Dict[str, WorkOrderRecord] = {}


def _missing_fields(issue: Dict[str, Any]) -> List[str]:
    missing = []
    for field_name in REQUIRED_FIELDS:
        if not issue.get(field_name):
            missing.append(field_name)
    return missing


def _compute_score(issue: Dict[str, Any], missing: List[str]) -> float:
    priority = (issue.get("priority") or "low").lower()
    base = BASE_PRIORITY_WEIGHT.get(priority, 0.1)
    text = f"{issue.get('summary','')} {issue.get('description','')}"
    keyword_bonus = _keyword_score(text)
    missing_penalty = len(missing) * 0.05
    return round(max(0.0, base + keyword_bonus - missing_penalty), 3)


def _baseline_steps() -> List[Dict[str, Any]]:
    return [
        {"description": step, "status": "pending"}
        for step in BASELINE_STEPS
    ]


def refresh_work_orders() -> Dict[str, Any]:
    issues = xjira_service.search_issues()
    WORK_ORDER_REGISTRY.clear()
    for issue in issues:
        record = _build_record(issue)
        WORK_ORDER_REGISTRY[record.key] = record
    return {"count": len(WORK_ORDER_REGISTRY)}


def _build_record(issue: Dict[str, Any]) -> WorkOrderRecord:
    missing = _missing_fields(issue)
    score = _compute_score(issue, missing)
    status = issue.get("status")
    normalized_status = (status or "").strip().lower()
    is_completed = normalized_status in {"done", "closed", "resolved"}
    return WorkOrderRecord(
        key=issue["key"],
        jira_id=issue.get("id"),
        summary=issue.get("summary", ""),
        description=issue.get("description"),
        priority=issue.get("priority"),
        status=status,
        assignee=issue.get("assignee"),
        updated=issue.get("updated"),
        missing_fields=missing,
        score=score,
        steps=_baseline_steps(),
        completed=is_completed,
    )


def list_work_orders() -> List[Dict[str, Any]]:
    if not WORK_ORDER_REGISTRY:
        refresh_work_orders()
    ordered = sorted(
        WORK_ORDER_REGISTRY.values(),
        key=lambda record: record.score,
        reverse=True,
    )
    return [record.to_dict() for record in ordered]


def get_work_order(issue_id: str) -> Optional[WorkOrderRecord]:
    if not WORK_ORDER_REGISTRY:
        refresh_work_orders()
    for record in WORK_ORDER_REGISTRY.values():
        if record.jira_id == issue_id or record.key == issue_id:
            return record
    return None


def record_note(issue_id: str, author: str, note: str) -> Dict[str, Any]:
    record = get_work_order(issue_id)
    if not record:
        raise KeyError(f"Unknown work order {issue_id}")
    entry = {"author": author, "note": note, "timestamp": datetime.utcnow().isoformat()}
    record.notes.append(entry)
    return entry


def mark_step(issue_id: str, index: int, status: str) -> Dict[str, Any]:
    record = get_work_order(issue_id)
    if not record:
        raise KeyError(f"Unknown work order {issue_id}")
    if not (0 <= index < len(record.steps)):
        raise IndexError("Step index out of range")
    record.steps[index]["status"] = status
    return record.steps[index]


def mark_completed(issue_id: str) -> WorkOrderRecord:
    record = get_work_order(issue_id)
    if not record:
        raise KeyError(f"Unknown work order {issue_id}")
    record.completed = True
    return record

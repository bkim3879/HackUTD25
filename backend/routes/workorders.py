"""Work order orchestration routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from services import jira_service, workorder_service

router = APIRouter(prefix="/workorders", tags=["Work Orders"])


class NotePayload(BaseModel):
    author: str = Field(..., description="Technician or system adding the update.")
    note: str = Field(..., description="Details about the action taken or new telemetry.")


class StepUpdatePayload(BaseModel):
    index: int = Field(..., ge=0, description="Zero-based index of the step to update.")
    status: Literal["pending", "in_progress", "done"] = Field("done")


class CompletePayload(BaseModel):
    transition_name: str = Field("Done", description="Jira workflow transition to trigger.")
    resolution_comment: str | None = Field(
        None, description="Optional note posted back to Jira upon completion."
    )


class StartPayload(BaseModel):
    transition_name: str = Field(
        "21", description="Jira workflow transition (id or name) that represents In Progress."
    )


@router.post("/refresh")
def refresh_workorders():
    """Pull the latest Jira tickets and rebuild the work order registry."""
    summary = workorder_service.refresh_work_orders()
    return summary


@router.get("/queue")
def list_workorders():
    """Return work orders sorted by impact score."""
    records = workorder_service.list_work_orders()
    return {"count": len(records), "results": records}


@router.get("/highest")
def highest_priority():
    """Return the highest ranked work order."""
    orders = workorder_service.list_work_orders()
    if not orders:
        raise HTTPException(status_code=404, detail="No work orders available.")
    return orders[0]


@router.get("/{issue_id}")
def workorder_detail(issue_id: str):
    record = workorder_service.get_work_order(issue_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Work order {issue_id} not found.")
    return record.to_dict()


@router.post("/{issue_id}/notes")
def add_note(issue_id: str, payload: NotePayload):
    try:
        entry = workorder_service.record_note(issue_id, payload.author, payload.note)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "note recorded", "entry": entry}


@router.post("/{issue_id}/steps")
def update_step(issue_id: str, payload: StepUpdatePayload):
    try:
        step = workorder_service.mark_step(issue_id, payload.index, payload.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IndexError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "step updated", "step": step}


@router.post("/{issue_id}/complete")
def complete_workorder(issue_id: str, payload: CompletePayload):
    try:
        record = workorder_service.mark_completed(issue_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    jira_transition = jira_service.transition_issue(issue_id, payload.transition_name)
    response = {"work_order": record.to_dict(), "jira_transition": jira_transition}
    if payload.resolution_comment:
        workorder_service.record_note(issue_id, "system", payload.resolution_comment)
    return response


@router.post("/{issue_id}/start")
def start_workorder(issue_id: str, payload: StartPayload):
    try:
        record = workorder_service.mark_in_progress(issue_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    jira_transition = jira_service.transition_issue(issue_id, payload.transition_name)
    return {"work_order": record.to_dict(), "jira_transition": jira_transition}

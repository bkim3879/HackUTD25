"""FastAPI routes exposing Jira Cloud helpers."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from requests import HTTPError

from services import jira_service

router = APIRouter(prefix="/jira", tags=["Jira"])


class CreateIssuePayload(BaseModel):
    summary: str = Field(..., description="Issue summary shown in Jira")
    description: str = Field(..., description="Markdown/ADF-friendly description")
    issue_type: str = Field("Task", description="Jira issue type name")
    priority: str = Field("Medium", description="Jira priority label")


class CreateSprintIssuePayload(CreateIssuePayload):
    sprint_id: int = Field(..., description="Sprint identifier from Agile API")


class TransitionPayload(BaseModel):
    transition_id: str = Field(..., description="Transition ID returned by /transitions")


def _handle_error(err: Exception) -> None:
    status = 502
    detail = str(err)
    if isinstance(err, HTTPError) and err.response is not None:
        status = err.response.status_code
        detail = err.response.text or detail
    raise HTTPException(status_code=status, detail=detail)


@router.get("/list")
def list_all_issues():
    try:
        return jira_service.get_all_issues()
    except Exception as err:
        _handle_error(err)

@router.get("/listissue")
def list_issue(issue_key: str = Query(..., description="Exact Jira issue key (e.g., DWOS-118)")):
    try:
        return jira_service.get_issue(issue_key)
    except Exception as err:
        _handle_error(err)

@router.post("/transition")
def transition_issue(issue_key: str, transition_name: str):
    try:
        return jira_service.transition_issue(issue_key, transition_name)
    except Exception as err:  # pragma: no cover
        _handle_error(err)


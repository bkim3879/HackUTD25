"""Routes exposing Nemotron RAG helpers."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from services.rag_service import DependencyNotInstalled, rag_service


router = APIRouter(prefix="/rag", tags=["RAG"])


class ManualIngestPayload(BaseModel):
    tickets: list[dict] = Field(..., description="Raw ticket dictionaries to seed the vector store.")


class GeneratePayload(BaseModel):
    incident_summary: str | None = Field(
        None, description="Short natural language description of the incident."
    )
    issue_id: str | None = Field(
        None, description="Existing Jira issue id to base the work order on."
    )
    issue_key: str | None = Field(
        None, description="Legacy Jira issue key for backward compatibility."
    )
    desired_outcome: str | None = Field(
        None, description="Optional target outcome (e.g., restore service, finish audit)."
    )
    top_k: int | None = Field(
        None, ge=1, le=10, description="Override retrieval depth for this request."
    )
    operator_notes: str | None = Field(
        None, description="Optional technician notes to seed the work order."
    )

    @model_validator(mode="after")
    def validate_sources(self):
        if not self.incident_summary and not (self.issue_id or self.issue_key):
            raise ValueError("Provide either incident_summary or issue_id/issue_key.")
        return self


def _handle_error(err: Exception) -> None:
    if isinstance(err, DependencyNotInstalled):
        raise HTTPException(status_code=500, detail=str(err))
    if isinstance(err, ValueError):
        raise HTTPException(status_code=400, detail=str(err))
    raise HTTPException(status_code=502, detail=str(err))


@router.post("/ingest/jira")
def ingest_from_jira():
    try:
        return rag_service.ingest_jira()
    except Exception as err:  # pragma: no cover
        _handle_error(err)


@router.post("/ingest/manual")
def ingest_manual(payload: ManualIngestPayload):
    try:
        return rag_service.ingest_manual(payload.tickets)
    except Exception as err:  # pragma: no cover
        _handle_error(err)


@router.post("/work-orders")
def generate_work_order(payload: GeneratePayload):
    try:
        return rag_service.generate_work_order(
            incident_summary=payload.incident_summary,
            desired_outcome=payload.desired_outcome,
            top_k=payload.top_k,
            issue_id=payload.issue_id,
            legacy_issue_key=payload.issue_key,
            operator_notes=payload.operator_notes,
        )
    except Exception as err:  # pragma: no cover
        _handle_error(err)

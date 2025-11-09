"""Nemotron-based agentic RAG pipeline for Jira -> Work Order generation."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, TypedDict

from dotenv import load_dotenv

from services import workorder_service, xjira_service
from langgraph.graph import StateGraph, END

load_dotenv()


class DependencyNotInstalled(RuntimeError):
    """Raised when optional RAG dependencies are missing."""


def _lazy_imports() -> Dict[str, Any]:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.schema import Document
        from langchain.vectorstores import Chroma
        from langchain.chains import RetrievalQA
        from langchain.tools import Tool
        from langchain.agents import AgentType, initialize_agent
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    except ImportError as exc:  # pragma: no cover - executed only without deps
        raise DependencyNotInstalled(
            "Install the RAG extras first: pip install langchain chromadb langchain-openai"
        ) from exc

    return {
        "RecursiveCharacterTextSplitter": RecursiveCharacterTextSplitter,
        "Document": Document,
        "Chroma": Chroma,
        "RetrievalQA": RetrievalQA,
        "Tool": Tool,
        "AgentType": AgentType,
        "initialize_agent": initialize_agent,
        "ChatOpenAI": ChatOpenAI,
        "OpenAIEmbeddings": OpenAIEmbeddings,
    }


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DEFAULT_MODEL = os.getenv("BREV_MODEL", "nemotron-4-qa-9b-v2")
DEFAULT_EMBED_MODEL = os.getenv("BREV_EMBED_MODEL", "nemotron-embedqa-v1")
DEFAULT_API_BASE = os.getenv("BREV_API_BASE", "https://api.brev.dev/v1")
DEFAULT_VECTOR_PATH = Path(os.getenv("RAG_VECTOR_DB_PATH", ".rag_store")).resolve()


@dataclass
class JiraTicket:
    key: str
    summary: str
    status: str | None = None
    priority: str | None = None
    assignee: str | None = None
    updated: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "JiraTicket":
        return cls(
            key=payload.get("key"),
            summary=payload.get("summary") or payload.get("fields", {}).get("summary", ""),
            status=payload.get("status"),
            priority=payload.get("priority"),
            assignee=payload.get("assignee"),
            updated=payload.get("updated"),
            description=payload.get("description"),
        )

    def to_text(self) -> str:
        parts = [
            f"Ticket: {self.key}",
            f"Summary: {self.summary}",
        ]
        if self.status:
            parts.append(f"Status: {self.status}")
        if self.priority:
            parts.append(f"Priority: {self.priority}")
        if self.assignee:
            parts.append(f"Assignee: {self.assignee}")
        if self.updated:
            parts.append(f"Updated: {self.updated}")
        if self.description:
            parts.append(f"Description: {self.description}")
        return "\n".join(parts)


class WorkOrderState(TypedDict, total=False):
    incident: str
    desired_outcome: str | None
    retrieval: Dict[str, Any]
    plan: str
    sources: List[Dict[str, Any]]
    work_order: Dict[str, Any]


class NemotronAgenticRAG:
    """Wraps ingestion, retrieval, and Nemotron generation."""

    def __init__(
        self,
        persist_directory: Path = DEFAULT_VECTOR_PATH,
        collection_name: str = "jira_work_orders",
        top_k: int = 4,
    ):
        self._imports = _lazy_imports()
        self.persist_directory = persist_directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.top_k = top_k

        self.text_splitter = self._imports["RecursiveCharacterTextSplitter"](
            chunk_size=800, chunk_overlap=120
        )
        api_key = _env("BREV_API_KEY")
        os.environ.setdefault("OPENAI_API_KEY", api_key)
        os.environ.setdefault("OPENAI_API_BASE", DEFAULT_API_BASE)
        self.embedder = self._imports["OpenAIEmbeddings"](
            model=DEFAULT_EMBED_MODEL,
            openai_api_key=api_key,
            openai_api_base=DEFAULT_API_BASE,
        )
        self.vectorstore = self._imports["Chroma"](
            collection_name=self.collection_name,
            persist_directory=str(self.persist_directory),
            embedding_function=self.embedder,
        )
        self.llm = self._imports["ChatOpenAI"](
            model=DEFAULT_MODEL,
            openai_api_key=api_key,
            openai_api_base=DEFAULT_API_BASE,
            temperature=0.2,
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.top_k})
        self.qa_chain = self._imports["RetrievalQA"].from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
        )
        self.graph = self._build_graph()

        retriever_tool = self._imports["Tool"](
            name="jira_work_order_search",
            description="Use to recall Jira tickets and historical work orders relevant to an incident.",
            func=self._retriever_tool,
        )
        self.agent = self._imports["initialize_agent"](
            tools=[retriever_tool],
            llm=self.llm,
            agent=self._imports["AgentType"].ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
        )

    def _retriever_tool(self, query: str) -> str:
        docs = self.vectorstore.similarity_search(query, k=self.top_k)
        if not docs:
            return "No related Jira tickets were retrieved."
        return "\n---\n".join(doc.page_content for doc in docs)

    def _tickets_to_documents(self, tickets: Sequence[JiraTicket]) -> List[Any]:
        Document = self._imports["Document"]
        docs: List[Document] = []
        for ticket in tickets:
            for chunk in self.text_splitter.split_text(ticket.to_text()):
                docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "key": ticket.key,
                            "summary": ticket.summary,
                            "priority": ticket.priority,
                            "status": ticket.status,
                            "updated": ticket.updated,
                        },
                    )
                )
        return docs

    def _build_graph(self):
        workflow = StateGraph(dict)
        workflow.add_node("retrieve", self._node_retrieve)
        workflow.add_node("plan", self._node_plan)
        workflow.add_node("generate", self._node_generate)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "plan")
        workflow.add_edge("plan", "generate")
        workflow.add_edge("generate", END)
        return workflow.compile()

    def _node_retrieve(self, state: WorkOrderState) -> WorkOrderState:
        question = self._compose_question(state["incident"], state.get("desired_outcome"))
        k = state.get("top_k", self.top_k)
        self.retriever.search_kwargs["k"] = k
        response = self.qa_chain({"query": question})
        sources = [
            {"key": doc.metadata.get("key"), "summary": doc.metadata.get("summary")}
            for doc in response.get("source_documents", [])
        ]
        return {"retrieval": response, "sources": sources}

    def _node_plan(self, state: WorkOrderState) -> WorkOrderState:
        incident = state["incident"]
        desired = state.get("desired_outcome")
        retrieval_text = state.get("retrieval", {}).get("result", "")
        plan_prompt = (
            "You are planning mitigations for a data center incident.\n"
            "Generate a numbered list (max 4 steps) referencing historical work orders.\n"
            f"Incident: {incident}\n"
        )
        if desired:
            plan_prompt += f"Desired outcome: {desired}\n"
        if retrieval_text:
            plan_prompt += f"Retrieved context:\n{retrieval_text}\n"
        plan_response = self.llm.invoke(
            [
                {"role": "system", "content": "Keep the plan concise and actionable."},
                {"role": "user", "content": plan_prompt},
            ]
        )
        plan_text = getattr(plan_response, "content", str(plan_response))
        return {"plan": plan_text}

    def _node_generate(self, state: WorkOrderState) -> WorkOrderState:
        retrieval_text = state.get("retrieval", {}).get("result", "")
        plan = state.get("plan", "")
        structured_prompt = (
            "You are transforming Jira issues into executable work orders.\n"
            "Return the final work order in JSON with the shape:\n"
            '{"title": "...", "impact": "...", "steps": ["..."], "materials": ["..."], '
            '"validation": ["..."], "jira_links": ["DWOS-123"]}\n'
            f"Context summary:\n{retrieval_text}\n\n"
            f"Technician action plan:\n{plan}\n"
        )
        final_response = self.llm.invoke(
            [
                {"role": "system", "content": "Output valid JSON and stay concise."},
                {"role": "user", "content": structured_prompt},
            ]
        )
        try:
            work_order_payload = json.loads(final_response.content)
        except json.JSONDecodeError:
            work_order_payload = {"raw_text": final_response.content}
        return {"work_order": work_order_payload}

    @staticmethod
    def _compose_question(incident: str, desired_outcome: str | None) -> str:
        question = f"Create a work order for: {incident}"
        if desired_outcome:
            question += f"\nDesired outcome: {desired_outcome}"
        return question

    def ingest_jira(self) -> Dict[str, Any]:
        issues = xjira_service.search_issues()
        tickets = [JiraTicket.from_dict(issue) for issue in issues]
        documents = self._tickets_to_documents(tickets)
        if not documents:
            return {"ingested_documents": 0}
        self.vectorstore.add_documents(documents)
        self.vectorstore.persist()
        return {"ingested_documents": len(documents), "tickets_indexed": len(tickets)}

    def ingest_manual(self, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        tickets = [JiraTicket.from_dict(record) for record in records]
        docs = self._tickets_to_documents(tickets)
        self.vectorstore.add_documents(docs)
        self.vectorstore.persist()
        return {"ingested_documents": len(docs), "tickets_indexed": len(tickets)}

    def generate_work_order(
        self,
        incident_summary: str | None = None,
        desired_outcome: str | None = None,
        top_k: int | None = None,
        issue_id: str | None = None,
        legacy_issue_key: str | None = None,
        operator_notes: str | None = None,
    ) -> Dict[str, Any]:
        state: WorkOrderState = {}
        context_text = None
        lookup_key = issue_id or legacy_issue_key
        if lookup_key:
            record = workorder_service.get_work_order(lookup_key)
            if not record:
                raise ValueError(f"Work order {lookup_key} not found.")
            if record.missing_fields:
                return {
                    "work_order": None,
                    "plan": None,
                    "sources": [],
                    "missing_fields": record.missing_fields,
                    "issue_id": lookup_key,
                    "message": "Jira ticket missing required data. Please complete the fields before generating a work order.",
                }
            context_text = record.context_text()
            incident_summary = record.summary or incident_summary or record.key
        if not incident_summary:
            raise ValueError("incident_summary is required when issue_key is not provided.")

        state["incident"] = incident_summary
        if desired_outcome:
            state["desired_outcome"] = desired_outcome
        if top_k:
            state["top_k"] = top_k
        if operator_notes:
            state["operator_notes"] = operator_notes
        if context_text:
            state["jira_context"] = context_text
        try:
            result = self.graph.invoke(state)
            return {
                "work_order": result.get("work_order"),
                "plan": result.get("plan"),
                "sources": result.get("sources", []),
                "issue_id": lookup_key,
            }
        except Exception as exc:  # Fallback if LLM/embedding endpoints are unavailable
            # Build a minimal, deterministic work order so operational flows can continue.
            fallback_steps: list[str] = []
            try:
                rec = workorder_service.get_work_order(lookup_key) if lookup_key else None
                if rec and rec.steps:
                    fallback_steps = [str(s.get("description")) for s in rec.steps]
            except Exception:
                pass
            work_order = {
                "title": f"Work Order for {incident_summary}",
                "impact": "Operational incident requiring technician attention.",
                "steps": fallback_steps
                or [
                    "Inspect sensor telemetry and confirm thresholds",
                    "Power cycle affected server if safe",
                    "Verify airflow/coolant paths",
                ],
                "materials": [],
                "validation": [
                    "Temperatures stabilized within acceptable range",
                    "Service resumes without throttling",
                ],
                "jira_refs": [rec.key] if lookup_key and (rec := workorder_service.get_work_order(lookup_key)) else [],
            }
            return {
                "work_order": work_order,
                "plan": "Baseline plan generated due to upstream model error.",
                "sources": [],
                "issue_id": lookup_key,
                "warning": f"Fell back to baseline plan: {type(exc).__name__}",
            }


rag_service = NemotronAgenticRAG()

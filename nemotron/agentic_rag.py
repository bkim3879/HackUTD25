"""Agentic RAG pipeline powered by Nemotron 9B v2 for DWOS work orders."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import requests
from dotenv import load_dotenv

from langchain.agents import AgentType, initialize_agent
from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool
from langchain.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings

load_dotenv(dotenv_path=Path(__file__).with_suffix(".env"))


@dataclass
class JiraTicket:
    """Lightweight representation of tickets returned by the Jira backend API."""

    key: str
    summary: str
    status: str | None = None
    priority: str | None = None
    assignee: str | None = None
    updated: str | None = None
    description: str | None = None

    @classmethod
    def from_backend(cls, ticket: Dict[str, Any]) -> "JiraTicket":
        fields = ticket.get("fields", {})
        return cls(
            key=ticket.get("key") or fields.get("key", ""),
            summary=ticket.get("summary") or fields.get("summary", ""),
            status=ticket.get("status") or fields.get("status"),
            priority=ticket.get("priority") or fields.get("priority"),
            assignee=ticket.get("assignee") or fields.get("assignee"),
            updated=ticket.get("updated") or fields.get("updated"),
            description=ticket.get("description") or fields.get("description"),
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
            parts.append("Description:")
            parts.append(self.description)
        return "\n".join(parts)


@dataclass
class JiraBackendClient:
    """Simple HTTP client to pull tickets from the existing backend API."""

    base_url: str = "http://localhost:8000"

    def list_recent(self, jql: str | None = None, max_results: int = 25) -> List[JiraTicket]:
        url = f"{self.base_url.rstrip('/')}/jira/list"
        params: Dict[str, Any] = {"max_results": max_results, "fetch_all": False}
        if jql:
            params["jql"] = jql
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        issues = payload.get("issues", payload)
        return [JiraTicket.from_backend(issue) for issue in issues]


class WorkOrderAgent:
    """Agentic RAG wrapper that merges Jira payloads with hardware user guides."""

    def __init__(
        self,
        resource_dir: Path | None = None,
        persist_dir: Path | None = None,
        collection_name: str = "dwos_guides",
        top_k: int = 4,
        model: str | None = None,
        embed_model: str | None = None,
    ):
        self.resource_dir = resource_dir or Path(__file__).parent / "resources"
        self.persist_dir = persist_dir or (Path(__file__).parent / ".vector_store")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.top_k = top_k
        self.model = model or os.getenv("NVIDIA_NEMOTRON_MODEL", "nvidia/nemotron-4-qa-9b-v2")
        self.embed_model = embed_model or os.getenv("NVIDIA_EMBED_MODEL", "nvidia/nv-embedqa-e5-v5")

        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("Missing NVIDIA_API_KEY in nemotron/.env")

        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
        self.embedder = NVIDIAEmbeddings(model=self.embed_model, api_key=api_key)
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedder,
            persist_directory=str(self.persist_dir),
        )
        self.llm = ChatNVIDIA(model=self.model, api_key=api_key, temperature=0.15)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.top_k})
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
        )

        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.jira_context: str = "No Jira context has been provided yet."
        self.agent = initialize_agent(
            tools=self._build_tools(),
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            memory=self.memory,
        )

    # ------------------------------------------------------------------ ingestion
    def ingest_guides(self, refresh: bool = False) -> Dict[str, Any]:
        """Load PDFs under resources/ and add them to the vector store."""
        docs: List[Document] = []
        for pdf in sorted(self.resource_dir.glob("*.pdf")):
            loader = PyPDFLoader(str(pdf))
            for page in loader.load():
                docs.append(
                    Document(
                        page_content=page.page_content,
                        metadata={"source": pdf.name, "page": page.metadata.get("page", 0)},
                    )
                )
        if not docs:
            return {"ingested": 0, "message": "No PDFs found."}

        if refresh:
            self.vectorstore.delete_collection()
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedder,
                persist_directory=str(self.persist_dir),
            )

        chunks = []
        for doc in docs:
            for chunk in self.text_splitter.split_text(doc.page_content):
                chunks.append(Document(page_content=chunk, metadata=doc.metadata))

        self.vectorstore.add_documents(chunks)
        self.vectorstore.persist()
        return {"ingested": len(chunks), "sources": sorted({doc.metadata["source"] for doc in docs})}

    def ingest_user_instruction(self, text: str, author: str = "operator") -> Dict[str, Any]:
        """Allow run-time instructions to become part of the retrieval store."""
        meta = {"source": f"user_{author}"}
        documents = [
            Document(page_content=chunk, metadata=meta)
            for chunk in self.text_splitter.split_text(text)
        ]
        self.vectorstore.add_documents(documents)
        self.vectorstore.persist()
        return {"ingested": len(documents), "author": author}

    def set_jira_context(self, tickets: Sequence[JiraTicket]) -> None:
        """Cache textified Jira issues for the JiraContext tool."""
        if not tickets:
            self.jira_context = "No Jira issues supplied."
            return
        sections = []
        for ticket in tickets:
            sections.append(ticket.to_text())
        self.jira_context = "\n\n---\n\n".join(sections)

    # tools
    def _build_tools(self) -> List[Tool]:
        guide_tool = Tool(
            name="HardwareGuideSearch",
            description=(
                "Use to look up GPU/Server maintenance instructions, BOMs, "
                "and procedural steps from DGX user guides."
            ),
            func=lambda query: self.qa_chain.run(query),
        )

        jira_tool = Tool(
            name="JiraContext",
            description="Call this to review the latest Jira tickets before drafting work orders.",
            func=lambda _: self.jira_context,
        )

        return [guide_tool, jira_tool]

    # work order generation
    def generate_work_order(
        self,
        tickets: Sequence[JiraTicket],
        operator_notes: str | None = None,
    ) -> Dict[str, Any]:
        """Turn Jira payload + instructions into a structured work order."""
        self.set_jira_context(tickets)
        operator_section = f"Operator notes:\n{operator_notes}\n" if operator_notes else ""
        prompt = (
            "You are the Dynamic Work Order agent for a hyperscale data center.\n"
            "Use the available tools to ground every instruction:\n"
            "- HardwareGuideSearch: DGX user guides and SOPs.\n"
            "- JiraContext: latest Jira incidents that must be turned into a work order.\n"
            "Return a valid JSON object with the shape:\n"
            '{\n  "title": str,\n  "summary": str,\n  "impact": str,\n'
            '  "steps": [str],\n  "materials": [str],\n  "validation": [str],\n'
            '  "jira_refs": [str]\n}\n'
            "Each step must be actionable (verb + object) and if hardware models are involved, "
            "cite the relevant guide.\n"
            f"{operator_section}"
            "Begin when ready."
        )
        response = self.agent.run(prompt)
        try:
            payload = json.loads(response)
        except json.JSONDecodeError:
            payload = {"raw_text": response}
        return {
            "work_order": payload,
            "jira_context": self.jira_context,
            "notes": operator_notes,
        }

    def interactive_update(self, user_text: str) -> str:
        """Use the guides + new info to return updated instructions."""
        self.ingest_user_instruction(user_text, author="live_input")
        follow_up_prompt = (
            "You just received new field intel from a technician. "
            "Summarize the delta and produce an updated step-by-step plan. "
            "Ensure the plan references any guidance retrieved from the corpus."
        )
        return self.agent.run(f"{follow_up_prompt}\nNew info:\n{user_text}")


if __name__ == "__main__":
    agent = WorkOrderAgent()
    agent.ingest_guides()
    jira_client = JiraBackendClient()
    tickets = jira_client.list_recent(max_results=5)
    result = agent.generate_work_order(tickets, operator_notes="Stabilize rack A12 before peak load.")
    print(json.dumps(result, indent=2))

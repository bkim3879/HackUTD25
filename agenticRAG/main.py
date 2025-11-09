"""Minimal FastAPI Agentic RAG service backed by NVIDIA NIMs."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document
    from langchain.vectorstores import FAISS
    from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - clear error during startup
    raise RuntimeError(
        "Missing dependencies for agenticRAG. Install with: pip install -r agenticRAG/requirements.txt"
    ) from exc


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env", override=False)

class QueryPayload(BaseModel):
    question: str = Field(..., description="Free-form question or task prompt for the agent.")
    top_k: int | None = Field(
        None,
        ge=1,
        le=12,
        description="Override how many context chunks to retrieve (defaults to 4).",
    )


class TextIngestPayload(BaseModel):
    text: str = Field(..., description="Raw text to ingest into the RAG index.")
    source: str | None = Field(None, description="Friendly name for provenance metadata.")
    page: int | None = Field(None, description="Optional page/section indicator saved in metadata.")


class AgenticRAG:
    """Lightweight two-step (plan + respond) agent grounded in local resources."""

    def __init__(
        self,
        resource_dir: Path,
        nim_api_key: str,
        nim_api_base: str,
        nim_llm_model: str,
        nim_embed_model: str,
        top_k: int = 4,
    ) -> None:
        self.resource_dir = resource_dir
        self.top_k = top_k
        self.documents: List[Document] = []
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
        self.embedder = NVIDIAEmbeddings(model=nim_embed_model, api_key=nim_api_key, base_url=nim_api_base)
        self.llm = ChatNVIDIA(
            model=nim_llm_model,
            api_key=nim_api_key,
            base_url=nim_api_base,
            temperature=0.2,
            top_p=0.7,
            max_tokens=768,
        )
        self.vectorstore = self._build_vectorstore()

    def _build_vectorstore(self):
        documents = self._load_documents()
        if not documents:
            raise RuntimeError(
                f"No PDF resources found in {self.resource_dir}. Add documents before starting the service."
            )
        self.documents = documents
        return FAISS.from_documents(documents, self.embedder)

    def refresh_resources(self) -> int:
        self.vectorstore = self._build_vectorstore()
        return len(self.documents)

    def resource_inventory(self) -> List[dict]:
        inventory: List[dict] = []
        for pdf_path in sorted(self.resource_dir.glob("*.pdf")):
            info = {"file": pdf_path.name}
            try:
                reader = PdfReader(str(pdf_path))
                info["pages"] = len(reader.pages)
            except Exception:
                info["pages"] = None
            inventory.append(info)
        return inventory

    def _load_documents(self) -> List[Document]:
        docs: List[Document] = []
        for pdf_path in sorted(self.resource_dir.glob("*.pdf")):
            try:
                reader = PdfReader(str(pdf_path))
            except Exception:
                continue
            for page_idx, page in enumerate(reader.pages, start=1):
                try:
                    text = (page.extract_text() or "").strip()
                except Exception:
                    text = ""
                if not text:
                    continue
                for chunk in self.text_splitter.split_text(text):
                    docs.append(
                        Document(
                            page_content=chunk,
                            metadata={"source": pdf_path.name, "page": page_idx},
                        )
                    )
        return docs

    def ingest_text(self, text: str, source: str | None = None, page: int | None = None) -> int:
        if not text or not text.strip():
            raise ValueError("text payload must be non-empty")
        chunks = self.text_splitter.split_text(text)
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "source": source or "manual_text",
                    "page": page,
                },
            )
            for chunk in chunks
        ]
        if not documents:
            raise ValueError("text did not produce any chunks")
        self.documents.extend(documents)
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(documents, self.embedder)
        else:
            self.vectorstore.add_documents(documents)
        return len(documents)

    def _retrieve(self, question: str, top_k: int) -> List[Document]:
        return self.vectorstore.similarity_search(question, k=top_k)

    def _plan(self, question: str, context: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "You are an analytical planner. Outline how you would answer the user question.",
            },
            {
                "role": "user",
                "content": f"Question: {question}\nContext:\n{context}\nProvide a short bullet plan.",
            },
        ]
        response = self.llm.invoke(messages)
        return getattr(response, "content", str(response))

    def _respond(self, question: str, context: str, plan: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "You are a professional data center technician assistant. Use the provided plan and context to answer the user's question clearly and concisely.",
            },
            {
                "role": "user",
                "content": f"Question: {question}\nPlan:\n{plan}\nContext:\n{context}\nRespond clearly.",
            },
        ]
        response = self.llm.invoke(messages)
        return getattr(response, "content", str(response))

    def run(self, question: str, top_k: int | None = None) -> dict:
        if not question.strip():
            raise ValueError("Question must be non-empty.")
        k = top_k or self.top_k
        docs = self._retrieve(question, k)
        if not docs:
            raise RuntimeError("No relevant context found. Add more documents to resources/")
        context = "\n\n".join(
            f"[{idx+1}] ({doc.metadata.get('source')} p.{doc.metadata.get('page')})\n{doc.page_content}"
            for idx, doc in enumerate(docs)
        )
        plan = self._plan(question, context)
        answer = self._respond(question, context, plan)
        references = [
            {
                "source": doc.metadata.get("source"),
                "page": doc.metadata.get("page"),
            }
            for doc in docs
        ]
        return {"question": question, "plan": plan, "answer": answer, "references": references}


@lru_cache(maxsize=1)
def build_agent() -> AgenticRAG:
    resource_dir = Path(__file__).resolve().parent / "resources"
    api_key = os.getenv("NIM_API_KEY", "brev_api_-35DV28tOosEzIPqAC1NfJ3KxyLD")
    if not api_key:
        raise RuntimeError("Missing NIM_API_KEY environment variable.")
    api_base = os.getenv("NIM_API_BASE", "https://api.brev.dev/v1")
    llm_model = os.getenv(
        "NIM_LLM_MODEL",
        "nvcf:nvidia/nemotron-nano-9b-v2:dep-35Exc02ogoBWiKIbr98m0CmSo5w",
    )
    embed_model = os.getenv("NIM_EMBED_MODEL", "nvidia/embedding-2.0")
    top_k = int(os.getenv("NIM_TOP_K", "4"))
    return AgenticRAG(
        resource_dir=resource_dir,
        nim_api_key=api_key,
        nim_api_base=api_base,
        nim_llm_model=llm_model,
        nim_embed_model=embed_model,
        top_k=top_k,
    )


app = FastAPI(
    title="Agentic RAG (NVIDIA NIM)",
    description="Simple FastAPI service demonstrating planning + retrieval + response using Nemotron 9B v2.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Service metadata")
def root():
    return {
        "message": "Agentic RAG service operational",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.post("/rag/query", summary="Run Agentic RAG", response_description="Plan + answer + references")
def rag_query(payload: QueryPayload):
    try:
        agent = build_agent()
        return agent.run(question=payload.question, top_k=payload.top_k)
    except Exception as err:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.get("/health", summary="Basic health check")
def health_check():
    try:
        agent = build_agent()
        return {
            "status": "ok",
            "documents_indexed": agent.vectorstore.index.ntotal if agent.vectorstore else 0,
            "top_k": agent.top_k,
        }
    except Exception as err:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.get("/resources", summary="List available PDF resources")
def list_resources():
    try:
        agent = build_agent()
        return {
            "files": agent.resource_inventory(),
            "chunks_indexed": len(agent.documents),
            "top_k": agent.top_k,
        }
    except Exception as err:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.post("/resources/refresh", summary="Rebuild index from resources folder")
def refresh_resources():
    try:
        agent = build_agent()
        chunks = agent.refresh_resources()
        return {
            "message": "resources reloaded",
            "chunks_indexed": chunks,
            "files": agent.resource_inventory(),
        }
    except Exception as err:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.post("/resources/ingest-text", summary="Ingest arbitrary text into the index")
def ingest_text(payload: TextIngestPayload):
    try:
        agent = build_agent()
        chunks = agent.ingest_text(payload.text, source=payload.source, page=payload.page)
        return {
            "message": "text ingested",
            "chunks_added": chunks,
            "total_chunks": len(agent.documents),
        }
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except Exception as err:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(err)) from err


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agenticRAG.main:app", host="0.0.0.0", port=9000, reload=True)

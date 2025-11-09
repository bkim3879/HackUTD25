// Prefer relative URLs so Vite dev proxy (or same-origin) handles requests.
// Override with VITE_API_BASE when deploying behind a different origin.
const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");
const AGENTIC_BASE = (import.meta.env.VITE_AGENTIC_RAG_BASE ?? "http://localhost:9000").replace(/\/$/, "");

async function handleResponse(response) {
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    const message = detail?.detail || response.statusText || "Unknown error";
    throw new Error(message);
  }
  return response.json();
}

export async function fetchWorkorders() {
  const response = await fetch(`${API_BASE}/workorders/queue`);
  return handleResponse(response);
}

export async function refreshWorkorders() {
  const response = await fetch(`${API_BASE}/workorders/refresh`, { method: "POST" });
  return handleResponse(response);
}

export async function fetchWorkorderDetail(issueIdOrKey) {
  const response = await fetch(`${API_BASE}/workorders/${issueIdOrKey}`);
  return handleResponse(response);
}

export async function addTechnicianNote(issueKey, author, note) {
  const response = await fetch(`${API_BASE}/workorders/${issueKey}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ author, note }),
  });
  return handleResponse(response);
}

export async function updateWorkorderStep(issueKey, index, status) {
  const response = await fetch(`${API_BASE}/workorders/${issueKey}/steps`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index, status }),
  });
  return handleResponse(response);
}

export async function generateWorkorderUpdate(issueId, operatorNotes, legacyKey, context = null) {
  const parts = [];
  const identifier = context?.key || legacyKey || issueId;
  if (identifier) parts.push(`Work Order: ${identifier}`);
  if (context?.summary) parts.push(`Summary: ${context.summary}`);
  if (context?.description) parts.push(`Description: ${context.description}`);
  if (context?.priority) parts.push(`Priority: ${context.priority}`);
  if (context?.status) parts.push(`Status: ${context.status}`);
  if (context?.assignee) parts.push(`Assignee: ${context.assignee}`);
  if (context?.updated) parts.push(`Updated: ${context.updated}`);
  parts.push(`Technician request: ${operatorNotes}`);

  const response = await fetch(`${AGENTIC_BASE}/rag/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: parts.join("\n") }),
  });
  return handleResponse(response);
}

export async function completeWorkorder(issueIdOrKey, transitionName = "31", resolutionComment) {
  const response = await fetch(`${API_BASE}/workorders/${issueIdOrKey}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transition_name: transitionName, resolution_comment: resolutionComment || null }),
  });
  return handleResponse(response);
}

export async function generateAgenticWorkOrder(ticketPayload) {
  const response = await fetch(`${AGENTIC_BASE}/rag/work-order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(ticketPayload),
  });
  return handleResponse(response);
}

export async function startWorkorder(issueIdOrKey, transitionName = "21") {
  const response = await fetch(`${API_BASE}/workorders/${issueIdOrKey}/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transition_name: transitionName }),
  });
  return handleResponse(response);
}

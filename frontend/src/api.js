// Prefer relative URLs so Vite dev proxy (or same-origin) handles requests.
// Override with VITE_API_BASE when deploying behind a different origin.
const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

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

export async function generateWorkorderUpdate(issueId, operatorNotes, legacyKey) {
  const response = await fetch(`${API_BASE}/rag/work-orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      issue_id: issueId,
      issue_key: legacyKey,
      operator_notes: operatorNotes,
    }),
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

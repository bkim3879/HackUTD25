import { useMemo, useState } from "react";
import { extractLocationFromDescription, extractLocationDetails } from "../formatters.js";
import { StatusPill } from "./StatusPill.jsx";

const priorityTone = {
  blocker: "danger",
  highest: "danger",
  critical: "danger",
  high: "warning",
  medium: "muted",
  low: "success",
  lowest: "success",
};

const statusTone = {
  "in progress": "muted",
  "waiting parts": "warning",
  triaged: "muted",
  done: "success",
};

export function DetailPanel({ order, loading, onStepUpdate, onAddNote, onComplete }) {
  const [noteText, setNoteText] = useState("");
  const [noteAuthor, setNoteAuthor] = useState("Technician");
  const [completeComment, setCompleteComment] = useState("");

  const missingFields = order?.missing_fields || [];

  const normalizedPriority = useMemo(() => (order?.priority || "").toLowerCase(), [order]);
  const normalizedStatus = useMemo(() => (order?.status || "").toLowerCase(), [order]);
  const location = useMemo(() => extractLocationFromDescription(order?.description || ""), [order]);
  const locationDetails = useMemo(() => extractLocationDetails(order?.description || ""), [order]);

  const handleStepToggle = (idx, currentStatus) => {
    const nextStatus = currentStatus === "done" ? "pending" : "done";
    onStepUpdate?.(idx, nextStatus);
  };

  const handleSubmitNote = (event) => {
    event.preventDefault();
    if (!noteText.trim()) return;
    onAddNote?.(noteAuthor, noteText.trim());
    setNoteText("");
  };

  if (loading) {
    return (
      <article className="panel panel--wide">
        <h3>Work Order Detail</h3>
        <p>Loading details...</p>
      </article>
    );
  }

  if (!order) {
    return (
      <article className="panel panel--wide">
        <h3>Work Order Detail</h3>
        <p>Select a work order to view steps.</p>
      </article>
    );
  }

  return (
    <article className="panel panel--wide">
      <h3>Work Order Detail</h3>
      <div className="detail-card">
        <p className="detail-label">Issue</p>
        <p className="detail-key">{order.key}</p>
        <p className="detail-summary">{order.summary}</p>
        <div className="detail-meta">
          <StatusPill label={order.priority || "Unknown"} tone={priorityTone[normalizedPriority]} />
          <StatusPill label={order.status || "Unknown"} tone={statusTone[normalizedStatus]} />
          <StatusPill label={`Score ${order.score?.toFixed(2) ?? "0.00"}`} tone="muted" />
        </div>
        {(locationDetails.rack || locationDetails.gpu || locationDetails.server || locationDetails.node || locationDetails.freeform) && (
          <div className="location-card">
            <p className="location-title">Location</p>
            <p className="location-text">
              {[locationDetails.rack && `Rack ${locationDetails.rack}`,
                locationDetails.server && `Server ${locationDetails.server}`,
                locationDetails.node && `Node ${locationDetails.node}`,
                locationDetails.gpu && `GPU ${locationDetails.gpu}`]
                .filter(Boolean)
                .join(" • ") || locationDetails.freeform || location}
            </p>
          </div>
        )}

        {missingFields.length ? (
          <div className="missing-alert">
            <p>
              Missing Jira info: <strong>{missingFields.join(", ")}</strong>. Please update the ticket before
              executing the work order.
            </p>
          </div>
        ) : null}

        <h4>Steps</h4>
        <ul className="checklist">
          {(order.steps || []).map((step, idx) => {
            const inputId = `step-${idx}`;
            return (
              <li key={`${step.description}-${idx}`} className="step">
                <input
                  id={inputId}
                  className="step-checkbox"
                  type="checkbox"
                  checked={step.status === "done"}
                  onChange={() => handleStepToggle(idx, step.status)}
                />
                <label htmlFor={inputId} className="step-label">
                  <span className="step-control" aria-hidden="true" />
                  <span className="step-text">{step.description}</span>
                </label>
              </li>
            );
          })}
        </ul>

        <h4>Technician Notes</h4>
        <div className="notes-list">
          {(order.notes || []).map((entry, idx) => (
            <div key={`${entry.timestamp}-${idx}`} className="note-entry">
              <p className="note-meta">
                <strong>{entry.author}</strong> • {new Date(entry.timestamp).toLocaleString()}
              </p>
              <p>{entry.note}</p>
            </div>
          ))}
          {!(order.notes || []).length && <p className="muted">No notes recorded yet.</p>}
        </div>

        <form className="note-form" onSubmit={handleSubmitNote}>
          <div className="note-form__row">
            <input
              type="text"
              value={noteAuthor}
              onChange={(event) => setNoteAuthor(event.target.value)}
              placeholder="Author"
            />
            <textarea
              value={noteText}
              onChange={(event) => setNoteText(event.target.value)}
              placeholder="Append technician note..."
            />
          </div>
          <button type="submit" className="button primary">
            Add Note
          </button>
        </form>

        <h4>Complete Work Order</h4>
        <div className="note-form__row">
          <input
            type="text"
            value={completeComment}
            onChange={(e) => setCompleteComment(e.target.value)}
            placeholder="Resolution comment (optional)"
          />
          <button
            type="button"
            className="button primary"
            onClick={() => onComplete?.(completeComment)}
            disabled={order.completed}
          >
            {order.completed ? "Completed" : "Complete Work Order"}
          </button>
        </div>
      </div>
    </article>
  );
}

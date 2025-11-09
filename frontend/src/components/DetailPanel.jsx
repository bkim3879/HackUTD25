import { StatusPill } from "./StatusPill.jsx";

const priorityTone = {
  Critical: "danger",
  High: "warning",
  Medium: "muted",
  Low: "success",
};

const statusTone = {
  "In Progress": "muted",
  "Waiting Parts": "warning",
  Triaged: "muted",
  Done: "success",
};

export function DetailPanel({ order, checklist }) {
  if (!order) return null;
  return (
    <article className="panel panel--stacked">
      <h3>Work Order Detail</h3>
      <div className="detail-card">
        <p className="detail-label">Selected Issue</p>
        <p className="detail-key">{order.key}</p>
        <p className="detail-summary">{order.summary}</p>
        <div className="detail-meta">
          <StatusPill label={order.priority} tone={priorityTone[order.priority]} />
          <StatusPill label={order.status} tone={statusTone[order.status]} />
        </div>
        <ul className="checklist">
          {checklist.map((step) => (
            <li key={step.text}>
              <input type="checkbox" checked={step.done} readOnly />
              <span>{step.text}</span>
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}

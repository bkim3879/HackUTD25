import { StatusPill } from "./StatusPill.jsx";

const priorityTone = {
  Highest: "danger",
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
  "To Do": "muted",
};

export function WorkOrdersPanel({ orders, selectedKey, onSelect, onRefresh, loading }) {
  return (
    <article className="panel panel--wide">
      <div className="panel__header">
        <div>
          <h3>Work Orders</h3>
          <p>{loading ? "Refreshing queue..." : "Synced with Jira"}</p>
        </div>
        <div className="panel__header-actions">
          <button className="button ghost" type="button" onClick={onRefresh} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>
      <table className="workorder-table">
        <thead>
          <tr>
            <th>Key</th>
            <th>Summary</th>
            <th>Priority</th>
            <th>Score</th>
            <th>Assignee</th>
            <th>Status</th>
            <th>Missing</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr
              key={order.key}
              className={order.key === selectedKey ? "row-selected" : undefined}
              onClick={() => onSelect(order)}
            >
              <td>{order.key}</td>
              <td>
                <div className="order-summary">
                  <p className="order-summary__title">{order.summary}</p>
                  <p className="order-summary__score">Score: {(order.score ?? 0).toFixed(2)}</p>
                </div>
              </td>
              <td>
                <StatusPill label={order.priority} tone={priorityTone[order.priority]} />
              </td>
              <td>{(order.score ?? 0).toFixed(2)}</td>
              <td>{order.assignee || "Unassigned"}</td>
              <td>
                <StatusPill label={order.status} tone={statusTone[order.status]} />
              </td>
              <td>
                {order.missing_fields?.length ? (
                  <span className="missing-pill">{order.missing_fields.join(", ")}</span>
                ) : (
                  <span className="status-pill success">Complete</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}

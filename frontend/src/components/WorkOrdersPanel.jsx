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

export function WorkOrdersPanel({ orders, selectedKey, onSelect }) {
  return (
    <article className="panel panel--wide">
      <div className="panel__header">
        <div>
          <h3>Work Orders</h3>
          <p>Synced with Jira</p>
        </div>
        <div className="panel__header-actions">
          <button className="button ghost" type="button">
            Export
          </button>
          <button className="button primary" type="button">
            + New Work Order
          </button>
        </div>
      </div>
      <table className="workorder-table">
        <thead>
          <tr>
            <th>Key</th>
            <th>Summary</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Assignee</th>
            <th>Updated</th>
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
              <td>{order.summary}</td>
              <td>
                <StatusPill label={order.priority} tone={priorityTone[order.priority]} />
              </td>
              <td>
                <StatusPill label={order.status} tone={statusTone[order.status]} />
              </td>
              <td>{order.assignee}</td>
              <td>{order.updated}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}

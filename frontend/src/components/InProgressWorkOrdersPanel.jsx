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

export function InProgressWorkOrdersPanel({ orders, selectedKey, onSelect, onOpenSelected }) {
  return (
    <article className="panel panel--stacked">
      <div className="panel__header">
        <div>
          <h3>Work Orders In Progress</h3>
          <p>Actively being worked</p>
        </div>
      </div>
      <table className="workorder-table">
        <thead>
          <tr>
            <th>Key</th>
            <th>Summary</th>
            <th>Priority</th>
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
              <td>{order.assignee || "Unassigned"}</td>
              <td>{order.updated || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
        <button className="button ghost" type="button" onClick={onOpenSelected} disabled={!selectedKey}>
          View Selected Work Order
        </button>
      </div>
    </article>
  );
}

import { StatusPill } from "./StatusPill.jsx";

const sections = [
  { label: "Dashboard", active: true },
  { label: "Active Work Orders" },
  { label: "GPU Uptime Analytics" },
  { label: "Technician Tools" },
  { label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand__mark">DW</div>
        <div>
          <p className="brand__title">Dynamic Work Order</p>
          <p className="brand__subtitle">Data Center Ops</p>
        </div>
      </div>
      <nav className="sidebar__nav">
        <p className="sidebar__section-label">Overview</p>
        {sections.slice(0, 3).map((item) => (
          <button
            key={item.label}
            className={`nav-link ${item.active ? "active" : ""}`}
            type="button"
          >
            {item.label}
          </button>
        ))}
        <p className="sidebar__section-label">Tools</p>
        {sections.slice(3).map((item) => (
          <button key={item.label} className="nav-link" type="button">
            {item.label}
          </button>
        ))}
      </nav>
      <div className="sidebar__footer">
        <div>
          <p className="sidebar__status-label">Server Health</p>
          <p className="sidebar__status-value">99.2% uptime</p>
        </div>
        <StatusPill label="Stable" tone="success" />
      </div>
    </aside>
  );
}

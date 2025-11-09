import { StatusPill } from "./StatusPill.jsx";

const sections = [
  { id: "dashboard", label: "Dashboard" },
  { id: "workorders", label: "Active Work Orders" },
  { id: "tools", label: "Technician Tools" },
  { id: "settings", label: "Settings" }
];

export function Sidebar({ active = "dashboard", onNavigate }) {
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
        {sections.slice(0, 1).map((item) => (
          <button
            key={item.id}
            className={`nav-link ${active === item.id ? "active" : ""}`}
            type="button"
            aria-pressed={active === item.id}
            onClick={() => onNavigate?.(item.id)}
          >
            {item.label}
          </button>
        ))}
        <p className="sidebar__section-label">Tools</p>
        {sections.slice(2).map((item) => (
          <button
            key={item.id}
            className={`nav-link ${active === item.id ? "active" : ""}`}
            type="button"
            aria-pressed={active === item.id}
            onClick={() => onNavigate?.(item.id)}
          >
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

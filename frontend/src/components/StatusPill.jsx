const variantClass = {
  success: "status-pill success",
  warning: "status-pill warning",
  danger: "status-pill danger",
  muted: "status-pill muted",
};

export function StatusPill({ label, tone = "muted" }) {
  return <span className={variantClass[tone] || variantClass.muted}>{label}</span>;
}

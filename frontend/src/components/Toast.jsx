export function Toast({ message, tone = "info" }) {
  if (!message) return null;
  return (
    <div className={`toast toast--${tone}`} role="status">
      {message}
    </div>
  );
}

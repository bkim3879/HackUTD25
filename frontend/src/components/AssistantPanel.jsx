export function AssistantPanel({
  messages,
  onSubmit,
  disabled,
  busy,
  contextKey,
  collapsed,
  onToggleCollapse,
}) {
  function handleSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const text = formData.get("message")?.toString().trim();
    if (!text) return;
    onSubmit(text);
    form.reset();
  }

  return (
    <aside className={`assistant-panel ${collapsed ? "assistant-panel--collapsed" : ""}`}>
      <div className="assistant-panel__header">
        <h3>Technician Assistant</h3>
        <div className="assistant-panel__controls">
          {!collapsed && <span className="status-pill muted">{busy ? "Processing..." : "AI Ready"}</span>}
          <button
            type="button"
            className="collapse-button"
            aria-label={collapsed ? "Expand assistant" : "Collapse assistant"}
            onClick={onToggleCollapse}
          >
            {collapsed ? "◀" : "▶"}
          </button>
        </div>
      </div>
      {!collapsed ? (
        <>
          <p className="assistant-context">{contextKey ? `Linked to ${contextKey}` : "Select a work order to start"}</p>
          <div className="assistant-chat">
            {messages.map((entry, index) => (
              <div key={`${entry.author}-${index}`} className={`chat-bubble ${entry.author}`}>
                {entry.text}
              </div>
            ))}
          </div>
          <form className="assistant-input" onSubmit={handleSubmit}>
            <input
              name="message"
              type="text"
              placeholder={disabled ? "Select a work order..." : "Ask for next best action..."}
              disabled={disabled || busy}
            />
            <button className="button primary" type="submit" disabled={disabled || busy}>
              Send
            </button>
          </form>
        </>
      ) : (
        <p className="assistant-panel__collapsed-label">Chat hidden</p>
      )}
    </aside>
  );
}

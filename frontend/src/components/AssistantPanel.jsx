export function AssistantPanel({ messages, onSubmit }) {
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
    <aside className="assistant-panel">
      <div className="assistant-panel__header">
        <h3>Technician Assistant</h3>
        <span className="status-pill muted">AI Ready</span>
      </div>
      <div className="assistant-chat">
        {messages.map((entry, index) => (
          <div key={`${entry.author}-${index}`} className={`chat-bubble ${entry.author}`}>
            {entry.text}
          </div>
        ))}
      </div>
      <form className="assistant-input" onSubmit={handleSubmit}>
        <input name="message" type="text" placeholder="Ask for next best action..." />
        <button className="button primary" type="submit">
          Send
        </button>
      </form>
    </aside>
  );
}

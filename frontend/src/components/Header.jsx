export function Header({ onRefresh, loading, error }) {
  return (
    <header className="main-header">
      <div>
        <h1>Ops Command Center</h1>
        <p>
          {loading ? "Syncing with Jira..." : "Synced"} • <span>{error ? `Error: ${error}` : "Live"}</span>
        </p>
      </div>
      <div className="header-actions">
        <button
          className="icon-button"
          type="button"
          aria-label="Refresh dashboard"
          onClick={onRefresh}
          disabled={loading}
        >
          &#x21bb;
        </button>
        <button className="icon-button" type="button" aria-label="Toggle filters">
          &#x1f50d;
        </button>
        <div className="profile-chip">
          <span className="profile-chip__avatar">TL</span>
          <span>Lead Tech</span>
        </div>
      </div>
    </header>
  );
}

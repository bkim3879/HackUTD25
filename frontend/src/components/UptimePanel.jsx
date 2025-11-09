const uptimeSeries = [97.8, 98.2, 99.1, 98.7, 99.6, 99.3, 99.74];

export function UptimePanel() {
  const max = 100;
  const min = 97;
  const points = uptimeSeries
    .map((value, index) => {
      const x = (index / (uptimeSeries.length - 1)) * 100;
      const y = ((max - value) / (max - min)) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <article className="panel panel--stacked">
      <h3>GPU Uptime</h3>
      <div className="chart-card">
        <svg viewBox="0 0 100 40" className="sparkline" preserveAspectRatio="none" role="img">
          <polyline points={points} />
        </svg>
      </div>
      <div className="priority-legend">
        <span className="status-pill success">&gt;= 99%</span>
        <span className="status-pill warning">97% - 99%</span>
        <span className="status-pill danger">&lt; 97%</span>
      </div>
    </article>
  );
}

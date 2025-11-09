export function MetricsGrid({ metrics }) {
  return (
    <section className="metrics-grid">
      {metrics.map((metric) => (
        <article key={metric.label} className="kpi-card">
          <h2>{metric.label}</h2>
          <p className="kpi-value">{metric.value}</p>
          <p className={`kpi-trend ${metric.direction}`}>{metric.trend}</p>
        </article>
      ))}
    </section>
  );
}

import { Button } from "./Button.jsx";

export function PageFrame({ pageId, eyebrow, title, intro, actions = [], children }) {
  return (
    <article data-page-id={pageId}>
      <header className="page-hero">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {intro && <p className="intro">{intro}</p>}
        {actions.length > 0 && (
          <div className="hero-actions">
            {actions.map((a) => (
              <Button key={a.label} variant={a.variant || "primary"} onClick={() => a.onNavigate?.(a.target)}>
                {a.label}
              </Button>
            ))}
          </div>
        )}
      </header>
      <div>{children}</div>
    </article>
  );
}

export function SectionBlock({ eyebrow, title, note, children, id }) {
  return (
    <section className="section-block" id={id}>
      <div className="section-header">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
        {note && <p className="note">{note}</p>}
      </div>
      <div>{children}</div>
    </section>
  );
}

export function FeatureGrid({ items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="features-grid">
      {items.map((item) => (
        <article className="feature-item" key={item.title}>
          <div className="feature-line" />
          {item.label && <span className="label">{item.label}</span>}
          <h3>{item.title}</h3>
          <p>{item.body}</p>
        </article>
      ))}
    </div>
  );
}

export function MetricGrid({ items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="metrics-grid">
      {items.map((item) => (
        <div className="metric-item" key={item.label}>
          <span className="metric-label">{item.label}</span>
          <strong className="metric-value">{item.value}</strong>
          <small className="metric-detail">{item.detail}</small>
        </div>
      ))}
    </div>
  );
}

export function StepGrid({ steps }) {
  if (!steps || steps.length === 0) return null;
  return (
    <div className="steps-grid">
      {steps.map((step) => (
        <article className="step-item" key={step.title}>
          <span className="step-number">{step.number}</span>
          <div className="step-body">
            <h3>{step.title}</h3>
            <p>{step.body}</p>
          </div>
        </article>
      ))}
    </div>
  );
}

export function DetailList({ items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="details-list">
      {items.map((item) => (
        <div className="detail-item" key={item.title}>
          <dt>{item.title}</dt>
          <dd>{item.body}</dd>
        </div>
      ))}
    </div>
  );
}

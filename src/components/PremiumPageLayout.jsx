function safeList(value, fallback = []) {
  return Array.isArray(value) && value.length ? value : fallback;
}

export function PageFrame({ pageId, eyebrow, title, intro, children, actions = [] }) {
  return (
    <article className="premium-page" data-page-id={pageId}>
      <header id="heroPanel" className="page-hero full-span" aria-labelledby={`${pageId}-title`}>
        <div className="hero-copy">
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h1 id={`${pageId}-title`}>{title}</h1>
          {intro ? <p className="hero-deck">{intro}</p> : null}
          {actions.length ? <ActionRow actions={actions} /> : null}
        </div>
        <div className="motion-grid hero-visual" data-motion-surface="page-hero" aria-hidden="true">
          <div className="page-transition-beam" data-motion-layer="beam"></div>
          <div className="motion-stream" data-motion-layer="stream"></div>
          <div className="motion-orbit" data-motion-layer="orbit">
            <span></span>
            <span></span>
            <span></span>
          </div>
          {["Parse", "Protect", "Compile", "Measure"].map((label) => (
            <span className="motion-node" key={label}>
              {label}
            </span>
          ))}
          <div className="motion-marquee" data-motion-layer="marquee">
            <span>token economy</span>
            <span>protected values</span>
            <span>semantic pruning</span>
            <span>trace metadata</span>
            <span>local review</span>
          </div>
          <div className="motion-stat-panel">
            <div className="motion-stat">
              <span>Mode</span>
              <strong>Policy</strong>
            </div>
            <div className="motion-stat">
              <span>Trace</span>
              <strong>Visible</strong>
            </div>
            <div className="motion-stat">
              <span>Context</span>
              <strong>Local</strong>
            </div>
          </div>
          <div className="visual-caption">
            <span>{eyebrow || "PromptCompiler"}</span>
            <strong>{title}</strong>
          </div>
        </div>
      </header>
      {children}
    </article>
  );
}

export function ActionRow({ actions = [] }) {
  return (
    <div className="hero-actions">
      {actions.map((action) => (
        <PageButton key={`${action.label}-${action.target || action.href || "action"}`} action={action} />
      ))}
    </div>
  );
}

export function PageButton({ action }) {
  const className = action.variant === "secondary" ? "ghost-link" : "primary-link";

  if (action.href) {
    return (
      <a className={className} href={action.href}>
        {action.label}
      </a>
    );
  }

  return (
    <button
      className={action.variant === "secondary" ? "secondary" : "primary"}
      type="button"
      data-page-target={action.target}
      data-page-path={action.path}
      onClick={() => action.onNavigate?.(action.target)}
    >
      {action.label}
    </button>
  );
}

export function SectionBlock({ eyebrow, title, note, children, id }) {
  return (
    <section id={id} className="panel full-span" aria-labelledby={id ? `${id}-title` : undefined}>
      <div className="panel-heading">
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h2 id={id ? `${id}-title` : undefined}>{title}</h2>
          {note ? <p className="section-note">{note}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}

export function FeatureGrid({ items, fallback }) {
  return (
    <div className="proof-grid">
      {safeList(items, fallback).map((item) => (
        <article className="proof-card" key={item.title}>
          {item.label ? <span>{item.label}</span> : null}
          <h3>{item.title}</h3>
          <p>{item.body}</p>
        </article>
      ))}
    </div>
  );
}

export function MetricGrid({ items, fallback }) {
  return (
    <div className="hero-metrics" aria-label="Page highlights">
      {safeList(items, fallback).map((item) => (
        <div key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          <small>{item.detail}</small>
        </div>
      ))}
    </div>
  );
}

export function StepGrid({ steps, fallback }) {
  return (
    <div className="stage-grid">
      {safeList(steps, fallback).map((step, index) => (
        <article className="stage-card" key={step.title}>
          <span>{step.number || String(index + 1).padStart(2, "0")}</span>
          <h3>{step.title}</h3>
          <p>{step.body}</p>
        </article>
      ))}
    </div>
  );
}

export function DetailList({ items, fallback }) {
  return (
    <dl className="details-list">
      {safeList(items, fallback).map((item) => (
        <div key={item.term || item.title}>
          <dt>{item.term || item.title}</dt>
          <dd>{item.description || item.body}</dd>
        </div>
      ))}
    </dl>
  );
}

export function CodeExample({ title, lines }) {
  return (
    <figure className="panel command-panel full-span">
      <figcaption className="compact-heading">
        <p className="eyebrow">Example</p>
        <h2>{title}</h2>
      </figcaption>
      <pre aria-label={title}>{safeList(lines, []).join("\n")}</pre>
    </figure>
  );
}

export function pageActions(onNavigate, primaryTarget = "workbench", secondaryTarget = "docs") {
  return [
    { label: "Open Workbench", target: primaryTarget, onNavigate },
    { label: "Read Docs", target: secondaryTarget, variant: "secondary", onNavigate },
  ];
}

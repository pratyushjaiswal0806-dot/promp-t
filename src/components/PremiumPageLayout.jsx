import React from "react";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { FadeIn } from "./ui/FadeIn.jsx";
import { RevealStagger } from "./ui/RevealStagger.jsx";
import { CountUp } from "./ui/CountUp.jsx";
import { MagneticButton } from "./ui/MagneticButton.jsx";

function safeList(value, fallback = []) {
  return Array.isArray(value) && value.length ? value : fallback;
}

export function PageFrame({ pageId, eyebrow, title, intro, children, actions = [] }) {
  if (pageId === "home") {
    return (
      <article className="premium-page" data-page-id={pageId} style={{ position: "relative" }}>
        {/* Giant Outlined Backdrop Heading */}
        <div className="giant-text-backdrop">
          <h1 className="compile-outline">COMPILE</h1>
          <h1 className="context-solid">CONTEXT</h1>
        </div>

        <header id="heroPanel" className="home-hero-split full-span" aria-labelledby={`${pageId}-title`}>
          {/* Operator Notes Card (Rotated 3deg, zine-cut) */}
          <FadeIn direction="right" delay={100} className="operator-notes-terminal zine-cut zine-rotate-3">
            <h2 className="label-tag">Operator Notes</h2>
            <div className="notes-section">
              <h3>Docs</h3>
              <p>Installation, quick-start, CLI reference...</p>
              <div className="notes-links">
                <button type="button" onClick={() => window.location.hash = "#/workbench"}>Open Workbench</button>
                <span style={{ color: "var(--line)" }}>///</span>
                <button type="button" onClick={() => window.location.hash = "#/docs"}>Read Docs</button>
              </div>
            </div>
            <div className="notes-section accented">
              <h3>Installation</h3>
              <p>Clone the repo and install dependencies to begin compilation.</p>
            </div>
          </FadeIn>

          {/* Terminal/SDK Ref Card (Rotated -2deg) */}
          <FadeIn direction="left" delay={200} className="terminal-sdk-ref zine-rotate-neg-2">
            <h2>Terminal/SDK Ref</h2>
            <div className="terminal-code-block font-mono">
              <div>
                <span className="prompt-char">❯</span>
                <span>git clone https://localhost.com/compile</span>
              </div>
              <div>
                <span className="prompt-char">❯</span>
                <span>npm install</span>
              </div>
              <div>
                <span className="prompt-char">❯</span>
                <span>npm run build</span>
              </div>
            </div>
            
            <button
              type="button"
              className="button-clean-primary zine-cut"
              style={{ width: "100%", marginTop: "2rem", justifyContent: "center" }}
              onClick={() => window.location.hash = "#/workbench"}
            >
              Get Started →
            </button>
          </FadeIn>
        </header>
        
        <div className="page-content-clean">
          {children}
        </div>
      </article>
    );
  }

  return (
    <article className="premium-page" data-page-id={pageId}>
      <header id="heroPanel" className="page-hero-clean full-span" aria-labelledby={`${pageId}-title`}>
        <div className="hero-copy-clean">
          {eyebrow ? (
            <FadeIn direction="down" delay={100}>
              <p className="eyebrow eyebrow-premium-clean">{eyebrow}</p>
            </FadeIn>
          ) : null}
          
          <FadeIn direction="up" delay={200}>
            <h1 id={`${pageId}-title`} className="premium-title-clean">{title}</h1>
          </FadeIn>

          {intro ? (
            <FadeIn direction="up" delay={300}>
              <p className="hero-deck-clean">{intro}</p>
            </FadeIn>
          ) : null}

          {actions.length ? (
            <FadeIn direction="up" delay={400}>
              <ActionRow actions={actions} />
            </FadeIn>
          ) : null}
        </div>
      </header>
      
      <div className="page-content-clean">
        {children}
      </div>
    </article>
  );
}

export function ActionRow({ actions = [] }) {
  return (
    <div className="hero-actions-clean">
      {actions.map((action) => (
        <PageButton key={`${action.label}-${action.target || action.href || "action"}`} action={action} />
      ))}
    </div>
  );
}

export function PageButton({ action }) {
  const isSecondary = action.variant === "secondary";
  const className = isSecondary ? "button-clean-secondary" : "button-clean-primary";

  if (action.href) {
    return (
      <MagneticButton strength={10} className={className} onClick={() => window.open(action.href, '_blank')}>
        <span className="button-text-container">
          {action.label}
          {!isSecondary && <ArrowRight size={14} className="button-arrow" />}
        </span>
      </MagneticButton>
    );
  }

  return (
    <MagneticButton
      strength={10}
      className={className}
      type="button"
      data-page-target={action.target}
      data-page-path={action.path}
      onClick={() => action.onNavigate?.(action.target)}
    >
      <span className="button-text-container">
        {action.label}
        {!isSecondary && <ArrowRight size={14} className="button-arrow" />}
      </span>
    </MagneticButton>
  );
}

export function SectionBlock({ eyebrow, title, note, children, id }) {
  return (
    <FadeIn direction="up" delay={100} className="section-block-clean full-span" id={id}>
      <div className="section-header-clean">
        {eyebrow ? <p className="eyebrow eyebrow-premium-clean">{eyebrow}</p> : null}
        <h2 id={id ? `${id}-title` : undefined} className="section-title-clean">{title}</h2>
        {note ? <p className="section-note-clean">{note}</p> : null}
      </div>
      <div className="section-body-clean">
        {children}
      </div>
    </FadeIn>
  );
}

export function FeatureGrid({ items, fallback }) {
  return (
    <RevealStagger className="features-grid-clean" stagger={0.08}>
      {safeList(items, fallback).map((item, index) => {
        let cardStyle = {};
        let cardClass = "feature-item-clean ";
        let labelStyle = {};
        let titleStyle = {};
        let pStyle = {};

        if (index === 0) {
          cardClass += "zine-cut zine-rotate-1";
          cardStyle = { border: "4px solid var(--text)", boxShadow: "15px 15px 0 var(--shadow-soft)" };
          labelStyle = { background: "var(--accent-lime)", color: "var(--text-on-accent)", display: "inline-block", padding: "0.25rem 0.75rem", boxShadow: "5px 5px 0 var(--text)" };
        } else if (index === 1) {
          cardClass += "zine-cut-alt zine-rotate-neg-2";
          cardStyle = { border: "4px solid var(--accent-lime)", boxShadow: "15px 15px 0 var(--shadow-soft)" };
          labelStyle = { background: "var(--text)", color: "var(--bg)", display: "inline-block", padding: "0.25rem 0.75rem", float: "right", boxShadow: "-5px 5px 0 var(--accent-lime)" };
        } else if (index === 2) {
          cardClass += "zine-cut zine-rotate-2";
          cardStyle = { border: "4px solid var(--text)", background: "var(--surface)", boxShadow: "15px 15px 0 var(--shadow-soft)" };
          labelStyle = { background: "var(--accent-lime)", color: "var(--text-on-accent)", display: "inline-block", padding: "0.25rem 0.75rem", boxShadow: "5px 5px 0 var(--text)" };
          titleStyle = { color: "var(--accent-lime-text)" };
        } else if (index === 3) {
          cardClass += "zine-cut-alt zine-rotate-neg-1";
          cardStyle = { border: "4px solid var(--accent-lime)", background: "var(--surface)", color: "var(--text)", boxShadow: "15px 15px 0 var(--shadow-soft)" };
          labelStyle = { background: "var(--text)", color: "var(--bg)", display: "inline-block", padding: "0.25rem 0.75rem", boxShadow: "5px 5px 0 var(--accent-lime)" };
          titleStyle = { color: "var(--accent-lime-text)" };
          pStyle = { color: "var(--text)", borderLeftColor: "var(--accent-lime-text)", fontWeight: "bold" };
        }

        return (
          <article className={cardClass} style={cardStyle} key={item.title}>
            <div style={{ display: "flow-root", marginBottom: "1.5rem" }}>
              {item.label ? (
                <span className="feature-label-clean" style={labelStyle}>
                  {item.label}
                </span>
              ) : null}
            </div>
            <h3 style={titleStyle}>{item.title}</h3>
            <p style={pStyle} className="font-mono">{item.body}</p>
          </article>
        );
      })}
    </RevealStagger>
  );
}

export function MetricGrid({ items, fallback }) {
  return (
    <RevealStagger className="metrics-grid-clean" stagger={0.06}>
      {safeList(items, fallback).map((item, index) => {
        const cleanValStr = String(item.value || "");
        const endNum = parseFloat(cleanValStr) || 0;
        const suffix = cleanValStr.replace(/[0-9.]/g, "");
        const decimals = cleanValStr.includes(".") ? cleanValStr.split(".")[1].length : 0;

        // Custom index-based styling classes for brutalist zine stats card collage
        let cardStyle = {};
        let cardClass = "metric-item-clean ";
        let textStyle = {};

        if (index === 0) {
          cardClass += "zine-rotate-1";
        } else if (index === 1) {
          cardClass += "zine-rotate-neg-2";
          cardStyle = { background: "var(--surface)", color: "var(--text)", borderColor: "var(--line)" };
        } else if (index === 2) {
          cardClass += "zine-rotate-3";
          cardStyle = { background: "var(--surface)", borderTop: "8px solid var(--accent-lime)" };
          textStyle = { WebkitTextStroke: "2px var(--text)", color: "transparent" };
        } else if (index === 3) {
          cardClass += "zine-rotate-neg-1";
          cardStyle = { background: "var(--accent-lime)", color: "var(--text-on-accent)", boxShadow: "10px 10px 0 var(--shadow-soft)" };
        }

        return (
          <div key={item.label} className={cardClass} style={cardStyle}>
            <span className="metric-label-clean" style={{ color: index === 3 ? "var(--text-on-accent)" : "var(--text)" }}>
              {item.label}
            </span>
            <strong className="metric-value-clean" style={Object.keys(textStyle).length ? textStyle : { color: index === 3 ? "var(--text-on-accent)" : "var(--accent-lime-text)" }}>
              <CountUp end={endNum} suffix={suffix} decimals={decimals} duration={1.2} />
            </strong>
            <small className="metric-detail-clean">{item.detail}</small>
          </div>
        );
      })}
    </RevealStagger>
  );
}

export function StepGrid({ steps, fallback }) {
  return (
    <RevealStagger className="steps-list-clean" stagger={0.08}>
      {safeList(steps, fallback).map((step, index) => {
        let cardStyle = {};
        let cardClass = "step-item-clean ";
        let badgeStyle = {};
        let headingStyle = {};
        let textStyle = {};

        if (index === 0) {
          cardClass += "zine-cut zine-rotate-1";
          cardStyle = { border: "4px solid var(--accent-lime)", boxShadow: "15px 15px 0 var(--shadow-soft)" };
          badgeStyle = { background: "rgba(199,248,90,0.15)", color: "var(--accent-lime-text)" };
          headingStyle = { borderLeft: "4px solid var(--accent-lime-text)", paddingLeft: "0.5rem" };
        } else if (index === 1) {
          cardClass += "zine-cut-alt zine-rotate-neg-1";
          cardStyle = { border: "4px solid var(--text)", background: "var(--surface)", boxShadow: "-15px 15px 0 var(--shadow-soft)" };
          badgeStyle = { background: "var(--accent-lime)", color: "var(--text-on-accent)", boxShadow: "5px 5px 0 var(--text)" };
          headingStyle = { borderLeft: "4px solid var(--accent-lime-text)", paddingLeft: "0.5rem", color: "var(--accent-lime-text)" };
        } else if (index === 2) {
          cardClass += "zine-cut zine-rotate-2";
          cardStyle = { border: "4px solid var(--accent-lime)", boxShadow: "15px 15px 0 var(--shadow-soft)" };
          badgeStyle = { background: "rgba(199,248,90,0.15)", color: "var(--accent-lime-text)" };
          headingStyle = { borderLeft: "4px solid var(--accent-lime-text)", paddingLeft: "0.5rem" };
        } else if (index === 3) {
          cardClass += "zine-cut-alt zine-rotate-neg-2";
          cardStyle = { border: "4px solid var(--text)", background: "var(--accent-lime)", color: "var(--text-on-accent)", boxShadow: "15px 15px 0 var(--shadow-soft)" };
          badgeStyle = { background: "var(--bg)", color: "var(--text)", boxShadow: "5px 5px 0 var(--text)" };
          headingStyle = { borderLeft: "8px solid var(--text-on-accent)", paddingLeft: "0.5rem", color: "var(--text-on-accent)" };
          textStyle = { color: "var(--text-on-accent)" };
        }

        return (
          <article className={cardClass} style={cardStyle} key={step.title}>
            <div className="step-number-container-clean">
              <span className="step-number-clean" style={badgeStyle}>
                {step.number || String(index + 1).padStart(2, "0")}
              </span>
            </div>
            <div className="step-body-clean">
              <h3 style={headingStyle}>{step.title}</h3>
              <p style={textStyle}>{step.body}</p>
            </div>
          </article>
        );
      })}
    </RevealStagger>
  );
}

export function DetailList({ items, fallback }) {
  return (
    <RevealStagger className="details-list-clean" stagger={0.05}>
      {safeList(items, fallback).map((item) => (
        <div key={item.term || item.title} className="detail-item-clean">
          <dt>{item.term || item.title}</dt>
          <dd>{item.description || item.body}</dd>
        </div>
      ))}
    </RevealStagger>
  );
}

export function CodeExample({ title, lines }) {
  return (
    <FadeIn direction="up" delay={100} className="code-example-clean full-span">
      <figcaption className="code-example-heading-clean">
        <p className="eyebrow eyebrow-premium-clean">Terminal / SDK reference</p>
        <h2>{title}</h2>
      </figcaption>
      <pre aria-label={title} className="code-pre-clean">
        {safeList(lines, []).map((line, index) => (
          <div key={index} className="code-line-clean">
            <span className="code-line-number-clean">{index + 1}</span>
            <span className="code-line-content-clean">{line}</span>
          </div>
        ))}
      </pre>
    </FadeIn>
  );
}

export function pageActions(onNavigate, primaryTarget = "workbench", secondaryTarget = "docs") {
  return [
    { label: "Open Workbench", target: primaryTarget, onNavigate },
    { label: "Read Docs", target: secondaryTarget, variant: "secondary", onNavigate },
  ];
}

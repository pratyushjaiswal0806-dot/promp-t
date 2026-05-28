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
      <article className="premium-page" data-page-id={pageId}>
        <div className="ambient-glow-wrapper">
           <div className="glow-spot-lime"></div>
           <div className="glow-spot-blue"></div>
        </div>
        <header id="heroPanel" className="home-hero-split full-span" aria-labelledby={`${pageId}-title`}>
          <FadeIn direction="right" delay={100} className="operator-notes-terminal">
            <h4>Operator Notes</h4>
            <p>Docs<br/>Installation, quick-start, CLI reference...<br/><span className="highlight" style={{cursor:'pointer'}} onClick={() => window.location.href='/docs'}>Open Workbench &gt; Read Docs</span></p>
            <p>INSTALLATION<br/>Clone the repo and install dependencies...</p>
            <p>TERMINAL/SDK REFERENCE<br/><span className="highlight">Installation</span><br/>$ git clone https://localhost.com/compile<br/>$ npm install<br/>$ npm run build</p>
          </FadeIn>
          <div className="hero-copy-clean" style={{display:'flex', flexDirection:'column', justifyContent:'center'}}>
            <FadeIn direction="left" delay={200}>
              <h1 id={`${pageId}-title`} className="premium-title-clean">COMPILE<br/>CONTEXT</h1>
            </FadeIn>
          </div>
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
      {safeList(items, fallback).map((item) => (
        <article className="feature-item-clean" key={item.title}>
          <div className="feature-line-separator"></div>
          {item.label ? <span className="feature-label-clean">{item.label}</span> : null}
          <h3>{item.title}</h3>
          <p>{item.body}</p>
        </article>
      ))}
    </RevealStagger>
  );
}

export function MetricGrid({ items, fallback }) {
  return (
    <RevealStagger className="metrics-grid-clean" stagger={0.06}>
      {safeList(items, fallback).map((item) => {
        const cleanValStr = String(item.value || "");
        const endNum = parseFloat(cleanValStr) || 0;
        const suffix = cleanValStr.replace(/[0-9.]/g, "");
        const decimals = cleanValStr.includes(".") ? cleanValStr.split(".")[1].length : 0;

        return (
          <div key={item.label} className="metric-item-clean">
            <span className="metric-label-clean">{item.label}</span>
            <strong className="metric-value-clean">
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
      {safeList(steps, fallback).map((step, index) => (
        <article className="step-item-clean" key={step.title}>
          <div className="step-number-container-clean">
            <span className="step-number-clean">{step.number || String(index + 1).padStart(2, "0")}</span>
          </div>
          <div className="step-body-clean">
            <h3>{step.title}</h3>
            <p>{step.body}</p>
          </div>
        </article>
      ))}
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

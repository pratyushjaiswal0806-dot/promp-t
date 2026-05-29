import { PageFrame, SectionBlock, FeatureGrid, MetricGrid, StepGrid, pageActions } from "../components/PremiumPageLayout.jsx";
import { IconTile } from "../components/IconTile.jsx";
import { Particles } from "../components/Particles.jsx";
import { FadeIn } from "../components/ui/FadeIn.jsx";
import { home } from "../content/home.js";

export default function HomePage({ onNavigate }) {
  const h = home.hero;
  return (
    <PageFrame pageId="home" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={pageActions(onNavigate)}
    >
      <SectionBlock eyebrow="Live Stats" title="Pipeline at a glance">
        <MetricGrid items={home.metrics} />
      </SectionBlock>
      <SectionBlock eyebrow="What it does" title="Parse, protect, compile, measure">
        <FeatureGrid items={home.features} />
      </SectionBlock>
      <SectionBlock title="Use Cases">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "3rem", padding: "2rem 0" }}>
          {home.useCaseLinks.map((uc, index) => {
            const styleClass = `card-premium zine-style-${(index % 3) + 1}`;
            return (
              <div key={uc.title} className={styleClass}>
                <div className="card-premium-img-wrap">
                  <div className="card-premium-img-overlay"></div>
                  <img src={uc.image} alt={uc.title} className="card-premium-img" />
                </div>
                <h3 className="card-premium-title">{uc.title}</h3>
                <p className="card-premium-body">{uc.body}</p>
                <button type="button" className="card-premium-button" onClick={() => onNavigate(uc.target)}>Learn More →</button>
              </div>
            );
          })}
        </div>
      </SectionBlock>
      <SectionBlock eyebrow="How it works" title="From raw context to optimized prompt">
        <StepGrid steps={home.stages} />
      </SectionBlock>
    </PageFrame>
  );
}

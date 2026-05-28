import { PageFrame, SectionBlock, pageActions } from "../components/PremiumPageLayout.jsx";
import { SidebarNav } from "../components/SidebarNav.jsx";
import { EndpointCard } from "../components/EndpointCard.jsx";
import { apiReference } from "../content/apiReference.js";

const sections = apiReference.endpoints.map((e) => ({ id: e.path.replace(/[\/{}]/g, ""), title: e.path }));

export default function ApiReferencePage({ onNavigate }) {
  const h = apiReference.hero;
  return (
    <PageFrame pageId="api-reference" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={[
        { label: "Interactive API Docs", href: "/docs", onNavigate },
        { label: "Observability", target: "observability", variant: "secondary", onNavigate },
      ]}
    >
      <div className="sidebar-layout">
        <SidebarNav sections={sections} onNavigate={(id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })} />
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {apiReference.endpoints.map((ep) => (
            <div key={ep.path} id={ep.path.replace(/[\/{}]/g, "")}>
              <EndpointCard
                method={ep.method}
                path={ep.path}
                description={ep.description}
                requestSchema={ep.requestSchema}
                responseSchema={ep.responseSchema}
                example={ep.example}
                statusCodes={ep.statusCodes}
              />
            </div>
          ))}
        </div>
      </div>
    </PageFrame>
  );
}

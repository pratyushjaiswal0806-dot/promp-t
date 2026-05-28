import { PageFrame, SectionBlock, pageActions } from "../components/PremiumPageLayout.jsx";
import { SidebarNav } from "../components/SidebarNav.jsx";
import { CodeSnippet } from "../components/CodeSnippet.jsx";
import { CodeExample } from "../components/PremiumPageLayout.jsx";
import { docs } from "../content/docs.js";

const sections = docs.sections.map((s) => ({ id: s.title.toLowerCase().replace(/\s+/g, "-"), title: s.title }));

export default function DocsPage({ onNavigate }) {
  const h = docs.hero;
  return (
    <PageFrame pageId="docs" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={pageActions(onNavigate, "workbench", "how-it-works")}
    >
      <div className="sidebar-layout">
        <SidebarNav sections={sections} onNavigate={(id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })} />
        <div>
          {docs.sections.map((section) => {
            const id = section.title.toLowerCase().replace(/\s+/g, "-");
            return (
              <SectionBlock key={section.title} eyebrow={section.title} title="" note={section.body} id={id}>
                {section.commands?.length > 0 && <CodeExample title={section.title} lines={section.commands} />}
              </SectionBlock>
            );
          })}
        </div>
      </div>
    </PageFrame>
  );
}

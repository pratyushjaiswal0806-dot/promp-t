import { useEffect, useState } from "react";

export function SidebarNav({ sections, activeId, onNavigate }) {
  const [localActive, setLocalActive] = useState(activeId || sections?.[0]?.id);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPos = window.scrollY + 120;
      for (let i = sections.length - 1; i >= 0; i--) {
        const el = document.getElementById(sections[i].id);
        if (el && el.offsetTop <= scrollPos) {
          setLocalActive(sections[i].id);
          return;
        }
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [sections]);

  const active = activeId || localActive;

  return (
    <nav className="sidebar-nav" aria-label="Section navigation">
      {sections.map((s) => (
        <a
          key={s.id}
          href={`#${s.id}`}
          className={active === s.id ? "active" : ""}
          onClick={(e) => { e.preventDefault(); onNavigate?.(s.id); document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth" }); }}
        >
          {s.title || s.label}
        </a>
      ))}
    </nav>
  );
}

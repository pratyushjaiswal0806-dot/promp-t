import { useEffect, useState, useCallback } from "react";
import { navItems } from "../content/navigation.js";

export function useRouter() {
  const [page, setPage] = useState(() => {
    const p = window.location.pathname.replace(/\/+$/, "") || "/";
    for (const item of navItems) {
      if (item.href === p) return item.id;
    }
    return "home";
  });

  useEffect(() => {
    const onPop = () => {
      const p = window.location.pathname.replace(/\/+$/, "") || "/";
      for (const item of navItems) {
        if (item.href === p) { setPage(item.id); return; }
      }
      setPage("home");
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((pageId) => {
    const item = navItems.find((n) => n.id === pageId);
    if (!item) return;
    setPage(pageId);
    window.history.pushState(null, "", item.href);
    window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  }, []);

  return { page, navigate };
}

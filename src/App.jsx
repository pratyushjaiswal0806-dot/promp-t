import { useRouter } from "./router/useRouter.js";
import { Topbar } from "./components/Topbar.jsx";
import { Footer } from "./components/Footer.jsx";
import { ErrorBoundary } from "./components/ErrorBoundary.jsx";
import { ToastContainer } from "./components/Toast.jsx";
import { WorkbenchProvider } from "./workbench/context/CompilerContext.jsx";
import { WorkbenchShell } from "./workbench/WorkbenchShell.jsx";
import HomePage from "./pages/HomePage.jsx";
import HowItWorksPage from "./pages/HowItWorksPage.jsx";
import PlatformPage from "./pages/PlatformPage.jsx";
import SecurityPage from "./pages/SecurityPage.jsx";
import UseCasesPage from "./pages/UseCasesPage.jsx";
import ApiReferencePage from "./pages/ApiReferencePage.jsx";
import ObservabilityPage from "./pages/ObservabilityPage.jsx";
import DocsPage from "./pages/DocsPage.jsx";

export default function App() {
  const { page, navigate } = useRouter();

  const status = { text: "Ready", className: "ready" };

  return (
    <div className="premium-shell">
      <Topbar activePage={page} onNavigate={navigate} status={status} />
      <main className="workspace-shell">
        <ErrorBoundary>
          {page === "home" && <HomePage onNavigate={navigate} />}
          {page === "how-it-works" && <HowItWorksPage onNavigate={navigate} />}
          {page === "platform" && <PlatformPage onNavigate={navigate} />}
          {page === "security" && <SecurityPage onNavigate={navigate} />}
          {page === "use-cases" && <UseCasesPage onNavigate={navigate} />}
          {page === "api-reference" && <ApiReferencePage onNavigate={navigate} />}
          {page === "observability" && <ObservabilityPage onNavigate={navigate} />}
          {page === "docs" && <DocsPage onNavigate={navigate} />}
          {page === "workbench" && (
            <WorkbenchProvider>
              <WorkbenchShell />
            </WorkbenchProvider>
          )}
        </ErrorBoundary>
      </main>
      <Footer onNavigate={navigate} />
      <ToastContainer />
    </div>
  );
}

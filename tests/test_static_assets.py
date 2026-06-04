import json
import unittest
from pathlib import Path

from promptcompiler.fastapi_server import ROOT, WEB_ROOT, _content_type, _static_file_for_request

APP_SOURCE = ROOT / "src" / "App.jsx"
STYLE_SOURCE = ROOT / "src" / "styles.css"
TOKENS_SOURCE = ROOT / "src" / "styles" / "tokens.css"
LAYOUT_SOURCE = ROOT / "src" / "styles" / "layout.css"
PAGES_ROOT = ROOT / "src" / "pages"
PACKAGE_JSON = ROOT / "package.json"
VITE_CONFIG = ROOT / "vite.config.js"


class StaticAssetTests(unittest.TestCase):
    def test_favicon_ico_maps_to_svg_asset(self):
        path = _static_file_for_request("/favicon.ico")
        self.assertEqual(path, WEB_ROOT / "favicon.svg")
        self.assertEqual(_content_type(path), "image/svg+xml")

    def test_workbench_defaults_to_balanced_compile_mode(self):
        policy = (ROOT / "src" / "workbench" / "PolicyControls.jsx").read_text()
        self.assertIn('value="balanced"', policy)
        self.assertIn('value="context_file"', policy)
        self.assertIn('id="reuseExpectedCallsInput"', policy)
        self.assertIn('className="advanced-control-group"', policy)
        self.assertIn('id="contextAdvancedControls"', policy)
        self.assertIn('id="toolsAdvancedControls"', policy)

    def test_workbench_drawer_hides_secondary_tabs_behind_more_selector(self):
        drawer_source = (ROOT / "src" / "components" / "Drawer.jsx").read_text()
        shell_source = (ROOT / "src" / "workbench" / "WorkbenchShell.jsx").read_text()

        self.assertIn("primary", shell_source)
        self.assertIn("drawerMoreSelect", drawer_source)
        self.assertIn("secondaryTabs", drawer_source)

    def test_workbench_exposes_prompt_optimization_workflow_selectors(self):
        source = "\n".join(
            [
                (ROOT / "src" / "workbench" / "WorkbenchShell.jsx").read_text(),
                (ROOT / "src" / "workbench" / "InputPanel.jsx").read_text(),
                (ROOT / "src" / "workbench" / "OutputPanel.jsx").read_text(),
                (ROOT / "src" / "workbench" / "PolicyControls.jsx").read_text(),
                (ROOT / "src" / "workbench" / "AnalyticsPanel.jsx").read_text(),
                (ROOT / "src" / "workbench" / "HistoryPanel.jsx").read_text(),
            ]
        )
        for selector_id in (
            "promptInput",
            "compileButton",
            "analyzeButton",
            "lintButton",
            "nimButton",
            "modelSelect",
            "sampleSelect",
            "workflowPresetSelect",
            "targetBudgetInput",
            "dryRunInput",
            "zeroRetentionInput",
            "cacheEnabled",
            "outputFormat",
            "maxWordsInput",
            "explainToggle",
            "systemPromptRef",
            "reuseExpectedCallsInput",
            "includeDecodePromptInput",
            "validationModeSelect",
            "retrievalTopKInput",
            "toolCompactInput",
            "autoSemanticInput",
            "deterministicSemanticInput",
            "optimizedOutput",
            "optimizationReport",
            "metrics",
            "segmentsTable",
            "diffList",
            "semanticScores",
            "ragPruningTable",
            "historyList",
            "traceLookupInput",
        ):
            self.assertIn(f'id="{selector_id}"', source)

    def test_semantic_controls_are_visible_in_core_setup(self):
        policy = (ROOT / "src" / "workbench" / "PolicyControls.jsx").read_text()
        css = (ROOT / "src" / "styles" / "workbench.css").read_text()

        self.assertIn('className="semantic-quick-controls"', policy)
        self.assertIn('id="autoSemanticInput"', policy)
        self.assertIn('id="deterministicSemanticInput"', policy)
        self.assertIn(".semantic-quick-controls", css)

    def test_optimized_output_has_own_scroll_region(self):
        css = (ROOT / "src" / "styles" / "workbench.css").read_text()
        output_source = (ROOT / "src" / "workbench" / "OutputPanel.jsx").read_text()

        self.assertIn(".optimized-output-scroll", css)
        self.assertIn("overflow: auto", css)
        self.assertIn("overscroll-behavior: contain", css)
        self.assertIn('id="optimizedOutput"', output_source)
        self.assertIn('className="optimized-output-scroll"', output_source)

    def test_workbench_exposes_trust_clarity_selectors(self):
        source = "\n".join(
            [
                (ROOT / "src" / "workbench" / "OutputPanel.jsx").read_text(),
                (ROOT / "src" / "workbench" / "AnalyticsPanel.jsx").read_text(),
            ]
        )
        css = (ROOT / "src" / "styles" / "workbench.css").read_text()

        for selector_id in (
            "trustBadge",
            "promptRecommendation",
            "tokenAccountingPanel",
            "trustExplanationRows",
            "trustMetrics",
        ):
            self.assertIn(f'id="{selector_id}"', source)
        for class_name in (
            ".trust-badge",
            ".token-accounting-panel",
            ".prompt-recommendation-card",
            ".trust-explanation-rows",
        ):
            self.assertIn(class_name, css)

    def test_python_server_defaults_to_documented_port_8765(self):
        server_source = (ROOT / "promptcompiler" / "fastapi_server.py").read_text()
        cli_source = (ROOT / "promptcompiler" / "cli.py").read_text()
        readme = (ROOT / "README.md").read_text()
        self.assertIn("def run(host: str = \"127.0.0.1\", port: int = 8765)", server_source)
        self.assertIn("default=8765", cli_source)
        self.assertNotIn("127.0.0.1:8766", readme)

    def test_react_vite_project_config_builds_into_web_root(self):
        package = json.loads(PACKAGE_JSON.read_text())
        vite_config = VITE_CONFIG.read_text()
        index_html = (ROOT / "index.html").read_text()
        self.assertEqual(package["scripts"]["build"], "vite build")
        self.assertEqual(package["scripts"]["dev"], "vite --host 127.0.0.1")
        for dependency in ("@vitejs/plugin-react", "vite", "react", "react-dom"):
            self.assertIn(dependency, package["dependencies"])
        self.assertIn('outDir: "web"', vite_config)
        self.assertIn('<div id="root"></div>', index_html)
        self.assertIn('/src/main.jsx', index_html)

    def test_premium_frontend_explains_compile_pipeline(self):
        pages_source = (
            (ROOT / "src" / "pages" / "HomePage.jsx").read_text()
            + (ROOT / "src" / "content" / "home.js").read_text()
            + (ROOT / "src" / "workbench" / "AnalyticsPanel.jsx").read_text()
            + (ROOT / "src" / "workbench" / "Inspector.jsx").read_text()
        )
        for phrase in (
            "WorkbenchShell",
            "ErrorBoundary",
            "workbench",
            "home",
            "how-it-works",
        ):
            self.assertIn(phrase, APP_SOURCE.read_text())
        for phrase in (
            "Parse",
            "Protect",
            "Compile",
            "Measure",
            "Local-first",
            "Open Workbench",
        ):
            self.assertIn(phrase, pages_source)

    def test_multipage_premium_frontend_contract(self):
        source = APP_SOURCE.read_text()
        topbar_source = (ROOT / "src" / "components" / "Topbar.jsx").read_text()
        input_source = (ROOT / "src" / "workbench" / "InputPanel.jsx").read_text()

        expected_pages = (
            "HomePage",
            "HowItWorksPage",
            "PlatformPage",
            "SecurityPage",
            "UseCasesPage",
            "DocsPage",
            "ApiReferencePage",
            "ObservabilityPage",
        )
        for page_name in expected_pages:
            self.assertTrue((PAGES_ROOT / f"{page_name}.jsx").exists(), f"missing page: {page_name}")
            self.assertIn(page_name, source)

        for phrase in (
            "navigate",
            "ErrorBoundary",
            "ToastContainer",
            "WorkbenchProvider",
            "WorkbenchShell",
            "premium-shell",
        ):
            self.assertIn(phrase, source)

        self.assertIn("aria-current", topbar_source)
        self.assertTrue("fileInputRef" in input_source or "fileRef" in input_source)

    def test_styles_define_premium_visual_system(self):
        css = (
            (ROOT / "src" / "styles" / "tokens.css").read_text()
            + "\n"
            + (ROOT / "src" / "styles" / "layout.css").read_text()
        )
        for token in (
            "--surface-glass",
            "--accent-lime",
            "--accent-coral",
            "--accent-blue",
            ".page-hero",
            ".topbar",
            ".split-editor",
            ".controls-grid",
            ".features-grid",
            ".steps-grid",
            ".metrics-grid",
            ".premium-shell",
        ):
            self.assertIn(token, css)


if __name__ == "__main__":
    unittest.main()

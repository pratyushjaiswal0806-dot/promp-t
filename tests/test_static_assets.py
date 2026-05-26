import json
import unittest
from html.parser import HTMLParser

from promptcompiler.server import ROOT, WEB_ROOT, _content_type, _static_file_for_request


APP_SOURCE = ROOT / "src" / "App.jsx"
STYLE_SOURCE = ROOT / "src" / "styles.css"
SITE_CONTENT_SOURCE = ROOT / "src" / "data" / "siteContent.js"
PAGES_ROOT = ROOT / "src" / "pages"
PACKAGE_JSON = ROOT / "package.json"
VITE_CONFIG = ROOT / "vite.config.js"


class CompressionModeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_mode_select = False
        self.selected_mode = None
        self.ids = set()
        self.classes = set()
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        for class_name in values.get("class", "").split():
            self.classes.add(class_name)
        if tag == "select" and values.get("id") == "modeSelect":
            self.in_mode_select = True
            return
        if tag == "option" and self.in_mode_select and "selected" in values:
            self.selected_mode = values.get("value")

    def handle_endtag(self, tag):
        if tag == "select" and self.in_mode_select:
            self.in_mode_select = False

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)


class StaticAssetTests(unittest.TestCase):
    def test_favicon_ico_maps_to_svg_asset(self):
        path = _static_file_for_request("/favicon.ico")

        self.assertEqual(path, WEB_ROOT / "favicon.svg")
        self.assertEqual(_content_type(path), "image/svg+xml")

    def test_workbench_defaults_to_balanced_compile_mode(self):
        source = APP_SOURCE.read_text()

        self.assertIn('id="modeSelect"', source)
        self.assertIn('defaultValue="balanced"', source)

    def test_react_vite_project_config_builds_into_web_root(self):
        package = json.loads(PACKAGE_JSON.read_text())
        vite_config = VITE_CONFIG.read_text()
        index_html = (ROOT / "index.html").read_text()

        self.assertEqual(package["scripts"]["build"], "vite build")
        self.assertEqual(package["scripts"]["dev"], "vite --host 127.0.0.1")
        for dependency in ("@vitejs/plugin-react", "vite", "react", "react-dom"):
            self.assertIn(dependency, package["dependencies"])
        self.assertIn("outDir: \"web\"", vite_config)
        self.assertIn("<div id=\"root\"></div>", index_html)
        self.assertIn('/src/main.jsx', index_html)

    def test_premium_frontend_explains_compile_pipeline(self):
        source = APP_SOURCE.read_text()

        for selector in (
                "heroPanel",
                "signalCanvas",
                "pipelinePanel",
                "proofPanel",
                "controlPanel",
                "inputPanel",
                "outputPanel",
                "analyticsPanel",
                "workflowRail",
        ):
            self.assertIn(selector, source)
        for class_name in ("stage-card", "proof-card", "premium-shell"):
            self.assertIn(class_name, source)
        for phrase in (
            "Parse",
            "Protect",
            "Compile",
            "Measure",
            "What happens inside",
            "Local-first",
        ):
            self.assertIn(phrase, source)

    def test_multipage_premium_frontend_contract(self):
        source = APP_SOURCE.read_text()
        content = SITE_CONTENT_SOURCE.read_text()

        expected_pages = (
            "HomePage",
            "WorkbenchPage",
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

        for page_id in (
                "home",
                "workbench",
                "how-it-works",
                "platform",
                "security",
                "use-cases",
                "docs",
                "api-reference",
                "observability",
        ):
            self.assertIn(page_id, content)
        for phrase in (
            "data-page-target",
            "activePage",
            "pageFromLocation",
            "pathFromPage",
            "routePaths",
            "navigateToPage",
            "window.location.pathname",
            "aria-current",
            "fileInputRef.current?.click",
            "includesSelectedModel",
            "renderPage",
            "API reference",
            "Observability",
        ):
            self.assertIn(phrase, source)

    def test_styles_define_premium_visual_system(self):
        css = STYLE_SOURCE.read_text()

        for token in (
            "--surface-glass",
            "--accent-lime",
            "--accent-coral",
            "--accent-blue",
            ".hero-visual",
            ".stage-card",
            ".proof-card",
            ".page-view",
            ".premium-page",
            ".motion-grid",
            ".motion-orbit",
            ".motion-stream",
            ".motion-marquee",
            ".page-transition-beam",
            ".visually-hidden-file",
            "@keyframes page-enter",
            "@keyframes orbit-spin",
            "@keyframes stream-sweep",
            "@keyframes marquee-slide",
            "@media (prefers-reduced-motion: reduce)",
        ):
            self.assertIn(token, css)


if __name__ == "__main__":
    unittest.main()

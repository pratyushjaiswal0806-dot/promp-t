import os
import shutil
import subprocess
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from promptcompiler.server import PromptCompilerHandler


class WebE2ETests(unittest.TestCase):
    def test_browser_ui_flow_and_responsive_contract(self):
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if not shutil.which("node") or not shutil.which(chrome_path):
            self.skipTest("Node and Google Chrome are required for browser E2E checks")

        with patch.dict(os.environ, {"PROMPTCOMPILER_DISABLE_DOTENV": "1"}, clear=False):
            os.environ.pop("NVIDIA_API_KEY", None)
            server = ThreadingHTTPServer(("127.0.0.1", 0), PromptCompilerHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"

            try:
                result = subprocess.run(
                    ["node", "tests/web_e2e_runner.mjs", base_url],
                    check=False,
                    cwd=".",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
            finally:
                server.shutdown()
                server.server_close()

        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()

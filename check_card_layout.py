"""Measure card pages in an isolated, headless Chromium window."""

import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


WIDTH = 640
HEIGHT = 900
CHECK_SCRIPT = """
<script>
window.addEventListener("load", () => {
  const results = [...document.querySelectorAll("iframe")].map((frame) => {
    const page = frame.contentDocument;
    const content = page?.querySelector("main") || page?.body;
    if (!content || page.querySelector("parsererror")) return "cannot render this card";
    if ([...page.images].some((image) => !image.naturalWidth)) return "missing image";

    const width = Math.max(page.documentElement.scrollWidth, page.body.scrollWidth);
    const height = Math.max(page.documentElement.scrollHeight, page.body.scrollHeight);
    if (width > frame.width || height > frame.height) {
      return `renders at ${width} × ${height}px`;
    }
    return null;
  });
  document.querySelector("#result").textContent = JSON.stringify(results);
});
</script>
"""


def find_browser():
    for command in ("chrome", "google-chrome", "chromium", "chromium-browser", "msedge", "microsoft-edge"):
        executable = shutil.which(command)
        if executable:
            return executable

    for folder in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        if folder in os.environ:
            for install in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"):
                executable = Path(os.environ[folder]) / install
                if executable.is_file():
                    return str(executable)

    executable = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if executable.is_file():
        return str(executable)
    raise ValueError("Install Chrome, Chromium, or Edge, or pass --browser with its executable path")


def check_card_layout(cards, browser=None):
    browser = browser or find_browser()
    with TemporaryDirectory(prefix="epub-layout-") as directory:
        temp = Path(directory)
        preview = temp / "check.html"
        for start in range(0, len(cards), 40):
            batch = cards[start:start + 40]
            frames = "".join(
                f'<iframe style="border:0" width="{WIDTH}" height="{HEIGHT}" '
                f'src="{html.escape(card.resolve().as_uri(), quote=True)}"></iframe>'
                for card in batch
            )
            preview.write_text(
                f'<!doctype html><meta charset="utf-8"><pre id="result"></pre>{CHECK_SCRIPT}{frames}',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    browser, "--headless", "--disable-gpu", "--no-first-run",
                    "--allow-file-access-from-files", f"--user-data-dir={temp / 'profile'}",
                    "--dump-dom", preview.as_uri(),
                ],
                capture_output=True, encoding="utf-8", errors="replace", timeout=60,
            )
            output = re.search(r'<pre id="result">(.+?)</pre>', result.stdout)
            if result.returncode or not output:
                raise ValueError("Chromium failed to measure the card pages")
            problems = json.loads(html.unescape(output.group(1)))
            if len(problems) != len(batch):
                raise ValueError("Chromium did not measure every card page")
            errors = [f"{card.name}: {problem}" for card, problem in zip(batch, problems) if problem]
            if errors:
                raise ValueError(f"Cards must fit a {WIDTH} × {HEIGHT}px page:\n" + "\n".join(errors))

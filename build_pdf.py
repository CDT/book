"""Build a shuffled PDF with one web-style card per page."""

import argparse
import html
import json
import math
import random
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from build_epub import ROOT
from check_card_layout import find_browser


SITE = ROOT / "site"
BOOK_PDF = ROOT / "output" / "pdf" / "book.pdf"
PREVIEW_SCRIPT = """
const entries = JSON.parse(document.querySelector("#card-data").textContent);
const pages = [...document.querySelectorAll(".print-page")];
const problems = [];
for (const [index, page] of pages.entries()) {
  const entry = entries[index];
  try {
    renderCard(page.querySelector("article"), entry.source, entry.url);
  } catch (error) {
    problems.push(entry.name + ": " + error.message);
  }
}

window.addEventListener("load", () => {
  const heights = [];
  for (const [index, page] of pages.entries()) {
    const sheet = page.getBoundingClientRect();
    const bottomMargin = parseFloat(getComputedStyle(page).paddingBottom);
    const card = page.querySelector("article");
    const name = entries[index].name;
    const height = card.getBoundingClientRect().bottom - sheet.top + bottomMargin;
    heights.push(height);
    if (height > sheet.height || card.scrollWidth > card.clientWidth + 1) {
      problems.push(name + " does not fit on one A4 page");
    }
    if ([...card.querySelectorAll("img")].some((image) => !image.naturalWidth)) {
      problems.push(name + " has an image that did not load");
    }
    for (const hero of card.querySelectorAll(".card-hero")) {
      if (hero.querySelector("figcaption").offsetHeight > hero.clientHeight) {
        problems.push(name + " has a title or definition that overflows its illustration");
      }
    }
  }
  document.querySelector("#layout-result").textContent = JSON.stringify({ problems, heights });
});
"""


def preview_html(cards):
    entries = json.dumps([
        {"name": card.name, "url": card.resolve().as_uri(), "source": card.read_text(encoding="utf-8")}
        for card in cards
    ]).replace("<", r"\u003c")
    pages = '<section class="print-page"><article class="card-content"></article></section>' * len(cards)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Knowledge Cards</title>
  <link rel="stylesheet" href="{(SITE / 'styles.css').as_uri()}">
  <link rel="stylesheet" href="{(SITE / 'print.css').as_uri()}">
</head>
<body>
  {pages}
  <pre id="layout-result" hidden></pre>
  <script id="card-data" type="application/json">{entries}</script>
  <script src="{(SITE / 'card-content.js').as_uri()}"></script>
  <script>{PREVIEW_SCRIPT}</script>
</body>
</html>
"""


def build_pdf(source_dir, output, rng, browser=None):
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as error:
        raise ValueError("Install pypdf with: python -m pip install pypdf") from error

    cards = sorted(source_dir.rglob("*.xhtml"))
    if not cards:
        raise ValueError(f"No XHTML cards found under {source_dir}")
    rng.shuffle(cards)
    browser = browser or find_browser()

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="card-pdf-", dir=output.parent) as directory:
        work = Path(directory)
        preview = work / "cards.html"
        preview.write_text(preview_html(cards), encoding="utf-8")
        temporary_pdf = work / "cards.pdf"
        command = [
            browser, "--headless", "--disable-gpu", "--no-first-run",
            f"--user-data-dir={work / 'profile'}", "--window-size=794,1123",
        ]

        layout = subprocess.run(
            command + ["--dump-dom", preview.as_uri()],
            capture_output=True, encoding="utf-8", errors="replace", timeout=120,
        )
        result = re.search(r'<pre id="layout-result" hidden="">(.+?)</pre>', layout.stdout)
        if layout.returncode or not result:
            raise ValueError("Chromium could not measure the PDF pages")
        measurements = json.loads(html.unescape(result.group(1)))
        if measurements["problems"]:
            raise ValueError("\n".join(measurements["problems"]))

        printed = subprocess.run(
            command + [
                "--no-pdf-header-footer", f"--print-to-pdf={temporary_pdf}", preview.as_uri(),
            ],
            capture_output=True, timeout=120,
        )
        if printed.returncode or not temporary_pdf.is_file():
            raise ValueError("Chromium could not print the PDF")
        trimmed_pdf = work / "trimmed.pdf"
        with temporary_pdf.open("rb") as stream:
            reader = PdfReader(stream)
            page_count = len(reader.pages)
            if page_count != len(cards):
                raise ValueError(f"PDF has {page_count} pages for {len(cards)} cards")
            writer = PdfWriter(clone_from=reader)
            for page, height in zip(writer.pages, measurements["heights"], strict=True):
                # Browser layout measures CSS pixels. PDF coordinates use points from the bottom.
                height_in_points = math.ceil(height * 72 / 96)
                bottom = max(float(page.mediabox.bottom), float(page.mediabox.top) - height_in_points)
                page.mediabox.bottom = bottom
                page.cropbox.bottom = bottom
            writer.write(trimmed_pdf)
        trimmed_pdf.replace(output)

    return len(cards)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BOOK_PDF)
    parser.add_argument("--seed", type=int, help="use the same seed to repeat a shuffle")
    parser.add_argument("--browser", help="path to Chrome, Chromium, or Edge")
    args = parser.parse_args()
    try:
        count = build_pdf(ROOT / "cards", args.output, random.Random(args.seed), args.browser)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"{error}\n")
    print(f"Wrote {args.output} ({count} pages)")


if __name__ == "__main__":
    main()

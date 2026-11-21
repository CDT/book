"""Generate a static Knowledge Cards website for GitHub Pages.

Run build_epub.py first: the generated website includes the X3 EPUB.
"""

import json
import shutil
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
SOURCE_CARDS = ROOT / "cards"
SOURCE_SITE = ROOT / "site"
OUTPUT = ROOT / "dist"
XHTML = "{http://www.w3.org/1999/xhtml}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def build():
    epub = ROOT / "book.epub"
    if not epub.is_file():
        raise FileNotFoundError("book.epub missing: run python build_epub.py first")

    cards = sorted(SOURCE_CARDS.rglob("*.xhtml"))
    if not cards:
        raise ValueError("No cards found")

    catalog = []
    for path in cards:
        page = ElementTree.parse(path).getroot()
        title = (page.findtext(f"{XHTML}head/{XHTML}title") or "").strip()
        if not title:
            raise ValueError(f"{path}: missing title")
        for image in page.iter(f"{XHTML}img"):
            image_path = (path.parent / image.attrib["src"]).resolve()
            if not image_path.is_relative_to(SOURCE_CARDS.resolve()) or not image_path.is_file():
                raise ValueError(f"{path}: missing or invalid illustration {image.attrib['src']!r}")

        relative = path.relative_to(SOURCE_CARDS)
        catalog.append({
            "title": title,
            "language": page.get(XML_LANG, "en"),
            "category": relative.parts[0] if len(relative.parts) > 1 else "",
            "url": "cards/" + quote(relative.as_posix(), safe="/"),
        })

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(SOURCE_SITE, OUTPUT)
    shutil.copytree(SOURCE_CARDS, OUTPUT / "cards")
    shutil.copy2(epub, OUTPUT / "book.epub")
    (OUTPUT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUT / ".nojekyll").touch()
    print(f"Built {OUTPUT} with {len(catalog)} cards and X3 EPUB")


if __name__ == "__main__":
    build()

"""Generate a static Knowledge Cards website for GitHub Pages.

Run build_epub.py first. Illustrations in dist/ are whitespace-trimmed solely
for web reading; original source images and the X3 EPUB are left unchanged.
"""

import json
import shutil
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE_CARDS = ROOT / "cards"
SOURCE_SITE = ROOT / "site"
OUTPUT = ROOT / "dist"
XHTML = "{http://www.w3.org/1999/xhtml}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def optimize_web_illustrations():
    """Crop white paper edges in the published copy, preserving source art."""
    for path in (OUTPUT / "cards" / "images").glob("*.jpg"):
        with Image.open(path) as source:
            gray = source.convert("L")
            ink = gray.point(lambda shade: 255 if shade < 222 else 0)
            bounds = ink.getbbox()
            if not bounds:
                continue
            left, top, right, bottom = bounds
            width, height = gray.size
            pad = max(7, round(min(width, height) * 0.052))
            bounds = (
                max(0, left - pad), max(0, top - pad),
                min(width, right + pad), min(height, bottom + pad),
            )
            if bounds[2] - bounds[0] >= width - 10 and bounds[3] - bounds[1] >= height - 10:
                continue
            gray.crop(bounds).save(path, "JPEG", quality=87, optimize=True)


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
    optimize_web_illustrations()
    # Web image dimensions are known after whitespace trimming. Expose their
    # final aspect ratio so the viewer reserves a correctly sized placeholder
    # before requesting the image, avoiding layout shift on slow connections.
    for entry in catalog:
        rendered_card = OUTPUT / entry["url"]
        page = ElementTree.parse(rendered_card).getroot()
        image = next(page.iter(f"{XHTML}img"), None)
        if image is not None:
            artwork = (rendered_card.parent / image.attrib["src"]).resolve()
            with Image.open(artwork) as source:
                entry["illustration_ratio"] = round(source.width / source.height, 5)
    shutil.copy2(epub, OUTPUT / "book.epub")
    (OUTPUT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUT / ".nojekyll").touch()
    print(f"Built {OUTPUT} with {len(catalog)} cards, cropped web art, and X3 EPUB")


if __name__ == "__main__":
    build()

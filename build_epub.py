"""Build a shuffled, fixed-layout EPUB from the cards directory."""

import argparse
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree
from xml.sax.saxutils import escape, quoteattr
from zipfile import ZIP_DEFLATED, ZipFile

from check_card_layout import HEIGHT, WIDTH, check_card_layout


ROOT = Path(__file__).resolve().parent
BOOK = ROOT / "book.epub"
XHTML = "{http://www.w3.org/1999/xhtml}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
MEDIA_TYPES = {
    ".css": "text/css",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}


def build_epub(source_dir, output, rng, browser=None):
    cards = sorted(source_dir.rglob("*.xhtml"))
    if not cards:
        raise ValueError(f"No XHTML cards found under {source_dir}")
    rng.shuffle(cards)

    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
    ]
    spine = []
    toc = []
    languages = set()

    for number, card in enumerate(cards, start=1):
        page = ElementTree.parse(card).getroot()
        title = (page.findtext(f"{XHTML}head/{XHTML}title") or "").strip()
        language = page.get(XML_LANG)
        if not title or not language:
            raise ValueError(f"{card} needs a title and xml:lang")
        viewport = page.find(f"{XHTML}head/{XHTML}meta[@name='viewport']")
        dimensions = viewport.get("content", "") if viewport is not None else ""
        if not re.fullmatch(rf"width\s*=\s*{WIDTH}\s*,\s*height\s*=\s*{HEIGHT}", dimensions.strip()):
            raise ValueError(f"{card} needs a {WIDTH} × {HEIGHT}px viewport")
        languages.add(language)
        href = quote("cards/" + card.relative_to(source_dir).as_posix())
        manifest.append(f'<item id="card-{number}" href="{href}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="card-{number}"/>')
        toc.append(
            f'<li><a href="{href}" lang={quoteattr(language)} '
            f'xml:lang={quoteattr(language)}>{escape(title)}</a></li>'
        )

    assets = sorted(
        path for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in MEDIA_TYPES
    )
    for number, asset in enumerate(assets, start=1):
        href = quote("cards/" + asset.relative_to(source_dir).as_posix())
        media_type = MEDIA_TYPES[asset.suffix.lower()]
        manifest.append(f'<item id="asset-{number}" href="{href}" media-type="{media_type}"/>')

    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    language_tags = "".join(f"<dc:language>{escape(lang)}</dc:language>" for lang in sorted(languages))
    package = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="deck-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="deck-id">urn:uuid:31574790-4bd8-4d8a-95bd-f77665b3f11e</dc:identifier>
    <dc:title>Knowledge Cards</dc:title>
    {language_tags}
    <meta property="dcterms:modified">{modified}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
  </metadata>
  <manifest>{''.join(manifest)}</manifest>
  <spine>{''.join(spine)}</spine>
</package>
"""
    navigation = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"
      lang="en" xml:lang="en">
  <head><title>Contents</title></head>
  <body><nav epub:type="toc" id="toc">
    <h1>Contents</h1>
    <ol>{''.join(toc)}</ol>
  </nav></body>
</html>
"""
    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""
    check_card_layout(cards, browser)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as book:
        book.writestr("mimetype", "application/epub+zip", compress_type=0)
        book.writestr("META-INF/container.xml", container)
        book.writestr("EPUB/package.opf", package)
        book.writestr("EPUB/nav.xhtml", navigation)
        for path in cards + assets:
            book.write(path, "EPUB/cards/" + path.relative_to(source_dir).as_posix())

    return len(cards)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BOOK)
    parser.add_argument("--seed", type=int, help="use the same seed to repeat a shuffle")
    parser.add_argument("--browser", help="path to Chrome, Chromium, or Edge for page-fit validation")
    args = parser.parse_args()
    try:
        count = build_epub(ROOT / "cards", args.output, random.Random(args.seed), args.browser)
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    print(f"Wrote {args.output} ({count} cards)")


if __name__ == "__main__":
    main()

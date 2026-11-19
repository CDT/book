# Knowledge Cards

## Web viewer

Run `python serve_cards.py` and open [the card library](http://localhost:2345). The viewer reads the same XHTML files as the EPUB builder. Refresh the browser after adding or editing cards.

## PDF

Run `python build_pdf.py` to shuffle the deck and write `output/pdf/book.pdf`, the file served by the site's Download PDF button. The PDF shares the web viewer's card styles and places one card on each page, with the page height trimmed to the content. Rebuild after adding or editing cards.

The PDF build uses Chrome, Chromium, or Edge and the `pypdf` Python package (`python -m pip install pypdf`). Use `--seed 42` for a repeatable shuffle or `--browser` for a custom browser executable.

## EPUB

Run `python build_epub.py` to shuffle the deck and write `book.epub`. The EPUB’s reading order and table of contents use the same shuffle. For a repeatable order with the same set of cards, run `python build_epub.py --seed 42`.

The builder uses Chrome, Chromium, or Edge to check that every card fits on one page before writing the EPUB. Use `--browser` to point to a browser executable in a custom location.

Add one UTF-8 XHTML file per card under `cards/`.

| Category | Directory |
| --- | --- |
| English and Japanese vocabulary | `cards/vocabulary/` |
| Citations | `cards/citations/` |
| Philosophy and history | `cards/knowledge/` |

Use [the first vocabulary card](cards/vocabulary/remuneration.xhtml) for the shared stylesheet and fixed viewport. Give each card its own title, set both `lang` and `xml:lang` to the card’s language (for example, `ja` for Japanese), and keep its contents within the 640 × 900 page. Save card images under `cards/images/` and reference them with relative paths and descriptive alt text.

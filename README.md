# Knowledge Cards

## Web viewer

Run `python serve_cards.py` and open [the card library](http://localhost:2345). The viewer reads the same XHTML files as the EPUB builder. Refresh the browser after adding or editing cards.

## EPUB

Run `python build_epub.py` to shuffle the deck and write `book.epub`, which the web viewer serves through its **Download EPUB** button. Rebuild after adding or editing cards. The EPUB’s reading order and table of contents use the same shuffle. For a repeatable order with the same set of cards, run `python build_epub.py --seed 42`.

The builder uses Chrome, Chromium, or Edge to check that every card fits on one page before writing the EPUB. Use `--browser` to point to a browser executable in a custom location.

Each EPUB page contains one knowledge point. Add one UTF-8 XHTML file per knowledge point under `cards/`. The EPUB uses a single-page fixed layout with high-contrast type and compact illustrations for small screens. Keep the main explanation brief and use one short example where helpful. If a card overflows, trim repeated wording and secondary details, or shorten the illustration. Keep the shared font size and rerun the build until the card fits on one page.

| Category | Directory |
| --- | --- |
| English and Japanese vocabulary | `cards/vocabulary/` |
| Citations | `cards/citations/` |
| Philosophy and history | `cards/knowledge/` |

Use [the first vocabulary card](cards/vocabulary/remuneration.xhtml) for the shared stylesheet and fixed viewport. Give each card its own title, set both `lang` and `xml:lang` to the card’s language (for example, `ja` for Japanese), and keep its contents within the 640 × 900 page. Save card images under `cards/images/` and reference them with relative paths and descriptive alt text.

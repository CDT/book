# Knowledge Cards

## Web viewer

Run `python serve_cards.py` and open [the card library](http://localhost:2345). The viewer reads the same XHTML files as the EPUB builder. Refresh the browser after adding or editing cards.

## EPUB for Xteink X3

Install the build dependencies with `python -m pip install -r requirements.txt`. Run `python build_epub.py` to shuffle the deck and create `book.epub`. The web viewer serves this file through its **Download EPUB** button. Run with `--seed 42` for a repeatable order.

The Xteink X3 edition packages each knowledge point as one baseline grayscale JPEG inside its own EPUB page. The EPUB declares a 528 × 792 portrait viewport. Each image is 448 × 610 to leave space for the reader’s margins and chapter indicator. On the reader, keep EPUB images enabled. On devices that reflow EPUB text, the text is already drawn into each card image.

Put each knowledge point in its own UTF-8 XHTML file under `cards/`. Include one small, high-contrast illustration to support the meaning, and keep the explanation to one short definition, a useful phrase and one short example. If a card is too long, the build reports its filename. Trim the card and rebuild.

| Category | Directory |
| --- | --- |
| English and Japanese vocabulary | `cards/vocabulary/` |
| Citations | `cards/citations/` |
| Philosophy and history | `cards/knowledge/` |

Use [the first vocabulary card](cards/vocabulary/remuneration.xhtml) for the source structure and shared web stylesheet. Give each card its own title, set both `lang` and `xml:lang` to the card’s language (for example, `ja` for Japanese). Save card images under `cards/images/` and reference them with relative paths and descriptive alt text.

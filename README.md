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

## GitHub Pages deployment

The website is published via [GitHub Actions](.github/workflows/pages.yml) when `main` changes.
The default project-site URL is `https://cdt.github.io/book/`.

Pages has no Python server, so `build_site.py` writes `dist/catalog.json` and
copies all XHTML cards and illustrations as static assets. Website links are
relative, so the viewer works locally and under the `/book/` project path.
The workflow builds the X3 EPUB and includes it in the download link.

If Pages hasn't been activated automatically, open **Settings → Pages**
and set **Build and deployment → Source: GitHub Actions**; then rerun
the **Publish Knowledge Cards** workflow. GitHub Pages on a **private**
repository requires a GitHub Pro, Team, or Enterprise plan. Otherwise,
publish the site from a public repository instead.

To preview locally, run `python serve_cards.py`. To test the deploy
files locally, run `python build_epub.py && python build_site.py`.

## Restored classical Chinese quotations

The collection also contains **30 illustrated selections from 增广贤文** under `cards/citations/`, restored from the original X3 EPUB. The web reader shuffles these together with the **17 English vocabulary cards** into a single 47-card deck; it intentionally has no category/search/list interface. Each quote retains its separate grayscale illustration, and EPUB generation still enforces one page per card.

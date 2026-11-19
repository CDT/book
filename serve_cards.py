"""Serve the card library locally on port 2345."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from xml.etree import ElementTree

from build_epub import MEDIA_TYPES, ROOT, XHTML, XML_LANG
from build_pdf import BOOK_PDF


CARDS = ROOT / "cards"
SITE = ROOT / "site"
STATIC_FILES = {
    "/": (SITE / "index.html", "text/html; charset=utf-8"),
    "/styles.css": (SITE / "styles.css", "text/css; charset=utf-8"),
    "/card-content.js": (SITE / "card-content.js", "text/javascript; charset=utf-8"),
    "/viewer.js": (SITE / "viewer.js", "text/javascript; charset=utf-8"),
    "/book.pdf": (BOOK_PDF, "application/pdf"),
}


def card_catalog():
    catalog = []
    for path in sorted(CARDS.rglob("*.xhtml")):
        relative = path.relative_to(CARDS)
        page = ElementTree.parse(path).getroot()
        title = (page.findtext(f"{XHTML}head/{XHTML}title") or "").strip()
        catalog.append({
            "title": title or path.stem,
            "language": page.get(XML_LANG, "en"),
            "category": relative.parts[0] if len(relative.parts) > 1 else "",
            "url": "/cards/" + quote(relative.as_posix()),
        })
    return catalog


class CardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.serve()

    def do_HEAD(self):
        self.serve(include_body=False)

    def serve(self, include_body=True):
        route = unquote(urlsplit(self.path).path)
        if route == "/api/cards":
            try:
                data = json.dumps(card_catalog(), ensure_ascii=False).encode("utf-8")
            except (OSError, ElementTree.ParseError) as error:
                self.log_error("Could not load cards: %s", error)
                self.send_error(500, "Could not load the card library")
                return
            self.send_content(data, "application/json; charset=utf-8", include_body)
            return

        if route.startswith("/cards/"):
            path = (CARDS / route.removeprefix("/cards/")).resolve()
            media_type = {
                **MEDIA_TYPES,
                ".xhtml": "application/xhtml+xml; charset=utf-8",
            }.get(path.suffix.lower())
            if not path.is_relative_to(CARDS) or not media_type:
                self.send_error(404)
                return
        elif route in STATIC_FILES:
            path, media_type = STATIC_FILES[route]
        else:
            self.send_error(404)
            return

        try:
            data = path.read_bytes()
        except OSError:
            self.send_error(404)
            return
        self.send_content(data, media_type, include_body)

    def send_content(self, data, media_type, include_body):
        self.send_response(200)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if include_body:
            self.wfile.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=2345)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), CardHandler) as server:
        print(f"Card library at http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

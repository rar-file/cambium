"""Serve the Birch Stem Tracer locally, with its photos and a traces file.

    python tools/serve_tracer.py [port]        # then open http://127.0.0.1:8765/

GET  /               the tracer page (tools/birch-stem-tracer.html)
GET  /api/images     the photos to load: the Gullmarsskogen stand photos in
                     reference/ and the silver-birch whole_tree photos in
                     ../tree-data (read only), as [{url, name, size, group}]
GET  /img/<g>/<file> one of those photos
GET  /api/traces     reference/stem_traces.json (empty if not yet written)
POST /api/traces     replace reference/stem_traces.json (written atomically)

Listens on 127.0.0.1 only.
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "tools" / "birch-stem-tracer.html"
TRACES = ROOT / "reference" / "stem_traces.json"
SOURCES = {
    "ref": (ROOT / "reference", "gullmarsskogen_*.jpg"),
    # the other session's library: only ever opened for reading
    "inat": (ROOT.parent / "tree-data" / "inat-photos" / "silver_birch" / "whole_tree", "*.jpg"),
}
LOCK = threading.Lock()


def listing():
    out = []
    for group, (folder, pattern) in SOURCES.items():
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob(pattern)):
            out.append({"url": f"/img/{group}/{f.name}", "name": f.name, "size": f.stat().st_size, "group": group})
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/index.html"):
            return self._send(200, HTML.read_bytes(), "text/html; charset=utf-8")
        if path == "/api/images":
            return self._send(200, json.dumps(listing()).encode(), "application/json")
        if path == "/api/traces":
            with LOCK:
                body = TRACES.read_bytes() if TRACES.exists() else b'{"images": {}, "settings": {}}'
            return self._send(200, body, "application/json")
        parts = path.split("/")
        if len(parts) == 4 and parts[1] == "img" and parts[2] in SOURCES:
            folder, pattern = SOURCES[parts[2]]
            # only a file that the listing itself offers (no path tricks)
            match = [f for f in folder.glob(pattern) if f.name == parts[3]]
            if match:
                return self._send(200, match[0].read_bytes(), "image/jpeg")
        return self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if urlparse(self.path).path != "/api/traces":
            return self._send(404, b"not found", "text/plain")
        n = int(self.headers.get("Content-Length", "0"))
        try:
            data = json.loads(self.rfile.read(n).decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("images"), dict):
                raise ValueError("expected {images: {...}, settings: {...}}")
        except (ValueError, UnicodeDecodeError) as e:
            return self._send(400, str(e).encode(), "text/plain")
        with LOCK:
            tmp = TRACES.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
            os.replace(tmp, TRACES)
        return self._send(200, b'{"ok": true}', "application/json")

    def log_message(self, fmt, *args):
        if "POST" in (args[0] if args else ""):
            sys.stderr.write("%s saved traces\n" % self.log_date_time_string())


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"Birch Stem Tracer on http://127.0.0.1:{port}/  ({len(listing())} photos; traces -> {TRACES})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()

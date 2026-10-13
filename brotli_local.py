#!/usr/bin/env python3
"""
brotli_local.py - run the Brotli S3 Viewer on your own machine.

The browser can't fetch links that don't send CORS headers. This tiny local server fetches
the link for the page (with your username/password if needed), decompresses it, and hands the
text back. Nothing leaves your computer except the request to the link itself.

Usage:
    pip install brotli
    python brotli_local.py            # then open http://localhost:8765
    python brotli_local.py --port 9000
Keep brotli_viewer.html in the same folder as this script.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    import brotli
except ImportError:
    try:
        import brotlicffi as brotli
    except ImportError:
        sys.exit("Missing dependency. Install it with:  pip install brotli")

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "brotli_viewer.html")
MAX_BYTES = 512 * 1024 * 1024


def looks_like_text(b):
    try:
        b[:4096].decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def decompress(data):
    try:
        return brotli.decompress(data)
    except brotli.error:
        # The server may already have decoded it (Content-Encoding: br).
        if looks_like_text(data):
            return data
        raise


class Handler(BaseHTTPRequestHandler):
    server_version = "BrotliLocal/1.0"

    def log_message(self, fmt, *args):  # keep presigned query strings out of the console
        sys.stderr.write("%s - %s\n" % (self.address_string(), (fmt % args).split("?")[0]))

    def _send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, code, msg):
        self._send(code, json.dumps({"error": msg}).encode(), "application/json")

    def _same_origin(self):
        # Block other websites from using this helper (DNS-rebinding / cross-site calls).
        host = self.headers.get("Host", "").split(":")[0]
        if host not in ("localhost", "127.0.0.1"):
            return False
        origin = self.headers.get("Origin")
        if origin:
            return urllib.parse.urlparse(origin).hostname in ("localhost", "127.0.0.1")
        return True

    def do_GET(self):
        if not self._same_origin():
            return self._json_error(403, "Forbidden")
        if self.path.split("?")[0] in ("/", "/index.html", "/brotli_viewer.html"):
            try:
                with open(PAGE, "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                return self._json_error(500, "brotli_viewer.html must be in the same folder as brotli_local.py")
        self._json_error(404, "Not found")

    def do_POST(self):
        if self.path != "/api/fetch" or not self._same_origin():
            return self._json_error(404, "Not found")
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n) or b"{}")
            url = req.get("url", "")
        except Exception:
            return self._json_error(400, "Bad request")
        if urllib.parse.urlparse(url).scheme not in ("http", "https"):
            return self._json_error(400, "The link must start with http:// or https://")

        headers = {"User-Agent": "brotli-local/1.0"}
        user, pw = req.get("user") or "", req.get("pass") or ""
        host = (urllib.parse.urlparse(url).hostname or "").lower()
        # S3 never uses basic auth and answers HTTP 400 if it receives one, so don't send it there.
        if (user or pw) and not host.endswith(".amazonaws.com"):
            headers["Authorization"] = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                data = r.read(MAX_BYTES + 1)
        except urllib.error.HTTPError as e:
            detail = ""
            try:  # S3 explains itself in XML: <Code>…</Code><Message>…</Message>
                body = e.read(4096).decode("utf-8", "replace")
                import re
                code = re.search(r"<Code>(.*?)</Code>", body)
                msg = re.search(r"<Message>(.*?)</Message>", body)
                if code or msg:
                    detail = ": " + " - ".join(m.group(1) for m in (code, msg) if m)
            except Exception:
                pass
            hint = " (presigned link expired, or access denied)" if e.code == 403 and not detail else ""
            return self._json_error(e.code, f"The server answered HTTP {e.code}{detail}{hint}")
        except Exception as e:
            return self._json_error(502, f"Could not reach the link: {e}")
        if len(data) > MAX_BYTES:
            return self._json_error(413, "File is larger than 512 MB")
        try:
            out = decompress(data)
        except brotli.error:
            return self._json_error(422, "The data is not valid Brotli.")
        self._send(200, out, "text/plain; charset=utf-8", {"X-Compressed-Size": str(len(data))})


def main():
    ap = argparse.ArgumentParser(description="Local helper for the Brotli S3 Viewer")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

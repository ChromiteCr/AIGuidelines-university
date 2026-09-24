#!/usr/bin/env python3
"""Preview docs/ locally exactly the way GitHub Pages serves it.

file:// cannot show ai.policy.nestudy.cn/MIT, and `python3 -m http.server`
gets three things wrong: it lists directories that have no index.html, it
answers a missing path with its own error page, and on macOS it ignores case.
Pages does none of these — paths are case-sensitive, and a missing path gets
docs/404.html with status 404, which is what lets /mit, /johns-hopkins and
/麻省理工 redirect. This server behaves the same, so what works here works online.

Usage:  python3 tools/serve.py [port]        then open http://localhost:8765/MIT
"""

import functools
import http.server
import os
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


def case_exact(fs_path):
    """True only if every path component matches the disk's spelling exactly.

    macOS disks ignore case, so /mit would quietly open docs/MIT here — but
    Pages runs on a case-sensitive filesystem, where /mit is a 404 that the
    router must catch. Refusing inexact case keeps the preview honest.
    """
    try:
        rel = Path(fs_path).resolve().relative_to(DOCS.resolve())
    except ValueError:
        return True
    cur = DOCS
    for part in rel.parts:
        if part not in os.listdir(cur):
            return False
        cur = cur / part
    return True


class PagesHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.exists(path) and not case_exact(path):
            self.send_error(404)
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404)          # Pages never lists a directory
        return None

    def send_error(self, code, message=None, explain=None):
        page = DOCS / "404.html"
        if code != 404 or not page.exists():
            return super().send_error(code, message, explain)
        body = page.read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"  {self.command} {self.path} → {args[1] if len(args) > 1 else ''}\n")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    handler = functools.partial(PagesHandler, directory=str(DOCS))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as srv:
        print(f"docs/ → http://localhost:{port}/    试试 /MIT、/mit、/johns-hopkins    Ctrl+C 结束")
        srv.serve_forever()


if __name__ == "__main__":
    main()

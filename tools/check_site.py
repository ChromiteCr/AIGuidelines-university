#!/usr/bin/env python3
"""Check every page under docs/ before it goes online.

  - every page is a real document (doctype + viewport), so it renders in
    standards mode and at phone width
  - every page's HTML nests correctly
  - every relative link points at a file that exists, and every in-page
    #anchor points at an id that exists on that page
  - every school page is reachable from the home page and the 404 router

Run after the builders; exits non-zero on any problem.

Usage:  python3 tools/check_site.py
"""

import html.parser
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
VOID = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed",
        "source", "track", "wbr", "option"}
JS_ROUTED = {"atlas.html"}   # fragments there are read by script, not ids


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors, self.links, self.ids = [], [], [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"</{tag}> vs <{self.stack[-1] if self.stack else '∅'}>")


def target(page, href):
    """The file a relative href resolves to, or None for external/JS links."""
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or href.startswith(("mailto:", "javascript:")):
        return None, None
    path = unquote(parts.path)
    base = page.parent
    t = (base / path).resolve() if path else page
    if path.endswith("/") or t.is_dir():
        t = t / "index.html"
    return t, parts.fragment


def main():
    pages = sorted(DOCS.rglob("*.html"))
    parsed = {}
    problems = []
    for p in pages:
        text = p.read_text(encoding="utf-8")
        rel = p.relative_to(DOCS)
        if not text.lstrip().lower().startswith("<!doctype html"):
            problems.append(f"{rel}: 缺少 <!doctype html>")
        if 'name="viewport"' not in text:
            problems.append(f"{rel}: 缺少 viewport")
        pg = Page()
        pg.feed(text)
        pg.close()
        if pg.errors or [t for t in pg.stack if t not in ("html", "head", "body")]:
            problems.append(f"{rel}: 嵌套错误 {pg.errors[:2]} 未闭合 {pg.stack[-3:]}")
        parsed[p] = pg

    n_links = 0
    for p, pg in parsed.items():
        if p.name == "404.html":
            continue                  # its links are built by script against the site root
        for href in pg.links:
            t, frag = target(p, href)
            if t is None:
                continue
            n_links += 1
            if not t.exists():
                problems.append(f"{p.relative_to(DOCS)}: 链接指向不存在的文件 {href}")
                continue
            if frag and t.name not in JS_ROUTED:
                ids = parsed[t].ids if t in parsed else set()
                if frag not in ids:
                    problems.append(f"{p.relative_to(DOCS)}: 锚点 {href} 在目标页不存在")

    # reachability of every school page
    school_dirs = sorted(d.name for d in DOCS.iterdir() if d.is_dir() and (d / "index.html").exists())
    home = DOCS / "index.html"
    home_links = {target(home, h)[0] for h in parsed[home].links} if home in parsed else set()
    for name in school_dirs:
        if (DOCS / name / "index.html").resolve() not in home_links:
            problems.append(f"主页没有链接到 /{name}")
    nf = (DOCS / "404.html").read_text(encoding="utf-8") if (DOCS / "404.html").exists() else ""
    m = re.search(r"var ALIASES = (\{.*?\});", nf, re.S)
    routed = set(json.loads(m.group(1)).values()) if m else set()
    for name in school_dirs:
        if name not in routed:
            problems.append(f"404 路由里没有 /{name}")

    print(f"页面       {len(pages)} 个（含 {len(school_dirs)} 个单校页面）")
    print(f"内部链接   {n_links} 条已核对")
    if problems:
        print(f"问题       {len(problems)} 处")
        for x in problems[:40]:
            print("  ! " + x)
        sys.exit(1)
    print("问题       0")


if __name__ == "__main__":
    main()

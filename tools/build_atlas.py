#!/usr/bin/env python3
"""data/policies.json + atlas/atlas.template.html  ->  docs/index.html

The template holds no policy content. It reads a single injected DATA object,
so regenerating the data regenerates the atlas. Never edit docs/index.html by
hand; edit the template or the data and re-run this.

Output lands in docs/ because that is one of the three directories GitHub Pages
can publish from without a build workflow, which gives the site the repository
root URL instead of a nested one.

Usage:  python3 tools/build_atlas.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "policies.json"
TPL = ROOT / "atlas" / "atlas.template.html"
OUT = ROOT / "docs" / "index.html"

MARKER = "/*__DATA__*/null"


def main():
    if not DATA.exists():
        sys.exit(f"missing {DATA} — run tools/build_data.py first")

    data = json.loads(DATA.read_text(encoding="utf-8"))
    tpl = TPL.read_text(encoding="utf-8")
    if MARKER not in tpl:
        sys.exit(f"marker {MARKER!r} not found in {TPL}")

    # </script> inside a string literal would close the block early.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = tpl.replace(MARKER, payload)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    # Tell Pages not to run the content through Jekyll.
    (OUT.parent / ".nojekyll").write_text("", encoding="utf-8")

    kb = len(html.encode("utf-8")) / 1024
    print(f"wrote {OUT.relative_to(ROOT)}  ({kb:.0f} KB, data {len(payload)/1024:.0f} KB)")


if __name__ == "__main__":
    main()

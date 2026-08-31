#!/usr/bin/env python3
"""data/policies.json + atlas/atlas.template.html  ->  docs/atlas.html

The template holds no policy content. It reads a single injected DATA object,
so regenerating the data regenerates the atlas. Never edit docs/atlas.html by
hand; edit the template or the data and re-run this.

Output lands in docs/ because that is one of the three directories GitHub Pages
can publish from without a build workflow. docs/index.html is the site's home
page, built separately, so the atlas takes its own filename.

Usage:  python3 tools/build_atlas.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sitelib import join_cjk  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "policies.json"
TPL = ROOT / "atlas" / "atlas.template.html"
OUT = ROOT / "docs" / "atlas.html"

MARKER = "/*__DATA__*/null"


def main():
    if not DATA.exists():
        sys.exit(f"missing {DATA} — run tools/build_data.py first")

    data = json.loads(DATA.read_text(encoding="utf-8"))
    tpl = TPL.read_text(encoding="utf-8")
    if MARKER not in tpl:
        sys.exit(f"marker {MARKER!r} not found in {TPL}")

    # The CJK line-break fix runs on the TEMPLATE ONLY. Applied to the finished
    # page it would also reach inside the injected JSON, where a Chinese string
    # containing a space would be silently rewritten — corrupting the dataset
    # the page is supposed to faithfully display.
    tpl = join_cjk(tpl)

    # </script> inside a string literal would close the block early.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = tpl.replace(MARKER, payload)

    # Read the payload back out and confirm it still parses to the same object.
    check = re.search(r"const DATA = (\{.*?\});\n", html, re.S)
    if not check or json.loads(check.group(1).replace("<\\/", "</")) != data:
        sys.exit("构建中止：页面内嵌的数据与 data/policies.json 不一致")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    # Tell Pages not to run the content through Jekyll.
    (OUT.parent / ".nojekyll").write_text("", encoding="utf-8")

    kb = len(html.encode("utf-8")) / 1024
    print(f"wrote {OUT.relative_to(ROOT)}  ({kb:.0f} KB, data {len(payload)/1024:.0f} KB)")


if __name__ == "__main__":
    main()

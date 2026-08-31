#!/usr/bin/env python3
"""home/home.html -> docs/index.html

The site's front door. It carries no policy content of its own, only the
headline figures and the two links, but those figures are hand-written like the
guidelines' are — so they go through the same check: each is registered as the
literal phrase it must appear as, filled in from data/policies.json.

Usage:  python3 tools/build_home.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sitelib import ROOT, assertion_builder, load_data, publish  # noqa: E402

SRC = ROOT / "home" / "home.html"
DST = ROOT / "docs" / "index.html"


def checks():
    d, dm, count, disclose = load_data()
    m = d["meta"]
    C = []
    add = assertion_builder(C)

    add("总校数", m["schools"], "<b>{n}</b><span lang=\"zh\">所大学，各自独立抽取")
    add("条款数", m["dimensions"], "<b>{n}</b><span lang=\"zh\">项可比条款")
    add("格数", m["cells"], "<b>{n}</b><span lang=\"zh\">格逐格对照",
        "三十所大学 × {n} 项条款的对照矩阵".replace("{n}", str(m["dimensions"])))
    add("引文核验", m["evidence_matched"], "<b>{n}</b><span lang=\"zh\">条引文经机器逐字核验",
        "当前 {n}/{n} 通过", "Currently {n}/{n} pass")
    add("有明文", m["filled"], "{n} 格有明文", "{n} with a rule")
    add("沉默格", m["silent"], "{n} 格沉默", "{n} silent")
    return C


def main():
    publish(SRC.read_text(encoding="utf-8"), DST, checks(), label="主页")


if __name__ == "__main__":
    main()

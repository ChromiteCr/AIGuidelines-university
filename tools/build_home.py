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
import html  # noqa: E402
import re  # noqa: E402

import build_guidelines as bg  # noqa: E402
import schools as reg  # noqa: E402
from sitelib import ROOT, assertion_builder, load_data, publish  # noqa: E402

SRC = ROOT / "home" / "home.html"
DST = ROOT / "docs" / "index.html"


def checks():
    d, dm, count, disclose = load_data()
    m = d["meta"]
    C = []
    add = assertion_builder(C)
    grid = f"{m['schools']} × {m['dimensions']}"

    add("总校数", m["schools"], "<b>{n}</b><span lang=\"zh\">所大学，逐校独立抽取",
        "美国 {n} 所大学 AI 使用政策比较研究", "AI Use Policies at {n} U.S. Universities",
        "采集美国 {n} 所大学", "{n} 校政策基本未涉及")
    add("条款数", m["dimensions"], "<b>{n}</b><span lang=\"zh\">项比较条款",
        "按 {n} 项条款逐校编码比较", "codes each against {n} provisions")
    add("格数", m["cells"], "<b>{n}</b><span lang=\"zh\">个编码单元（" + grid + "）",
        f"{m['schools']} 所大学 × {m['dimensions']} 项条款的编码矩阵")
    add("引文核验", m["evidence_matched"], "<b>{n}</b><span lang=\"zh\">条原文引证，逐字核验",
        "当前 {n}/{n} 通过", "Currently {n}/{n} pass")
    add("有明文", m["filled"], "{n} 格有明文", "{n} with a rule")
    add("未提及格", m["silent"], "{n} 格未提及", "{n} not addressed")

    # The verification section quotes the guidelines' own check counts, which
    # move whenever a figure is added to or removed from that document.
    n_assert = len(bg.checks())
    n_quote = len(re.findall(r"<blockquote>", bg.SRC.read_text(encoding="utf-8")))
    add("规范断言数", n_assert, "当前 {n} 处断言", "Currently {n} assertions")
    add("规范引文数", n_quote, "{n} 条引文全部通过", "and {n} quotations pass")
    return C


def school_index():
    """One entry per university, linking to its page, with its row of the atlas as a strip."""
    d, _, _, _ = load_data()
    out = []
    for s in sorted(d["schools"], key=lambda s: s["num"]):
        _, en, zh, _ = reg.SCHOOLS[s["id"]]
        strip = "".join(f'<i data-r="{c["rank"]}"></i>' for c in s["cells"])
        out.append(
            f'<a class="sch" href="{reg.slug(s["id"])}/" title="{html.escape(en)}">'
            f'<span class="n">{s["num"]:02d}</span><b>{html.escape(s["short"])}</b>'
            f'<span class="zh">{html.escape(zh)}</span><span class="fp">{strip}</span></a>')
    return "\n".join(out)


def main():
    src = SRC.read_text(encoding="utf-8")
    if "<!--__SCHOOLS__-->" not in src:
        raise SystemExit("home.html 缺少 <!--__SCHOOLS__--> 标记")
    publish(src.replace("<!--__SCHOOLS__-->", school_index()), DST, checks(), label="主页")


if __name__ == "__main__":
    main()

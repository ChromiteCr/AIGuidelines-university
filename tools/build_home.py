#!/usr/bin/env python3
"""home/home.html -> docs/index.html

The site's front door. It carries no policy content of its own, only the
headline figures, the three doors and the school index, but those figures are
hand-written like the guidelines' are — so they go through the same check: each
is registered as the literal phrase it must appear as, filled in from
data/policies.json and the admissions index.

Usage:  python3 tools/build_home.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import html  # noqa: E402
import re  # noqa: E402

import admissions as adm  # noqa: E402
import build_guidelines as bg  # noqa: E402
import schools as reg  # noqa: E402
from sitelib import ROOT, assertion_builder, load_data, publish, version_log  # noqa: E402

SRC = ROOT / "home" / "home.html"
DST = ROOT / "docs" / "index.html"


def checks():
    d, dm, count, disclose = load_data()
    m = d["meta"]
    C = []
    add = assertion_builder(C)
    grid = f"{m['schools']} × {m['dimensions']}"

    core = load_data(core=True)[0]["meta"]      # the thirty the guidelines rest on
    add("全站校数", m["schools"], "<title>{n} 所大学 AI 使用政策比较研究</title>",
        "<h1 lang=\"zh\">{n} 所大学 AI 使用政策比较研究</h1>", "AI Use Policies at {n} Universities: A Comparative Study",
        "<b>{n}</b><span lang=\"zh\">所大学，逐校独立抽取", "本研究采集 {n} 所大学公开发布的",
        "published AI use policies of {n} universities", "{n} 所大学 × 12 项条款的编码矩阵",
        "A coding matrix of {n} universities", "{n} 份来源文件由 {n} 个相互隔离的程序分别抽取",
        "The {n} source files were read by {n} isolated passes", "{n} pages")
    add("规范依据校数", core["schools"], "并以其中美国 {n} 所的", "the comparison of the {n} U.S. universities",
        "依据图谱中美国 {n} 所大学的比较结果制定", "the atlas's comparison of the {n} U.S. universities",
        "{n} 校政策基本未涉及", "01–{n} 为美国 {n} 所大学", "01–{n} are the {n} U.S. universities")
    add("条款数", m["dimensions"], "<b>{n}</b><span lang=\"zh\">项比较条款", "按 {n} 项条款逐校编码比较",
        "codes each against {n}")
    add("格数", m["cells"], "<b>{n}</b><span lang=\"zh\">个编码单元（" + grid + "）",
        "coded cells (" + grid + ")")
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

    # the admissions door
    a = adm.load()
    n_adm = len(a["by_id"])
    explicit = sum(1 for s in a["by_id"].values() if s["status"] == "explicit-undergraduate-ai")
    add("申请·学校数", n_adm, "{n} 所 · 以本科为主", "{n} · undergraduate first", "{n} 所大学招生办公室与申请平台",
        "What the admissions offices of {n} universities")
    add("申请·明文边界", explicit, f"{n_adm} 所中有 {{n}} 所对本科申请人写明了 AI 使用边界",
        f"{{n}} of the {n_adm} state explicit lines for undergraduate applicants")
    return C


def admissions_bar():
    """One segment per evidence status, sized by its number of schools."""
    a = adm.load()
    out = []
    for st in adm.STATUS_ORDER:
        n = sum(1 for s in a["by_id"].values() if s["status"] == st)
        if n:
            zh, en = adm.status_short(st)
            out.append(f'<span style="flex:{n}" title="{html.escape(zh)} / {html.escape(en)}：{n}">{n}</span>')
    return "".join(out)


def school_index():
    """One entry per university, linking to its page, with its row of the atlas as a
    strip and, outside the U.S., its country or region."""
    d, _, _, _ = load_data()
    out = []
    for s in sorted(d["schools"], key=lambda s: s["num"]):
        sid = s["id"]
        _, en, zh, _ = reg.SCHOOLS[sid]
        strip = "".join(f'<i data-r="{c["rank"]}"></i>' for c in s["cells"])
        ctry = ""
        if sid in reg.COUNTRY:
            cz, ce = reg.COUNTRY[sid]
            ctry = (f'<span class="tags"><span class="ctry"><span lang="zh">{html.escape(cz)}</span>'
                    f'<span lang="en">{html.escape(ce)}</span></span></span>')
        out.append(
            f'<a class="sch" href="{reg.slug(sid)}/" title="{html.escape(en)}">'
            f'<span class="n">{s["num"]:02d}</span><b>{html.escape(s["short"])}</b>'
            f'<span class="zh">{html.escape(zh)}</span><span class="fp">{strip}</span>{ctry}</a>')
    return "\n".join(out)


def main():
    src = SRC.read_text(encoding="utf-8")
    if "<!--__SCHOOLS__-->" not in src:
        raise SystemExit("home.html 缺少 <!--__SCHOOLS__--> 标记")
    if "<!--__ADM_BAR__-->" not in src:
        raise SystemExit("home.html 缺少 <!--__ADM_BAR__--> 标记")
    src = (src.replace("<!--__SCHOOLS__-->", school_index())
              .replace("<!--__ADM_BAR__-->", admissions_bar())
              .replace("<!--__VERSION__-->", html.escape(version_log()[0]["v"])))
    publish(src, DST, checks(), label="主页")


if __name__ == "__main__":
    main()

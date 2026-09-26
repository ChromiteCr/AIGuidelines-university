#!/usr/bin/env python3
"""home/home.html -> docs/index.html

The site's front door. It carries no policy content of its own, only the
headline figures, the three doors and the school index, but those figures are
hand-written like the guidelines' are — so they go through the same check: each
is registered as the literal phrase it must appear as, filled in from
data/policies.json, the admissions index and the expansion index.

Usage:  python3 tools/build_home.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import html  # noqa: E402
import re  # noqa: E402

import admissions as adm  # noqa: E402
import build_guidelines as bg  # noqa: E402
import expansion as exp  # noqa: E402
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

    n_added = len(exp.load()["by_id"])
    n_all = len(reg.SCHOOLS)
    if n_all != m["schools"] + n_added:
        raise SystemExit(f"学校总数 {n_all} ≠ 编码 {m['schools']} + 补充 {n_added}")
    add("全站校数", n_all, "<title>{n} 所大学 AI 使用政策比较研究</title>",
        "<h1 lang=\"zh\">{n} 所大学 AI 使用政策比较研究</h1>", "AI Use Policies at {n} Universities: A Comparative Study",
        "<b>{n}</b><span lang=\"zh\">所大学的校内规范与申请规定", "本研究采集 {n} 所大学公开发布的",
        "This study collects the published AI rules of {n} universities", "{n} 所均整理了", "For all {n},",
        "{n} pages")
    add("编码校数", m["schools"], "<b>{n}</b><span lang=\"zh\">所按 12 项条款逐校编码",
        "其中美国 {n} 所大学的校内政策按 12 项条款逐校编码比较", "The campus policies of {n} U.S. universities",
        "美国 {n} 所大学 × 12 项条款", "{n} U.S. universities × 12 provisions", "{n} 校政策基本未涉及",
        "{n} 所大学的校内政策采集于", "The campus policies of the {n}")
    add("补充校数", n_added, "其余 {n} 所收录校内规范的原文摘录", "for the other {n},", "表中另列补充的 {n} 所",
        "The {n} added universities are listed too", "标「未编码」的 {n} 所", "The {n} marked",
        "这 {n} 所只收录", "For these {n} only", "申请环节资料与补充的 {n} 所", "the {n} added universities")
    nums = sorted(int(sid[:2]) for sid in exp.load()["by_id"])
    add("补充编号", nums[0], f"的 {n_added} 所（{{n}}–{nums[-1]}）", f"The {n_added} marked \"not coded\" ({{n}}–{nums[-1]})")
    add("条款数", m["dimensions"], "所按 {n} 项条款逐校编码", "按 {n} 项条款逐校编码比较",
        "coded against {n} provisions and compared")
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
    """Every university in number order, linking to its page. A coded one shows its
    row of the atlas as a strip; an added one says it is not coded."""
    d, _, _, _ = load_data()
    coded = {s["id"]: s for s in d["schools"]}
    out = []
    for sid in sorted(reg.SCHOOLS):
        _, en, zh, _ = reg.SCHOOLS[sid]
        if sid in coded:
            s = coded[sid]
            short = s["short"]
            strip = "".join(f'<i data-r="{c["rank"]}"></i>' for c in s["cells"])
            extra = f'<span class="fp">{strip}</span>'
        else:
            short = reg.SHORT[sid]
            tags = '<span class="nc"><span lang="zh">未编码</span><span lang="en">NOT CODED</span></span>'
            if sid in reg.COUNTRY:
                cz, ce = reg.COUNTRY[sid]
                tags += (f'<span class="ctry"><span lang="zh">{html.escape(cz)}</span>'
                         f'<span lang="en">{html.escape(ce)}</span></span>')
            extra = f'<span class="tags">{tags}</span>'
        out.append(
            f'<a class="sch" href="{reg.slug(sid)}/" title="{html.escape(en)}">'
            f'<span class="n">{sid[:2]}</span><b>{html.escape(short)}</b>'
            f'<span class="zh">{html.escape(zh)}</span>{extra}</a>')
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

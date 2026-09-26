#!/usr/bin/env python3
"""README.md version table -> docs/versions.html

The versions page: every version with its date, type and what changed, grouped
by research stage (A1, A2, …), and the size of the research as it stands. The
version record lives in one place, the table under "## 版本记录" in README.md,
which sitelib.version_log() reads and checks (format, newest-first order, badge
in step with the newest row). Nothing about a version is written here.

Usage:  python3 tools/build_versions.py
"""

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import admissions as adm  # noqa: E402
import schools as reg  # noqa: E402
from build_schools import Balance  # noqa: E402
from sitelib import ROOT, join_cjk, load_data, version_log, wrap_document  # noqa: E402

TPL = ROOT / "home" / "versions.template.html"
DST = ROOT / "docs" / "versions.html"
E = html.escape

TYPES = {"milestone": ("里程碑", "Milestone"), "feat": ("新功能", "Feature"),
         "fix": ("修复", "Fix"), "docs": ("文档", "Docs")}


def bi(zh, en):
    return f'<span lang="zh">{zh}</span><span lang="en">{en}</span>'


def inline(text):
    """A version note: plain text with `code` spans, as written in the README table."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", E(text, quote=False))


def title(text):
    """A stage's name: the milestone note up to its first colon (or first clause)."""
    for sep in ("：", "，", "；"):
        head = text.split(sep, 1)[0]
        if len(head) < len(text) and len(head) <= 40:
            return head
    return text


def stage_of(v):
    return int(re.match(r"A(\d+)", v).group(1))


def main():
    rows = version_log()
    for r in rows:
        if r["type"] not in TYPES:
            raise SystemExit(f"版本记录：{r['v']} 的类型 {r['type']!r} 不在 {sorted(TYPES)} 之中")
    stages = {}
    for r in rows:
        stages.setdefault(stage_of(r["v"]), []).append(r)
    for n, rs in stages.items():
        heads = [r for r in rs if r["v"] == f"A{n}"]
        if not heads or heads[0]["type"] != "milestone":
            raise SystemExit(f"阶段 A{n} 缺少类型为 milestone 的 A{n} 一行")
    current = rows[0]
    order = sorted(stages)                       # oldest first, for the stage strip

    # ---- the research as it stands ------------------------------------------------
    d = load_data()[0]
    m = d["meta"]
    facts = [
        (len(reg.SCHOOLS), "所大学", "universities"),
        (m["schools"], "所按 12 项条款逐校编码", "coded against 12 provisions"),
        (m["cells"], f"个编码单元（{m['schools']} × {m['dimensions']}）", f"coded cells ({m['schools']} × {m['dimensions']})"),
        (m["evidence_matched"], "条原文引证，逐字核验", "quotations, verified verbatim"),
        (len(adm.load()["by_id"]), "份申请环节档案", "admissions records"),
        (len(rows), "个版本", "versions"),
    ]
    facts_html = "".join(f'<div class="fact"><b>{n}</b>{bi(E(zh), E(en))}</div>' for n, zh, en in facts)

    # ---- stages, oldest first ------------------------------------------------------
    cards = []
    for n in order:
        rs = stages[n]
        head = next(r for r in rs if r["v"] == f"A{n}")
        dates = sorted(r["date"] for r in rs)
        when = dates[0] if dates[0] == dates[-1] else f"{dates[0]} – {dates[-1]}"
        now = " now" if n == stage_of(current["v"]) else ""
        cards.append(
            f'<li class="stage{now}"><a href="#A{n}">'
            f'<span class="code">A{n}</span><span class="when">{E(when)}</span>'
            f'<span class="title">{inline(title(head["text"]))}</span>'
            f'<span class="count">{bi(f"{len(rs)} 个版本", f"{len(rs)} version" + ("s" if len(rs) > 1 else ""))}</span>'
            f'</a></li>')

    # ---- the log, newest stage first -----------------------------------------------
    blocks = []
    for n in reversed(order):
        rs = stages[n]
        head = next(r for r in rs if r["v"] == f"A{n}")
        entries = "".join(
            f'<li class="entry"><span class="v">{E(r["v"])}</span><span class="d">{E(r["date"])}</span>'
            f'<span class="t" data-k="{E(r["type"])}">{bi(*TYPES[r["type"]])}</span>'
            f'<p>{inline(r["text"])}</p></li>'
            for r in rs)
        blocks.append(f'<div class="phase" id="A{n}"><h3 class="phase-h"><b>A{n}</b>'
                      f'<span>{inline(title(head["text"]))}</span><i>{E(head["date"])}</i></h3>'
                      f'<ol class="log">{entries}</ol></div>')

    cname_file = ROOT / "docs" / "CNAME"
    cname = cname_file.read_text(encoding="utf-8").strip() if cname_file.exists() else ""
    canonical = f'<link rel="canonical" href="https://{cname}/versions.html">' if cname else ""

    tpl = TPL.read_text(encoding="utf-8")
    for marker in ("<!--__FACTS__-->", "<!--__STAGES__-->", "<!--__LOG__-->"):
        if marker not in tpl:
            raise SystemExit(f"versions.template.html 缺少 {marker} 标记")
    # The CJK line-break fix runs on the template only, never on injected text.
    page = (join_cjk(tpl)
            .replace("__CANONICAL__", canonical)
            .replace("__CURRENT_DATE__", E(current["date"]))
            .replace("__CURRENT_STAGE__", f"A{stage_of(current['v'])}")
            .replace("__CURRENT__", E(current["v"]))
            .replace("__NSTAGES__", str(len(order)))
            .replace("__NVERSIONS__", str(len(rows)))
            .replace("<!--__FACTS__-->", facts_html)
            .replace("<!--__STAGES__-->", "".join(cards))
            .replace("<!--__LOG__-->", "\n".join(blocks)))

    bal = Balance()
    bal.feed(page)
    bal.close()
    if bal.errors or bal.stack:
        sys.exit(f"versions.html: HTML 嵌套错误 {bal.errors[:3]} 未闭合 {bal.stack[-3:]}")
    DST.write_text(wrap_document(page), encoding="utf-8")
    print(f"版本与进展 {len(rows)} 个版本、{len(order)} 个阶段 → docs/versions.html（当前 {current['v']}，{current['date']}）")


if __name__ == "__main__":
    main()

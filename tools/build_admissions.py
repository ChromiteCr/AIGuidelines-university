#!/usr/bin/env python3
"""admissions/ -> docs/admissions.html

The overview of application-stage AI guidance: one row per university with its
evidence status, the collector's summary and a link to the full record on that
university's page (built by build_schools.py), then the shared platform sources
(Common App, the UC system) and the method.

Counts and statuses come from admissions/application-index.json; the few figures
the page states in prose are checked against it, as on the other pages.

Usage:  python3 tools/build_admissions.py
"""

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import admissions as adm  # noqa: E402
import schools as reg  # noqa: E402
from build_schools import KV_ZH, Balance, bi  # noqa: E402
from sitelib import ROOT, assertion_builder, flat, join_cjk, load_data, wrap_document  # noqa: E402

TPL = ROOT / "schools" / "admissions.template.html"
DST = ROOT / "docs" / "admissions.html"
E = html.escape

# What each status means, in terms of what was found — never how strict a rule is.
STATUS_DEF = {
    "explicit-undergraduate-ai": (
        "对本科申请人使用 AI 写明了边界：哪些用途允许、哪些禁止，或违反的后果。效力以来源的性质为准。",
        "States in writing where the lines are for undergraduate applicants: which uses are allowed, which are not, "
        "or what follows a breach. Its force depends on the kind of source."),
    "uc-system-ai-guidance": (
        "依据 UC 系统的共同来源（申请诚信声明与申请指南），不是该校区单独发布的政策。",
        "Rests on the UC system's shared sources (the Statement of Application Integrity and the application guide), "
        "not on a policy issued by the campus."),
    "undergraduate-advice-ai": (
        "官方渠道对申请中使用 AI 给出指导或劝告，但没有写成明确的许可或禁止边界。",
        "An official channel gives guidance or advice on using AI in the application, without stating firm lines."),
    "authenticity-only": (
        "有本人写作或真实性要求，但未核实到针对 AI 的具体边界；不能据此推出任何 AI 用途被允许或禁止。",
        "Own-work or authenticity requirements exist, but no AI-specific lines were verified; no AI use can be "
        "inferred from them to be allowed or forbidden."),
    "graduate-only-ai": (
        "已核实的 AI 明文只适用于研究生或特定项目，不外推到本科申请。",
        "The explicit AI rules verified apply only to graduate or specific programmes and are not extended to "
        "undergraduate applications."),
    "no-verified-guidance": (
        "未取得可核实的适用指导。",
        "No verifiable applicable guidance was obtained."),
}


def kv_label(key):
    return bi(E(KV_ZH.get(key, key)), E(key))


def main():
    d = adm.load()
    schools = sorted(d["by_id"].items(), key=lambda kv: kv[0])
    short = {s["id"]: s["short"] for s in load_data()[0]["schools"]}   # the names the atlas uses
    counts = {st: sum(1 for _, s in schools if s["status"] == st) for st in adm.STATUS_ORDER}
    present = [st for st in adm.STATUS_ORDER if counts[st]]
    uc = counts["uc-system-ai-guidance"]

    # ---- figures stated in prose ----------------------------------------------
    tpl = TPL.read_text(encoding="utf-8")
    checks = []
    add = assertion_builder(checks)
    add("学校数", len(schools), "美国 {n} 所大学", "{n} U.S. universities", "<h2 lang=\"zh\">{n} 所大学</h2>")
    add("UC 校区数", uc, "UC 的 {n} 所校区共用同一系统来源", "不计为 {n} 份独立政策",
        "the {n} UC campuses share one system source", "not counted as {n} independent policies")
    hay = flat(tpl)
    bad = [(lab, val, needle) for lab, val, needle in checks if needle not in hay]
    print(f"申请汇总 数字核对   {len(checks) - len(bad)}/{len(checks)} 处断言与 application-index.json 一致")
    for lab, val, needle in bad:
        print(f"  ! {lab}：数据是 {val}，文中找不到 {needle!r}")
    if bad:
        sys.exit("\n构建中止：文中的数字与申请资料索引对不上。")

    # ---- status filters ---------------------------------------------------------
    stats = []
    for st in present:
        zh, en = adm.status_short(st)
        stats.append(f'<button class="stat" type="button" data-s="{st}" aria-pressed="false">'
                     f'<b>{counts[st]}</b>{bi(E(zh), E(en))}</button>')

    # ---- one row per university ---------------------------------------------------
    rows = []
    for sid, s in schools:
        num = sid[:2]
        slug = reg.slug(sid)
        _, en_name, zh_name, _ = reg.SCHOOLS[sid]
        zh, en = adm.status_short(s["status"])
        n_src = sum(1 for x in s["sources"] if x.get("retrieval") != "blocked")
        n_q = sum(len(x.get("quotes") or []) for x in s["sources"])
        rows.append(
            f'<tr data-s="{s["status"]}">'
            f'<td class="n">{num}</td>'
            f'<td class="sch"><a href="{slug}/#admissions" title="{E(en_name)}"><b>{E(short[sid])}</b>'
            f'<span>{E(zh_name)}</span></a></td>'
            f'<td class="st"><span class="schip">{bi(E(zh), E(en))}</span></td>'
            f'<td class="sum">{E(s["summary_zh"])}</td>'
            f'<td class="src">{bi(f"来源 <b>{n_src}</b><br>引文 <b>{n_q}</b>", f"<b>{n_src}</b> sources<br><b>{n_q}</b> quotes")}</td>'
            f'</tr>')

    # ---- definitions -----------------------------------------------------------------
    defs = []
    for st in present:
        zh_def, en_def = STATUS_DEF[st]
        defs.append(f'<dt><span class="schip">{bi(E(adm.status_short(st)[0]), E(adm.status_short(st)[1]))}</span></dt>'
                    f'<dd>{bi(E(zh_def), E(en_def))}</dd>')

    # ---- shared platform sources -------------------------------------------------------
    p_front, p_body = adm.render(adm.PLATFORMS, "", None, kv_label)

    cname_file = ROOT / "docs" / "CNAME"
    cname = cname_file.read_text(encoding="utf-8").strip() if cname_file.exists() else ""
    canonical = f'<link rel="canonical" href="https://{cname}/admissions.html">' if cname else ""

    # The CJK line-break fix runs on the template only, never on injected text.
    page = (join_cjk(tpl)
            .replace("__CANONICAL__", canonical)
            .replace("__NSTATS__", str(len(present)))
            .replace("<!--__STATS__-->", "".join(stats))
            .replace("<!--__ROWS__-->", "\n".join(rows))
            .replace("<!--__DEFS__-->", "".join(defs))
            .replace("<!--__PLATFORMS_ABOUT__-->", p_front)
            .replace("<!--__PLATFORMS__-->", p_body))

    bal = Balance()
    bal.feed(page)
    bal.close()
    if bal.errors or bal.stack:
        sys.exit(f"admissions.html: HTML 嵌套错误 {bal.errors[:3]} 未闭合 {bal.stack[-3:]}")

    DST.write_text(wrap_document(page), encoding="utf-8")
    summary = "，".join(f"{adm.status_short(st)[0]} {counts[st]}" for st in present)
    print(f"申请汇总   {len(schools)} 所 → docs/admissions.html（{summary}）")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""One page per university:  docs/<slug>/index.html  →  ai.policy.nestudy.cn/<slug>

Each page is that university's AI rules on their own: its twelve provisions as
coded in the atlas, each with the sentence it rests on and where that position
sits among the thirty; what its admissions office says about applicants using
AI (from admissions/, see tools/admissions.py); and the full official text
collected for it — with every cited sentence highlighted in place and tagged
with the provision it supports.

Where univ/full/<file> exists, the page shows that complete text instead of the
research copy in univ/, with the parts the research copy leaves out set in small
grey type (currently MIT only; see unresearched()).

Also writes docs/404.html, which GitHub Pages serves for any missing path. It
redirects recognised variants (/mit, /Mit, /johns-hopkins, /麻省理工, /02) to
the canonical page, and otherwise lists all thirty.

Checks, all fatal:
  - every cited sentence is found in its source file and gets an anchor and a tag
  - a research copy differs from its full text only by removed passages
  - every page's HTML nests correctly
  - aliases never collide with each other or with an existing top-level page

Usage:  python3 tools/build_schools.py
"""

import difflib
import html
import html.parser
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import admissions as adm  # noqa: E402
import mdlite  # noqa: E402
import schools as reg  # noqa: E402
from sitelib import ROOT, load_data, wrap_document  # noqa: E402

TPL = ROOT / "schools" / "school.template.html"
DOCS = ROOT / "docs"
ADMISSIONS = adm.ADM               # admissions/<id>.md, rendered when present
FULL = ROOT / "univ" / "full"      # complete text, where the research copy was trimmed

E = html.escape

EN_QUESTION = {
    "default_rule": "When an assignment says nothing about AI, what applies?",
    "instructor_override": "Does an instructor's rule take precedence over the institution's?",
    "tiered_scale": "Is there a graduated permission framework?",
    "disclosure": "Must AI use be disclosed, and is that required or recommended?",
    "process_evidence": "Must drafts, prompts or edit history be kept?",
    "verification_duty": "Who is responsible when AI output is wrong or a citation is invented?",
    "integrity_framing": "How is a violation classified in the disciplinary system?",
    "detector_stance": "Can AI-detection results be used as evidence?",
    "data_privacy": "What must not be entered into an AI tool?",
    "ip_copyright": "Does it regulate the use of copyrighted and others' material?",
    "institutional_tools": "Does the institution designate or provide AI tools?",
    "learning_rationale": "Are the rules grounded in not bypassing the skills to be learned?",
}
EN_HINT = {
    "permission": "who decides whether AI may be used",
    "transparency": "what must be declared after use",
    "accountability": "responsibility for errors and violations",
    "boundaries": "limits on data, copyright and tools",
    "rationale": "the stated basis for the rules",
}
SCOPE_EN_HINT = {
    "university_wide": "a central or provost-level policy that applies to all students",
    "unit_or_school": "applies to one school, programme or department only",
    "instructor_facing": "a teaching-centre resource that guides instructors rather than binding students",
    "mixed": "the file combines a university-wide source with a narrower one",
}
KV_ZH = {
    "Accessed": "访问日期", "Format note": "格式说明", "Scope note": "适用范围", "Use note": "用途说明",
    "Official source": "官方来源", "Additional official source": "补充官方来源",
    "Publishing unit": "发布单位", "Issuing body": "发布机构", "Issuer": "发布方", "Domain": "域名",
    "Page date": "页面日期", "Page last updated": "页面更新", "Page note": "页面说明",
    "Effective": "生效", "Published": "发布", "Retrieval note": "采集说明", "Scope": "适用范围",
    **adm.KV_ZH,
}


def bi(zh, en, tag="span", cls=""):
    """Author a fragment twice; the page's language switch hides one."""
    c = f' class="{cls}"' if cls else ""
    return f'<{tag} lang="zh"{c}>{zh}</{tag}><{tag} lang="en"{c}>{en}</{tag}>'


def plain(md):
    """Evidence shown on a card: drop Markdown markup, keep every word, keep line breaks."""
    out = []
    for line in md.split("\n"):
        line = re.sub(r"^(#{1,6}\s+|[-*]\s+|\d+\.\s+|>\s?)", "", line.strip()).replace("**", "")
        if line:
            out.append(f"<span>{E(line)}</span>")
    return "".join(out)


def unresearched(research, full):
    """Character ranges of `full` that the research copy leaves out.

    The research copy was made from the full text by removing whole paragraphs
    and sections and putting an omission marker in their place — nothing kept was
    reworded. A line alignment therefore recovers the removed parts exactly, and
    anything else in the research copy that the full text lacks is an error.
    """
    r_lines, f_lines = research.split("\n"), full.split("\n")
    starts = [0]
    for line in f_lines:
        starts.append(starts[-1] + len(line) + 1)
    ranges = []
    sm = difflib.SequenceMatcher(None, r_lines, f_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for line in r_lines[i1:i2]:
            if line.strip() not in ("", ">") and not re.search(r"omitted|略去", line):
                raise SystemExit(f"研究版中有一行不在完整原文里：{line[:70]!r}")
        if j2 > j1:
            ranges.append((starts[j1], starts[j2]))
    return ranges


def words(text):
    return len(re.findall(r"[A-Za-z’']+", text))


class Balance(html.parser.HTMLParser):
    VOID = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed",
            "source", "track", "wbr", "option"}

    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"</{tag}> 与 <{self.stack[-1] if self.stack else '∅'}> 不匹配")


# ---------------------------------------------------------------------------
def school_page(s, ctx):
    d, dm = ctx["data"], ctx["dm"]
    sid, slug = s["id"], reg.slug(s["id"])
    _, en_name, zh_name, _ = reg.SCHOOLS[sid]
    total = d["meta"]["schools"]
    raw = (ROOT / s["file"]).read_text(encoding="utf-8")

    # ---- the complete text, where the research copy was trimmed -------------
    full_path = FULL / Path(s["file"]).name
    dim_ranges = []
    if full_path.exists():
        research, raw = raw, full_path.read_text(encoding="utf-8")
        dim_ranges = unresearched(research, raw)

    def outside_dim(a, b):
        return not any(x < b and a < y for x, y in dim_ranges)

    def locate(needle):
        """First occurrence in the raw file that is not in an uncited passage."""
        i = raw.find(needle)
        while i >= 0 and not outside_dim(i, i + len(needle)):
            i = raw.find(needle, i + 1)
        return i

    # ---- locate every cited sentence in the raw file ----------------------
    spans, missing = [], []
    for c in s["cells"]:
        if c["evidence"]:
            i = locate(c["evidence"])
            if i < 0:
                missing.append(c["dim"])
            else:
                spans.append((i, i + len(c["evidence"]), c["dim"]))
    if s["quote"]["text"]:
        i = locate(s["quote"]["text"])
        if i < 0:
            missing.append("quote")
        else:
            spans.append((i, i + len(s["quote"]["text"]), "quote"))
    if missing:
        raise SystemExit(f"{sid}: 引文在原文中找不到 {missing}")

    dim_meta = {x["key"]: x for x in d["dimensions"]}

    def tag_html(label):
        if label == "quote":
            return (f'<sup class="evtag"><a href="#quote" data-ev="quote">'
                    f'{bi("摘录", "Excerpt")}</a></sup>')
        x = dim_meta[label]
        return (f'<sup class="evtag"><a href="#p-{label}" data-ev="{label}" '
                f'title="{E(x["zh"])} / {E(x["en"])}">{bi(E(x["zh"]), E(x["en"]))}</a></sup>')

    def kv_label(key):
        return bi(E(KV_ZH.get(key, key)), E(key))

    def omission(n, further):
        if further:
            return f'<p class="omit">{bi(f"本节另有 {n} 词未被本项目引用，已略去。", f"{n} further words omitted — not cited by this project.")}</p>'
        return (f'<p class="omit">{bi(f"本节共 {n} 词，未被本项目引用，已略去；全文见官方来源。", f"{n} words omitted here — not cited by this project; see the official source.")}</p>')

    title, front, rest = mdlite.split_front(mdlite.parse(raw))
    # Passages the research copy leaves out are set apart, block by block. The
    # research copy removed whole paragraphs, so a block is either entirely
    # inside a removed passage or entirely outside all of them.
    dim_words = 0
    for b in rest:
        span = mdlite.block_span(b)
        if not span or not dim_ranges:
            continue
        if any(x <= span[0] and span[1] <= y for x, y in dim_ranges):
            b["dim"] = True
            dim_words += words(raw[span[0]:span[1]])
        elif not outside_dim(*span):
            raise SystemExit(f"{sid}: 有一段文字跨越了引用与未引用部分的边界（偏移 {span}）")
    r = mdlite.Renderer(raw, spans, tag_html, lambda l: f"ev-{l}", kv_label, omission,
                        dim_html='<div class="uncited">')
    tk = (f'<p class="tk-label">{bi("以下为整理者所写的高中适用要点，非该校原文，不作为任何条款的依据。", "Below: the collector’s notes on application to high school — not the university’s text, and not used as evidence for any provision.")}</p>')
    front_html, body_html = r.render_all(front, rest, tk)
    no_anchor, no_tag = r.missing()
    if no_anchor or no_tag:
        raise SystemExit(f"{sid}: 引文未能在原文中标出 anchor={no_anchor} tag={no_tag}")

    accessed = next((it["segs"][0][1].split(":", 1)[1].strip() for it in front
                     if it["segs"][0][1].startswith("Accessed:")), d["meta"]["accessed"])

    # ---- masthead -----------------------------------------------------------
    covered = s["covered"]
    scope = d["scopes"][s["scope"]]
    strip = []
    for c in s["cells"]:
        x = dim_meta[c["dim"]]
        strip.append(
            f'<a class="sc" data-r="{c["rank"]}" href="#p-{c["dim"]}" title="{E(x["zh"])}：{E(c["zh"])}">'
            f'<em>{bi(E(x["zh"]), E(x["en"]))}</em><b>{bi(E(c["zh"]), E(c["en"]))}</b></a>')
    cname = ctx["cname"]
    entry = ctx["adm"]["by_id"].get(sid)
    adm_file = ADMISSIONS / Path(s["file"]).name
    adm_chip = ""
    if entry and adm_file.exists():
        sz, se = adm.status_short(entry["status"])
        adm_chip = (f'<a class="chip adm-chip" href="#admissions">'
                    f'{bi(f"申请环节 · <b>{E(sz)}</b>", f"Admissions · <b>{E(se)}</b>")}</a>')
    mast = f'''<header class="mast"><div class="wrap">
  {bi(f"No.{s['num']:02d} / {total} · 美国 {total} 所大学 AI 使用政策比较研究", f"No.{s['num']:02d} of {total} · AI Use Policies at {total} U.S. Universities", cls="eyebrow")}
  <h1>{E(s["short"])}</h1>
  <p class="fullname"><span>{E(en_name)}</span><span class="zh">{E(zh_name)}</span></p>
  <div class="chips">
    <span class="chip" title="{E(scope["hint"])}">{bi(f"来源层级 · <b>{E(scope['zh'])}</b>", f"Source level · <b>{E(scope['en'])}</b>")}</span>
    <span class="chip">{bi(f"<b>{covered}</b> / 12 项有明文规定", f"<b>{covered}</b> of 12 provisions addressed")}</span>
    <span class="chip">{bi(f"采集于 <b>{E(accessed)}</b>", f"Accessed <b>{E(accessed)}</b>")}</span>
    {adm_chip}
  </div>
  <nav class="strip" aria-label="十二项条款 / Twelve provisions">{"".join(strip)}</nav>
  <p class="print-url">{E(cname or "")}/{slug}</p>
</div></header>'''

    # ---- pull quote ---------------------------------------------------------
    quote = ""
    if s["quote"]["text"]:
        quote = f'''<section id="quote">
  <div class="sec-head"><h2>{bi("原文摘录", "Excerpt")}</h2></div>
  <p class="sec-sub">{bi("选取标准：对高中读者最具引用价值的一句原文。", "Selected as the sentence most quotable for a high-school reader.")}</p>
  <blockquote class="pull"><p>{E(s["quote"]["text"].replace("**", ""))}</p>
    <a href="#ev-quote">{bi("↓ 在原文中的位置", "↓ Where it appears in the source")}</a></blockquote>
</section>'''

    # ---- provisions ---------------------------------------------------------
    cell = {c["dim"]: c for c in s["cells"]}
    groups = []
    for g in d["groups"]:
        cards = []
        for x in [x for x in d["dimensions"] if x["group"] == g["key"]]:
            c = cell[x["key"]]
            dist = {v["value"]: v for v in x["dist"]}
            same = dist[c["value"]]["n"]
            top = dist.get(x["top_value"]) if x["top_value"] else None
            head = f'''<div class="card-l">
      <h3>{bi(E(x["zh"]), E(x["en"]))}</h3>
      <span class="en">{bi(E(x["en"]), E(x["zh"]))}</span>
      <p>{bi(E(x["question"]), E(EN_QUESTION[x["key"]]))}</p>
    </div>'''
            atlas_link = (f'<a href="../atlas.html#{slug}/{x["key"]}">'
                          f'{bi("在图谱中与其他学校对照 ↗", "Compare with the others in the atlas ↗")}</a>')
            if c["rank"] == 0:
                cards.append(f'''<article class="card silent" id="p-{x["key"]}">
    {head}
    <div class="card-r">
      <div class="verdict"><span class="vchip" data-r="0">{bi("未作表述", "Not addressed")}</span></div>
      <p class="silent-note">{bi("本项目采集的官方来源未就此条款作出表述；这不代表该校没有相关规定。", "The official source collected here does not address this provision; this does not mean the university has no rule on it.")}</p>
      <p class="ctx">{bi(f"{total} 校中 <b>{same}</b> 所同样未作表述", f"<b>{same}</b> of {total} are likewise silent")}</p>
      <div class="links">{atlas_link}</div>
    </div>
  </article>''')
                continue
            is_top = top and c["value"] == x["top_value"] and not x.get("binary")
            main_tag = f'<span class="tag-main">{bi("主流口径", "MOST COMMON")}</span>' if is_top else ""
            top_txt_zh = f"该条主流口径：{E(top['zh'])}（{top['n']}/{x['covered']}）" if top else ""
            top_txt_en = f"most common: {E(top['en'])} ({top['n']}/{x['covered']})" if top else ""
            note = (f'<p class="note"><span class="k">{bi("编码说明", "CODING NOTE")}</span>{E(c["note"])}</p>'
                    if c["note"] else "")
            cards.append(f'''<article class="card" id="p-{x["key"]}">
    {head}
    <div class="card-r">
      <div class="verdict"><span class="vchip" data-r="{c["rank"]}">{bi(E(c["zh"]), E(c["en"]))}</span>{main_tag}</div>
      <blockquote class="ev">{plain(c["evidence"])}</blockquote>
      {note}
      <p class="ctx">{bi(f"{total} 校中 <b>{same}</b> 所与此相同 · {top_txt_zh}", f"<b>{same}</b> of {total} take this position · {top_txt_en}")}</p>
      <div class="links"><a href="#ev-{x["key"]}">{bi("↓ 在原文中的位置", "↓ Where it appears in the source")}</a>{atlas_link}</div>
    </div>
  </article>''')
        groups.append(f'''<div class="group">
  <div class="group-h"><b>{bi(E(g["zh"]), E(g["en"]))}</b><span>{bi(E(g["hint"]), E(EN_HINT[g["key"]]))}</span></div>
  <div class="cards">{"".join(cards)}</div>
</div>''')
    provisions = f'''<section id="provisions">
  <div class="sec-head"><h2>{bi("十二项条款", "The twelve provisions")}</h2><span class="en2">{covered} / 12</span></div>
  <p class="sec-sub">{bi(f"每项附该校原文中的依据语句，以及 {total} 校中持同一立场的校数。颜色越深，规定越明确、越具约束力（不代表优劣）；斜纹表示该来源未作表述。", f"Each provision gives the supporting sentence and how many of the {total} take the same position. Darker means more explicit and binding (not better); hatching means the source does not address it.")}</p>
  {"".join(groups)}
</section>'''

    # ---- details ------------------------------------------------------------
    extras = []
    if s["tiers"]:
        lis = "".join(f"<li>{E(t.replace('**', ''))}</li>" for t in s["tiers"])
        extras.append(f'<div class="extra"><h3>{bi("该校的分级框架", "Its permission levels")}</h3><ol>{lis}</ol></div>')
    if s["disclose"]:
        tags = "".join(f'<span class="chip">{bi(E(d["disclose_items"][k]["zh"]), E(d["disclose_items"][k]["en"]))}</span>'
                       for k in s["disclose"])
        extras.append(f'<div class="extra"><h3>{bi("要求披露的内容", "What must be disclosed")}</h3><div class="tags">{tags}</div></div>')
    details = (f'''<section id="details">
  <div class="sec-head"><h2>{bi("补充信息", "Further detail")}</h2></div>
  <div class="extras">{"".join(extras)}</div>
</section>''' if extras else "")

    # ---- source text --------------------------------------------------------
    verdict = d["verdicts"].get(s["audit"]["verdict"], {"zh": s["audit"]["verdict"], "en": s["audit"]["verdict"]})
    n_fix = len(s["audit"]["changes"])
    audit_zh = f"{E(verdict['zh'])}（审计员修正 {n_fix} 处）" if n_fix else "审计通过，无需修正"
    audit_en = f"{E(verdict['en'])} ({n_fix} corrections by the auditor)" if n_fix else "Clean — no corrections needed"
    rows = [
        f'<li><span class="k">{bi("来源层级", "Source level")}</span><span class="v">'
        f'{bi(f"{E(scope['zh'])} —— {E(scope['hint'])}", f"{E(scope['en'])} — {E(SCOPE_EN_HINT[s['scope']])}")}</span></li>',
        f'<li><span class="k">{bi("抽取审计", "Extraction audit")}</span><span class="v">{bi(audit_zh, audit_en)}</span></li>',
    ]
    for src in s["sources"]:
        unit = f"{E(src['unit'])}<br>" if src.get("unit") else ""
        rows.append(f'<li><span class="k">{bi("官方来源", "Official source")}</span><span class="v">{unit}'
                    f'<a href="{E(src["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{E(src["url"])}</a></span></li>')
    admissions = ""
    if adm_chip:
        afront_html, abody_html = adm.render(adm_file, "../", sid, kv_label)
        full_zh = ctx["adm"]["status_labels"][entry["status"]]
        full_en = adm.STATUS_TEXT[entry["status"]][2]
        admissions = f'''<section id="admissions">
  <div class="sec-head"><h2>{bi("申请环节的 AI 政策", "AI in the application")}</h2><span class="en2">admissions/{E(adm_file.name)}</span></div>
  <p class="sec-sub">{bi("该校招生办公室就申请人使用 AI 的公开表述，以本科新生申请为主。英文为逐字原文，中文为整理者的分析。证据状态描述找到了什么材料，不是宽严等级；未说明不代表允许。", "What this university's admissions office says about applicants using AI, chiefly for first-year undergraduate applications. English passages are verbatim; the Chinese is the collector's analysis. The evidence status describes what material was found, not how strict the rules are; silence does not mean permission.")}</p>
  <div class="adm-head">
    <span class="adm-k">{bi("证据状态", "Evidence status")}</span>
    <span class="adm-status">{bi(E(full_zh), E(full_en))}</span>
    <p class="adm-sum">{E(entry["summary_zh"])}</p>
    <a class="adm-all" href="../admissions.html">{bi("30 所大学对照 →", "All thirty compared →")}</a>
  </div>
  <div class="about"><h3>{bi("来源信息", "Source information")}</h3>{afront_html}</div>
  <div class="source adm">{abody_html}</div>
</section>'''

    uncited_note = ""
    if dim_words:
        uncited_note = bi(f"灰色小字为其余原文（约 {dim_words:,} 词），未被本项目引用，仅供参考。",
                          f" Text in small grey type (about {dim_words:,} words) is the rest of the collected text; it is not cited by this project and is shown for reference.")
    source = f'''<section id="source">
  <div class="sec-head"><h2>{bi("官方原文", "The official text")}</h2><span class="en2">{E(s["file"])}</span></div>
  <p class="sec-sub">{bi("本项目采集的该校官方文本。图谱引用的语句已高亮，句末标签注明对应条款，点击可返回该条款。", "The official text collected for this university. Sentences the atlas cites are highlighted; the tag after each names the provision it supports and links back to it.")}{uncited_note}</p>
  <div class="about">
    <h3>{bi("来源信息", "Source information")}</h3>
    <ul class="kv">{"".join(rows)}</ul>
    {front_html}
  </div>
  <div class="source">{body_html}</div>
</section>'''

    # ---- pager + footer -----------------------------------------------------
    order = ctx["order"]
    k = order.index(sid)
    pager = []
    if k > 0:
        p = ctx["by_id"][order[k - 1]]
        pager.append(f'<a class="prev" href="../{reg.slug(p["id"])}/"><span>← No.{p["num"]:02d}</span><b>{E(p["short"])}</b></a>')
    if k < len(order) - 1:
        n = ctx["by_id"][order[k + 1]]
        pager.append(f'<a class="next" href="../{reg.slug(n["id"])}/"><span>No.{n["num"]:02d} →</span><b>{E(n["short"])}</b></a>')

    footer = f'''<footer><div class="wrap">
  <p>{bi("<strong>内容取自官方原文；这是一份会定期更新的快照。</strong>所引文字逐字摘自该校官方发布的网页，版权归该校所有，为学术研究与评述目的引用。对政策的分类与强度分级是本项目的判断，不代表该校立场。采集之后该校若修订政策，本页不会自动跟进，正式采用前请回官网核实当前版本。",
                 "<strong>Official source text, kept as a periodically refreshed snapshot.</strong> Quotations are reproduced verbatim from the university’s own published pages; copyright remains with it and the material is used for academic research and commentary. The classification and strength grading are this project’s judgment, not the university’s position. Later revisions are not tracked automatically — verify against the official page before relying on it.")}</p>
  <p class="nav-links"><a href="../">{bi("主页", "Home")}</a> · <a href="../atlas.html">{bi("政策图谱", "Policy atlas")}</a> · <a href="../admissions.html">{bi("申请环节", "Admissions")}</a> · <a href="../guidelines.html">{bi("学生规范", "Student guidelines")}</a></p>
</div></footer>'''

    main = (f'{mast}\n<main class="wrap">\n{quote}\n{provisions}\n{details}\n{admissions}\n{source}\n'
            f'<nav class="pager">{"".join(pager)}</nav>\n</main>\n{footer}')

    # ---- assemble -----------------------------------------------------------
    switch = "\n".join(
        f'        <option value="{reg.slug(x["id"])}"{" selected" if x["id"] == sid else ""}>'
        f'{x["num"]:02d} · {E(x["short"])} · {E(reg.SCHOOLS[x["id"]][2])}</option>'
        for x in (ctx["by_id"][i] for i in order))
    canonical = f'<link rel="canonical" href="https://{cname}/{slug}/">' if cname else ""
    page = (ctx["tpl"]
            .replace("__TITLE__", E(f"{s['short']} · AI 使用政策"))
            .replace("__DESC__", E(f"{en_name}（{zh_name}）AI 使用政策：12 项条款的编码、依据原文与官方文本全文。"))
            .replace("__CANONICAL__", canonical)
            .replace("<!--__SWITCH__-->", switch)
            .replace("<!--__MAIN__-->", main))

    bal = Balance()
    bal.feed(page)
    bal.close()
    if bal.errors or bal.stack:
        raise SystemExit(f"{sid}: HTML 嵌套错误 {bal.errors[:3]} 未闭合 {bal.stack[-3:]}")
    for c in s["cells"]:
        if f'id="p-{c["dim"]}"' not in page:
            raise SystemExit(f"{sid}: 缺少条款锚点 p-{c['dim']}")
    return slug, page, len(spans), page.count("<mark")


# ---------------------------------------------------------------------------
NOT_FOUND = '''<title>页面不存在 · 404</title>
<meta name="robots" content="noindex">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Sans+SC:wght@400;500;700&family=Spectral:wght@600;700&display=swap">
<style>
:root{--paper:#E7E9EF;--surface:#FBFBFD;--ink:#131A2B;--ink-2:#414B61;--ink-3:#79839A;--rule:#D2D6E0;--seal-ink:#8A2B34}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#0B0F17;--surface:#141926;--ink:#E5E9F2;--ink-2:#AEB7CA;--ink-3:#727C95;--rule:#28303F;--seal-ink:#E9A3AA}}
:root[data-theme="dark"]{--paper:#0B0F17;--surface:#141926;--ink:#E5E9F2;--ink-2:#AEB7CA;--ink-3:#727C95;--rule:#28303F;--seal-ink:#E9A3AA}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans","Noto Sans SC",sans-serif;line-height:1.6}
.wrap{max-width:900px;margin:0 auto;padding:clamp(40px,8vw,90px) clamp(16px,5vw,44px) 60px}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.16em;color:var(--ink-3)}
h1{font-family:"Spectral","Noto Sans SC",serif;font-size:clamp(28px,5vw,44px);margin:8px 0 10px;line-height:1.15}
p{margin:0 0 16px;color:var(--ink-2);max-width:60ch}
.grid{display:grid;gap:1px;grid-template-columns:repeat(5,minmax(0,1fr));background:var(--rule);
  border:1px solid var(--rule);border-radius:3px;overflow:hidden;margin:22px 0}
.grid a{background:var(--surface);padding:10px 12px;text-decoration:none;color:var(--ink);
  display:grid;grid-template-columns:22px minmax(0,1fr);gap:1px 8px;align-items:baseline;align-content:start}
.grid a:hover{color:var(--seal-ink)}
.grid i{font-style:normal;font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--ink-3)}
.grid span{grid-column:2;font-size:12px;color:var(--ink-3)}
a{color:var(--seal-ink)}
@media (max-width:860px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:520px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
<main class="wrap">
  <p class="eyebrow">404</p>
  <h1 id="h">正在跳转…</h1>
  <p id="msg"></p>
  <div class="grid" id="list"></div>
  <p id="links"></p>
</main>
<noscript><p style="padding:0 20px">页面不存在。Page not found.</p></noscript>
<script>
var ALIASES = __ALIASES__;
var SCHOOLS = __SCHOOLS__;
// the site's own pages, typed without .html or in another case: /atlas, /Admissions
var PAGES = {"atlas": "atlas.html", "admissions": "admissions.html", "guidelines": "guidelines.html", "index": "", "home": ""};
(function () {
  var parts = location.pathname.split("/").filter(Boolean);
  var gh = /\\.github\\.io$/.test(location.hostname);
  var root = gh && parts.length ? "/" + parts[0] + "/" : "/";
  var segs = gh ? parts.slice(1) : parts;
  var last = segs.length ? segs[segs.length - 1] : "";
  try { last = decodeURIComponent(last); } catch (e) {}
  var key = last.trim().toLowerCase().replace(/\\.html$/, "").replace(/[\\s\\-_.,'’()·–—\\/]/g, "");
  if (Object.prototype.hasOwnProperty.call(PAGES, key) && location.pathname !== root + PAGES[key]) {
    location.replace(root + PAGES[key] + location.hash);
    return;
  }
  var hit = ALIASES[key];
  if (hit && location.pathname !== root + hit + "/") {
    location.replace(root + hit + "/" + location.hash);
    return;
  }
  document.getElementById("h").textContent = "页面不存在 · Page not found";
  var msg = document.getElementById("msg");
  msg.appendChild(document.createTextNode(
    "本站没有“" + last + "”这一页面。各校页面地址如下，例如 /MIT、/Stanford、/JHU（不区分大小写）。"));
  msg.appendChild(document.createElement("br"));
  msg.appendChild(document.createTextNode(
    "No page named “" + last + "”. University pages are listed below (case-insensitive)."));
  var list = document.getElementById("list");
  SCHOOLS.forEach(function (s) {
    var a = document.createElement("a");
    a.href = root + s[0] + "/";
    a.innerHTML = "<i>" + s[1] + "</i><b></b><span></span>";
    a.querySelector("b").textContent = s[2];
    a.querySelector("span").textContent = s[3];
    list.appendChild(a);
  });
  document.getElementById("links").innerHTML =
    '<a href="' + root + '">主页 Home</a> · <a href="' + root + 'atlas.html">政策图谱 Atlas</a> · ' +
    '<a href="' + root + 'admissions.html">申请环节 Admissions</a> · ' +
    '<a href="' + root + 'guidelines.html">学生规范 Guidelines</a>';
})();
</script>
'''


def main():
    d, dm, _, _ = load_data()
    by_id = {s["id"]: s for s in d["schools"]}
    order = [s["id"] for s in sorted(d["schools"], key=lambda s: s["num"])]
    unknown = set(by_id) ^ set(reg.SCHOOLS)
    if unknown:
        raise SystemExit(f"schools.py 与数据集的学校不一致：{sorted(unknown)}")

    cname_file = DOCS / "CNAME"
    ctx = {
        "data": d, "dm": dm, "by_id": by_id, "order": order,
        "tpl": TPL.read_text(encoding="utf-8"),
        "cname": cname_file.read_text(encoding="utf-8").strip() if cname_file.exists() else "",
        "adm": adm.load(),
    }
    # every admissions file is indexed, and every indexed school has its file
    files = {p.name[:-3] for p in ADMISSIONS.glob("[0-9][0-9]-*.md")} - {"00-Application-Platforms"}
    if files ^ set(ctx["adm"]["by_id"]):
        raise SystemExit(f"admissions/ 的文件与 application-index.json 不一致：{sorted(files ^ set(ctx['adm']['by_id']))}")

    table = reg.alias_table({s["id"]: s["short"] for s in d["schools"]})
    existing = {p.name.lower() for p in DOCS.iterdir()} - {reg.slug(i).lower() for i in reg.SCHOOLS}
    clash = sorted(k for k in table if k in {re.sub(r"\.html$", "", e) for e in existing})
    if clash:
        raise SystemExit(f"别名与 docs/ 下已有文件重名：{clash}")

    n_spans = n_marks = n_adm = 0
    for sid in order:
        slug, page, spans, marks = school_page(by_id[sid], ctx)
        n_adm += 'id="admissions"' in page
        out = DOCS / slug / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(wrap_document(page), encoding="utf-8")
        n_spans += spans
        n_marks += marks

    listing = [[reg.slug(i), f"{by_id[i]['num']:02d}", by_id[i]["short"], reg.SCHOOLS[i][2]] for i in order]
    (DOCS / "404.html").write_text(wrap_document(
        NOT_FOUND.replace("__ALIASES__", json.dumps(table, ensure_ascii=False, sort_keys=True))
                 .replace("__SCHOOLS__", json.dumps(listing, ensure_ascii=False))),
        encoding="utf-8")

    print(f"单校页面   {len(order)} 个 → docs/<slug>/index.html")
    print(f"原文标注   {n_spans} 条引文全部在原文中定位并标出（{n_marks} 个高亮片段）")
    print(f"网址别名   {len(table)} 个写法 → {len(order)} 个页面，无冲突 → docs/404.html")
    print(f"申请环节   {n_adm} 个页面含申请环节一节（admissions/）")
    full = sorted(p.name for p in FULL.glob("*.md")) if FULL.exists() else []
    if full:
        print(f"完整原文   {', '.join(full)}：未引用部分以灰色小字显示")


if __name__ == "__main__":
    main()

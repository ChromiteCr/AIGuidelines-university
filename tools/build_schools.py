#!/usr/bin/env python3
"""One page per university:  docs/<slug>/index.html  →  ai.policy.nestudy.cn/<slug>

Each page is that university's AI rules on their own: its twelve provisions as
coded in the atlas, each with the sentence it rests on and where that position
sits among the thirty, followed by the full official text collected for it —
with every cited sentence highlighted in place and tagged with the provision
it supports.

Also writes docs/404.html, which GitHub Pages serves for any missing path. It
redirects recognised variants (/mit, /Mit, /johns-hopkins, /麻省理工, /02) to
the canonical page, and otherwise lists all thirty.

Checks, all fatal:
  - every cited sentence is found in its source file and gets an anchor and a tag
  - every page's HTML nests correctly
  - aliases never collide with each other or with an existing top-level page

Usage:  python3 tools/build_schools.py
"""

import html
import html.parser
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mdlite  # noqa: E402
import schools as reg  # noqa: E402
from sitelib import ROOT, load_data, wrap_document  # noqa: E402

TPL = ROOT / "schools" / "school.template.html"
DOCS = ROOT / "docs"
ADMISSIONS = ROOT / "admissions"   # optional: admissions/<id>.md, rendered when present

E = html.escape

EN_QUESTION = {
    "default_rule": "When an assignment says nothing about AI, what applies?",
    "instructor_override": "Can an instructor's rule take precedence over the institution's?",
    "tiered_scale": "Is there a graduated permission framework rather than one rule for everything?",
    "disclosure": "Must AI use be disclosed, or is disclosure only recommended?",
    "process_evidence": "Should drafts, prompts and edit history be kept?",
    "verification_duty": "Who is responsible when AI output is wrong or a citation is invented?",
    "integrity_framing": "How is a violation classified in the disciplinary system?",
    "detector_stance": "Can an AI-detector result be used as evidence?",
    "data_privacy": "What must not be entered into an AI tool?",
    "ip_copyright": "Does it address copyright and other people's material?",
    "institutional_tools": "Does the institution designate or provide AI tools?",
    "learning_rationale": "Are the rules justified by not bypassing the skills being learned?",
}
EN_HINT = {
    "permission": "who decides whether AI may be used",
    "transparency": "what must be declared after use",
    "accountability": "who answers when something goes wrong",
    "boundaries": "what must not be touched",
    "rationale": "why the rules are what they are",
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

    # ---- locate every cited sentence in the raw file ----------------------
    spans, missing = [], []
    for c in s["cells"]:
        if c["evidence"]:
            i = raw.find(c["evidence"])
            if i < 0:
                missing.append(c["dim"])
            else:
                spans.append((i, i + len(c["evidence"]), c["dim"]))
    if s["quote"]["text"]:
        i = raw.find(s["quote"]["text"])
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
                    f'{bi("摘句", "Quoted")}</a></sup>')
        x = dim_meta[label]
        return (f'<sup class="evtag"><a href="#p-{label}" data-ev="{label}" '
                f'title="{E(x["zh"])} / {E(x["en"])}">{bi(E(x["zh"]), E(x["en"]))}</a></sup>')

    def kv_label(key):
        return bi(E(KV_ZH.get(key, key)), E(key))

    def omission(n, further):
        if further:
            return f'<p class="omit">{bi(f"本节另有 {n} 词未被本项目引用，已略去。", f"{n} further words omitted — not cited by this project.")}</p>'
        return (f'<p class="omit">{bi(f"本节共 {n} 词，未被本项目引用，已略去；全文见官方来源。", f"{n} words omitted here — not cited by this project; see the official source.")}</p>')

    r = mdlite.Renderer(raw, spans, tag_html, lambda l: f"ev-{l}", kv_label, omission)
    title, front, rest = mdlite.split_front(mdlite.parse(raw))
    tk = (f'<p class="tk-label">{bi("以下是整理者撰写的高中改编要点，不是该校原文，也不作为任何条款的证据。", "Below: the collector’s notes on adapting this for high school — not the university’s text, and never used as evidence for any provision.")}</p>')
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
    mast = f'''<header class="mast"><div class="wrap">
  {bi(f"No.{s['num']:02d} / {total} · 三十校 AI 政策图谱", f"No.{s['num']:02d} of {total} · Thirty-School AI Policy Atlas", cls="eyebrow")}
  <h1>{E(s["short"])}</h1>
  <p class="fullname"><span>{E(en_name)}</span><span class="zh">{E(zh_name)}</span></p>
  <div class="chips">
    <span class="chip" title="{E(scope["hint"])}">{bi(f"来源层级 · <b>{E(scope['zh'])}</b>", f"Source level · <b>{E(scope['en'])}</b>")}</span>
    <span class="chip">{bi(f"<b>{covered}</b> / 12 项有明文规定", f"<b>{covered}</b> of 12 provisions addressed")}</span>
    <span class="chip">{bi(f"采集于 <b>{E(accessed)}</b>", f"Accessed <b>{E(accessed)}</b>")}</span>
  </div>
  <nav class="strip" aria-label="十二项条款 / Twelve provisions">{"".join(strip)}</nav>
  <p class="print-url">{E(cname or "")}/{slug}</p>
</div></header>'''

    # ---- pull quote ---------------------------------------------------------
    quote = ""
    if s["quote"]["text"]:
        quote = f'''<section id="quote">
  <div class="sec-head"><h2>{bi("最值得引用的一句", "The line worth quoting")}</h2></div>
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
      <p class="silent-note">{bi("本项目采集的这份官方来源在此条上没有任何表述。这不代表该校没有相关规定，只代表该来源对此未作说明。", "The official source collected here says nothing on this point. That does not mean the university has no rule — only that this source is silent.")}</p>
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
  <p class="sec-sub">{bi("每一项都附该校原文中的那一句，并标出这一立场在三十所学校中所处的位置。颜色越深，规定越明确、越具约束力；斜纹表示该来源未作表述。", "Each provision carries the sentence it rests on, and where that position sits among the thirty. Darker means more explicit and more binding; hatching means the source is silent.")}</p>
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
  <div class="sec-head"><h2>{bi("细节", "Details")}</h2></div>
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
    adm_file = ADMISSIONS / Path(s["file"]).name
    if adm_file.exists():
        adm_raw = adm_file.read_text(encoding="utf-8")
        ar = mdlite.Renderer(adm_raw, [], tag_html, lambda l: f"adm-{l}", kv_label, omission)
        _, afront, arest = mdlite.split_front(mdlite.parse(adm_raw))
        afront_html, abody_html = ar.render_all(afront, arest, tk)
        admissions = f'''<section id="admissions">
  <div class="sec-head"><h2>{bi("申请端的 AI 政策", "AI policy for applicants")}</h2><span class="en2">admissions/{E(adm_file.name)}</span></div>
  {f'<div class="about">{afront_html}</div>' if afront_html else ""}
  <div class="source">{abody_html}</div>
</section>'''

    source = f'''<section id="source">
  <div class="sec-head"><h2>{bi("官方原文", "The official text")}</h2><span class="en2">{E(s["file"])}</span></div>
  <p class="sec-sub">{bi("以下是本项目采集的该校官方文本。被图谱引用的句子已标出，句末的标签对应上方的条款，点击即可跳回。", "Below is the official text collected for this university. Sentences the atlas cites are highlighted; the tag after each names the provision it supports — click it to jump back.")}</p>
  <div class="about">
    <h3>{bi("关于这份材料", "About this material")}</h3>
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
                 "<strong>Official source text, kept as a periodically refreshed snapshot.</strong> Quotations are reproduced verbatim from the university’s own published pages; copyright remains with it and the material is used for academic research and commentary. The classification and ranking are this project’s judgment, not the university’s position. Later revisions are not tracked automatically — verify against the official page before relying on it.")}</p>
  <p class="nav-links"><a href="../">{bi("主页", "Home")}</a> · <a href="../atlas.html">{bi("政策图谱", "Policy atlas")}</a> · <a href="../guidelines.html">{bi("学生规范", "Student guidelines")}</a></p>
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
            .replace("__TITLE__", E(f"{s['short']} 的 AI 使用政策"))
            .replace("__DESC__", E(f"{en_name}（{zh_name}）的 AI 使用政策：12 项条款逐条对照，附官方原文与出处。"))
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
NOT_FOUND = '''<title>找不到这个页面</title>
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
.grid{display:grid;gap:1px;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));background:var(--rule);
  border:1px solid var(--rule);border-radius:3px;overflow:hidden;margin:22px 0}
.grid a{background:var(--surface);padding:10px 12px;text-decoration:none;color:var(--ink);display:flex;gap:8px;align-items:baseline}
.grid a:hover{color:var(--seal-ink)}
.grid i{font-style:normal;font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--ink-3)}
.grid span{font-size:12px;color:var(--ink-3)}
a{color:var(--seal-ink)}
</style>
<main class="wrap">
  <p class="eyebrow">404</p>
  <h1 id="h">正在查找…</h1>
  <p id="msg"></p>
  <div class="grid" id="list"></div>
  <p id="links"></p>
</main>
<noscript><p style="padding:0 20px">找不到这个页面。Page not found.</p></noscript>
<script>
var ALIASES = __ALIASES__;
var SCHOOLS = __SCHOOLS__;
(function () {
  var parts = location.pathname.split("/").filter(Boolean);
  var gh = /\\.github\\.io$/.test(location.hostname);
  var root = gh && parts.length ? "/" + parts[0] + "/" : "/";
  var segs = gh ? parts.slice(1) : parts;
  var last = segs.length ? segs[segs.length - 1] : "";
  try { last = decodeURIComponent(last); } catch (e) {}
  var key = last.trim().toLowerCase().replace(/\\.html$/, "").replace(/[\\s\\-_.,'’()·–—\\/]/g, "");
  var hit = ALIASES[key];
  if (hit && location.pathname !== root + hit + "/") {
    location.replace(root + hit + "/" + location.hash);
    return;
  }
  document.getElementById("h").textContent = "找不到这个页面 · Page not found";
  document.getElementById("msg").textContent =
    "“" + last + "” 不是本站的页面。三十所大学各有一个独立页面，例如 /MIT、/Stanford、/JHU；" +
    "大小写和常见写法会自动跳转。";
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
    }

    table = reg.alias_table({s["id"]: s["short"] for s in d["schools"]})
    existing = {p.name.lower() for p in DOCS.iterdir()} - {reg.slug(i).lower() for i in reg.SCHOOLS}
    clash = sorted(k for k in table if k in {re.sub(r"\.html$", "", e) for e in existing})
    if clash:
        raise SystemExit(f"别名与 docs/ 下已有文件重名：{clash}")

    n_spans = n_marks = 0
    for sid in order:
        slug, page, spans, marks = school_page(by_id[sid], ctx)
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
    adm = sorted(p.name for p in ADMISSIONS.glob("*.md")) if ADMISSIONS.exists() else []
    print(f"申请端     {len(adm)} 份（放入 admissions/ 后重跑即显示）")


if __name__ == "__main__":
    main()

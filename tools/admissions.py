"""Application-stage AI guidance: the admissions/ source set.

admissions/NN-*.md record, per university, what its admissions office says about
applicants using AI — verbatim English excerpts with official links, the
collector's Chinese analysis kept apart from them, and the search record.
00-Application-Platforms.md covers the shared sources Common App and the UC
system, 00-UCAS-AI-Guidance.md the UK platform UCAS. application-index.json
indexes all of it and carries each school's evidence status and one-paragraph
summary.

The school pages and the overview page both render these files through here, so
the two cannot drift apart. Rendering makes three adjustments; the files
themselves are left as they are:
  - links into the local research folders (sources/, research/) keep their text
    but lose the link, because those folders are not published;
  - metadata rows that do nothing but point into those folders are dropped;
    (expansion/ files go through the same renderer; see expansion.py)
  - search-record sections are folded into a closed <details>.
"""

import html
import json
import re

import mdlite
import schools as reg
from sitelib import ROOT

ADM = ROOT / "admissions"
INDEX = ADM / "application-index.json"
PLATFORMS = ADM / "00-Application-Platforms.md"
UCAS = ADM / "00-UCAS-AI-Guidance.md"

# Display order, from the most specific material found to the least. This is an
# order of evidence, not of strictness: the statuses say what was found.
STATUS_ORDER = ["explicit-undergraduate-ai", "uc-system-ai-guidance", "ucas-system-ai-guidance",
                "undergraduate-advice-ai", "authenticity-only", "graduate-only-ai", "no-verified-guidance"]
# (short zh, short en, full en). The full Chinese labels come from the index.
STATUS_TEXT = {
    "explicit-undergraduate-ai": ("本科 AI 明文边界", "Explicit undergraduate rules",
                                  "Explicit AI boundaries for undergraduate applicants (force as stated in the source)"),
    "uc-system-ai-guidance": ("UC 系统共同规定", "UC system (shared source)",
                              "UC system undergraduate AI rules and guidance (a shared source, not a campus policy)"),
    "ucas-system-ai-guidance": ("UCAS 平台共同指导", "UCAS (shared source)",
                                "UCAS undergraduate AI guidance (a shared platform source; each university's rules checked separately)"),
    "undergraduate-advice-ai": ("本科 AI 官方指导", "Official undergraduate guidance",
                                "Official AI guidance or advice for undergraduate applicants"),
    "authenticity-only": ("仅本人写作／真实性要求", "Authenticity requirement only",
                          "Own-work and authenticity requirements; no detailed AI boundaries verified"),
    "graduate-only-ai": ("AI 明文仅见于研究生", "Graduate programmes only",
                         "Explicit AI rules verified only for graduate or specific programmes"),
    "no-verified-guidance": ("未取得可核实指导", "No verifiable guidance",
                             "No verifiable applicable guidance obtained"),
}

KV_ZH = {
    "Evidence status": "证据状态", "Evidence note": "证据说明",
    "Original campus-AI source file": "校内 AI 政策原文",
    "Original campus/course research (different scope)": "校内／课程政策原文（范围不同）",
    "Original campus/course guidance (not admissions policy)": "校内／课程指导（非招生政策）",
    "Original university AI guidance (different scope)": "校内 AI 指导（范围不同）",
    "Related university/course guidance (different scope)": "相关校内／课程指导（范围不同）",
    "Original reference": "原研究参考",
    "Publisher": "发布单位", "Unit / publisher": "发布单位", "Issuing unit": "发布单位",
    "Official URL": "官方链接", "URL": "链接", "Final rendered URL": "最终页面地址",
    "Public page-data used for extraction": "提取所用公开数据",
    "Authority": "来源性质", "Authority kind": "来源性质",
    "Audience / scope": "适用对象", "Scope / authority": "范围／性质",
    "Scope / verification note": "范围与核验说明", "Verification note": "核验说明",
    "Retrieved": "采集时间", "Retrieval": "采集方式", "Date note": "日期说明",
    "Browser note": "浏览器说明", "Earlier retrieval record": "早先采集记录",
    "Query / action": "检索／操作", "Query": "检索", "Result": "结果",
    "Research date": "检索日期", "Search": "检索",
    # expansion/ and the 2026-09-26 admissions files
    "Status": "证据状态", "Format": "格式说明", "Research snapshot": "检索日期",
    "Research acquisition": "采集说明", "Research record": "采集记录", "Research review": "复核日期",
    "Acquired": "采集时间", "Source date": "来源日期", "Publication date": "发布日期",
    "Final URL": "最终页面地址", "Provenance note": "来源说明", "Context": "上下文说明",
    "Saved body": "保存的正文", "Quote language": "引文语言",
}

# Rows whose only content is a pointer into the unpublished research folders.
DROP_KEYS = {"Saved text", "Local readable text", "Local snapshot", "Saved readable text",
             "Screenshot", "Desktop retry record"}
# The same, but only when the row is nothing more than such a pointer:
# "Saved body: unavailable or empty; …" is a finding and stays.
DROP_IF_POINTER = {"Local source body", "Saved body", "Snapshot"}
_POINTER = re.compile(r"^\[?(\.\./)*(application/)?(sources|research)/[^\s\]]+\]?(\([^)\s]+\))?\.?$")
# A closing line that points at the research JSON and says nothing else.
DROP_PARA = re.compile(r"^来源元数据与逐条引文：")
# "Search log", "Search and retry log", "检索记录（2026-09-24）" — but not "检索与局限",
# which also holds the limitations and stays open.
FOLD = re.compile(r"\bsearch\b|检索记录", re.I)


def load():
    """The index, with schools keyed by id ("02-MIT") and labels resolved."""
    d = json.loads(INDEX.read_text(encoding="utf-8"))
    by_id = {}
    for s in d["schools"]:
        sid = s["file"][:-3]
        if sid not in reg.SCHOOLS:
            raise SystemExit(f"application-index.json: 未知学校文件 {s['file']}")
        if s["status"] not in STATUS_TEXT:
            raise SystemExit(f"{s['file']}: 未知证据状态 {s['status']!r}")
        by_id[sid] = s
    d["by_id"] = by_id
    return d


def status_short(status):
    zh, en, _ = STATUS_TEXT[status]
    return zh, en


def resolver(prefix, own=None, from_campus=False):
    """Map a link target in an admissions file to a site address, or None.

    prefix is the path from the current page to the site root ("../" on a school
    page, "" on the overview). "../NN-X.md" is that school's campus-policy file,
    shown under #source on its page; "NN-X.md" is another admissions file.
    00-UCAS-AI-Guidance.md has its own section on the overview (#ucas).
    """
    def resolve(url):
        if url.startswith(("http://", "https://")):
            return url
        m = re.fullmatch(r"(\.\./|application/)?(\d\d-[A-Za-z-]+)\.md(#.*)?", url)
        if not m:
            return None                      # sources/…, research/…: not published
        sid = m.group(2)
        # From an admissions file "../NN-X.md" is the campus file; from a campus
        # file (expansion/, collected beside application/) the plain name is.
        campus = m.group(1) == "../" if not from_campus else m.group(1) is None
        if sid.startswith("00-"):
            anchor = "ucas" if "UCAS" in sid else "platforms"
            return f"{prefix}admissions.html#{anchor}"
        if sid not in reg.SCHOOLS:
            return None
        anchor = "#source" if campus else "#admissions"
        return anchor if sid == own else f"{prefix}{reg.slug(sid)}/{anchor}"
    return resolve


def _dropped(item):
    kv = mdlite._kv_split(item["segs"][0], mdlite.KV_WIDE)
    if not kv:
        return False
    key, (_, value) = kv
    return key in DROP_KEYS or (key in DROP_IF_POINTER and bool(_POINTER.match(value.strip())))


def _prune(blocks):
    out = []
    for b in blocks:
        if b["t"] == "list":
            items = [it for it in b["items"] if not _dropped(it)]
            if not items:
                continue
            b = dict(b, items=items)
        elif b["t"] == "p" and DROP_PARA.match(b["segs"][0][1]):
            continue
        out.append(b)
    # a rule left dangling at the very end once its closing line is gone
    while out and out[-1]["t"] == "hr":
        out.pop()
    return out


def _fold(text, level):
    if level == 2 and FOLD.search(text) and "局限" not in text:
        return f'<span class="fold-h">{html.escape(text)}</span>'
    return None


def render(path, prefix, own=None, kv_label=None, from_campus=False):
    """(front-matter html, body html) for one admissions (or expansion/) file."""
    raw = path.read_text(encoding="utf-8")
    _, front, rest = mdlite.split_front(mdlite.parse(raw))
    kept = _prune([{"t": "list", "items": front}]) if front else []
    front = kept[0]["items"] if kept else []
    r = mdlite.Renderer(raw, [], lambda lab: "", lambda lab: f"adm-{lab}", kv_label, None,
                        resolve=resolver(prefix, own, from_campus), kv_re=mdlite.KV_WIDE, fold=_fold)
    return r.render_all(front, _prune(rest), "")


def front_value(path, key):
    """The raw value of one front-matter row, e.g. front_value(p, "Accessed")."""
    m = re.search(rf"^- {re.escape(key)}:\s*(.+)$", path.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip() if m else ""

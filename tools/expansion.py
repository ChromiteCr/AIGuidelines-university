"""Campus AI guidance for the 22 universities added for the College Fair: expansion/.

expansion/NN-*.md record, per university, short verbatim excerpts from its
official campus guidance (teaching, coursework, academic integrity), with the
collector's Chinese analysis kept apart from them. academic-index.json indexes
the same material and gives each school an evidence status and a summary.

These files are not coded against the atlas's twelve provisions. The excerpts
were chosen for what each source says, not transcribed as a policy text, so a
provision they happen not to mention would say nothing about the policy. The
schools get a page each but no row in the atlas and no place in its figures.

The files share the admissions files' Markdown dialect and their pointers into
unpublished research folders, so they render through admissions.render.
"""

import json

import admissions as adm
import schools as reg
from sitelib import ROOT

EXP = ROOT / "expansion"
INDEX = EXP / "academic-index.json"

# From the broadest source found to the narrowest. The statuses describe the
# kind of source, not what it permits.
STATUS_ORDER = ["university-wide-policy", "official-student-guidance", "unit-specific-guidance",
                "faculty-facing-guidance", "no-verified-guidance"]
# (short zh, short en, full en). The full Chinese labels come from the index.
STATUS_TEXT = {
    "university-wide-policy": ("全校政策／诚信规则", "University-wide policy",
                               "University-wide policy or integrity rules (specific permissions as stated in the source)"),
    "official-student-guidance": ("官方学生使用指导", "Official student guidance",
                                  "Official guidance addressed to students"),
    "unit-specific-guidance": ("学院／部门范围指导", "Unit-level guidance",
                               "Guidance scoped to a school, department, course or teaching unit"),
    "faculty-facing-guidance": ("教师教学建议", "Guidance for instructors",
                                "Teaching advice for instructors; student-facing AI rules not verified"),
    "no-verified-guidance": ("未取得可核实指导", "No verifiable guidance",
                             "No verifiable applicable guidance obtained"),
}


def load():
    """The index, with schools keyed by id ("31-UC-Irvine")."""
    d = json.loads(INDEX.read_text(encoding="utf-8"))
    by_id = {}
    for s in d["schools"]:
        sid = s["file"][:-3]
        if sid not in reg.SCHOOLS:
            raise SystemExit(f"expansion/academic-index.json: 未知学校文件 {s['file']}")
        if s["status"] not in STATUS_TEXT:
            raise SystemExit(f"{s['file']}: 未知证据状态 {s['status']!r}")
        if not (EXP / s["file"]).exists():
            raise SystemExit(f"expansion/{s['file']} 不存在")
        by_id[sid] = s
    files = {p.name[:-3] for p in EXP.glob("[0-9][0-9]-*.md")}
    if files ^ set(by_id):
        raise SystemExit(f"expansion/ 的文件与 academic-index.json 不一致：{sorted(files ^ set(by_id))}")
    d["by_id"] = by_id
    return d


def status_short(status):
    zh, en, _ = STATUS_TEXT[status]
    return zh, en


def render(sid, prefix, kv_label=None):
    """(front-matter html, body html) for one school's campus file."""
    return adm.render(EXP / f"{sid}.md", prefix, sid, kv_label, from_campus=True)

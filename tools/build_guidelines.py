#!/usr/bin/env python3
"""guidelines/guidelines.html -> docs/guidelines.html, fact-checked on the way.

The atlas is generated from the dataset, so it cannot contradict it. The
guidelines are hand-written prose, so they can — and silently. Every numeric
claim is therefore registered below as the literal phrase it must appear as,
with the number filled in from data/policies.json. The check searches the
actual HTML for that phrase, so it verifies the document rather than this
script's own constants. Re-run the extraction and a figure moves, and the build
fails until the sentence around it is rewritten.

Verbatim quotations are checked too: each <blockquote> must still be a literal
substring of the univ/ file its <cite> names.

Usage:  python3 tools/build_guidelines.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sitelib import ROOT, assertion_builder, cn, load_data, publish  # noqa: E402

SRC = ROOT / "guidelines" / "guidelines.html"
DST = ROOT / "docs" / "guidelines.html"


def checks():
    """(label, value, phrase) — phrase must appear verbatim in the document."""
    d, dm, count, disclose = load_data()
    m = d["meta"]
    pct = lambda k: round(dm[k]["agreement"] * 100)
    C = []
    add = assertion_builder(C)

    # ---- masthead ---------------------------------------------------------
    add("总校数", m["schools"], '<b>{n}</b><span lang="zh">所美国大学的官方政策')
    add("条款数", m["dimensions"], '<b>{n}</b><span lang="zh">项逐条对照的条款')
    add("引文核验", m["evidence_matched"], '<b>{n}</b><span lang="zh">条经逐字核验的原文依据')

    # ---- §0 default rule --------------------------------------------------
    add("默认·一致度", pct("default_rule"),
        "<b>{n}%</b>", "默认规则 · 一致度 {n}%", "Default rule · {n}% agreement")
    add("默认·覆盖", dm["default_rule"]["covered"], "{c}所在其官方来源中作出明确表述的学校")
    add("默认禁止", count("default_rule", "prohibited_by_default"),
        "<b>{n}</b> 所默认禁止未经许可的使用", "<b>{n}</b> prohibit unapproved use by default")
    add("等同他人协助", count("default_rule", "treated_as_outside_help"),
        "<b>{n}</b> 所将其等同于他人代为完成", "<b>{n}</b> treat it as work done by another")
    add("有条件允许", count("default_rule", "conditional_use_allowed"),
        "<b>{n}</b> 所有条件允许", "<b>{n}</b> allow it conditionally")
    add("交由教师决定", count("default_rule", "instructor_decides_no_default"),
        "<b>{n}</b> 所交由任课教师逐门确定", "<b>{n}</b> leave it to the instructor",
        "{c}所学校就是这么规定的", "{e} of the thirty rely on exactly that")
    add("默认·未提及", count("default_rule", "not_addressed"),
        "<b>{n}</b> 所未作表述", "<b>{n}</b> states no position")

    # ---- §1 tiers ---------------------------------------------------------
    add("分级·明确框架", count("tiered_scale", "explicit_named_scale"),
        "有{c}所给出了明确的分级框架", "Only {e} of the thirty publish an explicit graduated framework")
    add("分级·非正式", count("tiered_scale", "informal_categories"),
        "另有{c}所用非正式的分类", "{e} more use informal categories")
    add("分级·沉默", dm["tiered_scale"]["silent"], "{c}所完全没提", "{e} say nothing")

    # ---- §3 disclosure ----------------------------------------------------
    add("披露·一致度", pct("disclosure"),
        "披露要求 · 一致度 {n}%", "Disclosure · {n}% agreement")
    add("强制披露", count("disclosure", "required"), "<b>{n}</b> 所强制", "<b>{n}</b> require it")
    add("存疑即披露", count("disclosure", "default_to_disclosing"),
        "<b>{n}</b> 所存疑即披露", "<b>{n}</b> says disclose when in doubt")
    add("建议披露", count("disclosure", "recommended"), "<b>{n}</b> 所建议", "<b>{n}</b> recommend")
    add("依课程而定", count("disclosure", "course_dependent"),
        "<b>{n}</b> 所依课程而定", "<b>{n}</b> leave it to the course")
    add("披露·未提及", count("disclosure", "not_addressed"),
        "<b>{n}</b> 所未提及", "<b>{n}</b> are silent")
    add("披露·工具名称", disclose("tool_name"), "这三项分别有 {n} 所")
    add("披露·提示词", disclose("prompts"), "{c}所学校要求记录 prompt", "{e} of the thirty ask for")

    # ---- §4 ---------------------------------------------------------------
    add("核实·一致度", round(dm["verification_duty"]["agreement"] * 100),
        "一致度 {n}%）", "({n}% agreement)")
    add("隐私·一致度", pct("data_privacy"),
        "数据与隐私 · 一致度 {n}%", "privacy · {n}% agreement")
    add("隐私·禁受限数据", count("data_privacy", "restricted_data_prohibited"),
        "<b>{n}</b> 所禁止上传受限数据", "<b>{n}</b> prohibit uploading restricted data")
    add("隐私·上传即公开", count("data_privacy", "upload_is_public_disclosure"),
        "<b>{n}</b> 所视上传为公开", "<b>{n}</b> treat upload as public")
    add("隐私·一般提醒", count("data_privacy", "general_caution"),
        "<b>{n}</b> 所一般提醒", "<b>{n}</b> give general caution")
    add("隐私·沉默", dm["data_privacy"]["silent"],
        "<b>{n}</b> 所未提及", "<b>{n}</b> are silent")
    add("版权·覆盖", dm["ip_copyright"]["covered"],
        "提到这一条的{c}所", "{e} address this")

    # ---- §5 consequences --------------------------------------------------
    add("违规定性·覆盖", dm["integrity_framing"]["covered"],
        "{c}所把违规使用定性为学术诚信问题", "{e} classify unauthorized use")
    add("违规·学术不端", count("integrity_framing", "academic_integrity_violation"),
        "其中{c}所归入学术", "{e} as misconduct")
    add("违规·等同抄袭", count("integrity_framing", "explicitly_plagiarism"),
        "{c}所明确等同抄袭", "{e} as plagiarism outright")

    # ---- §4 institutional tools (we designate none) ------------------------
    add("机构工具·沉默", dm["institutional_tools"]["silent"],
        "三十所学校里有{c}所同样没有指定任何工具", "{e} of the thirty likewise designate nothing")
    add("机构工具·有表态", dm["institutional_tools"]["covered"],
        "在表态的{c}所里", "among the {e} that do address it")
    add("机构工具·提供机构版", count("institutional_tools", "institution_provided_tool"),
        "{c}所提供机构版工具", "{e} provide an institutional tier")
    add("机构工具·批准清单", count("institutional_tools", "approved_tool_list"),
        "{c}所发布批准清单", "{e} publish an approved list")

    # ---- §5 detectors -----------------------------------------------------
    add("检测器·有表态", dm["detector_stance"]["covered"],
        "三十校中仅 {n} 所有表态", "only {n} of 30 take a position")
    add("检测器·不得为主证", count("detector_stance", "not_sole_or_primary_evidence"),
        "<b>{n}</b> 所明确", "<b>{n}</b> state it may not be sole")
    add("检测器·质疑可靠", count("detector_stance", "reliability_questioned"),
        "<b>{n}</b> 所质疑其可靠性", "<b>{n}</b> question its reliability")
    add("检测器·须先告知", count("detector_stance", "permitted_with_advance_notice"),
        "<b>{n}</b> 所要求提前告知", "<b>{n}</b> requires advance notice")
    add("检测器·沉默", dm["detector_stance"]["silent"],
        "<b>{n}</b> 所完全沉默", "<b>{n}</b> say nothing at all")
    add("过程留证·沉默", dm["process_evidence"]["silent"],
        "三十所学校里有{c}所对「过程留证」未作表述", "{e} of the thirty say nothing about keeping process evidence")

    # ---- appendix C -------------------------------------------------------
    add("格数", m["cells"], "{n} 格逐格对照", "{n} cells")
    add("有明文", m["filled"], "其中 {n} 格查有明文", "{n} cells have an explicit rule")
    add("沉默格", m["silent"], "{n} 格该来源沉默", "in {n} the source is silent")
    add("引文总数", m["evidence_matched"], "全部 {n} 条引文", "All {n} quotations")
    return C


def main():
    publish(SRC.read_text(encoding="utf-8"), DST, checks(), label="规范")


if __name__ == "__main__":
    main()

"""Codebook for the policy atlas.

Single source of truth for dimensions, allowed values, bilingual labels, and
strictness ranks. The extraction agents write raw codes; everything a human
sees is looked up here. Keep this file and the workflow prompt in sync.

rank: 0 = source is silent, 1 = weak/soft, 2 = substantive, 3 = strongest form.
Rank measures how explicit and binding the provision is, NOT whether it is good.
"""

# --- dimension groups -------------------------------------------------------

GROUPS = [
    ("permission", "许可", "Permission", "谁有权决定能不能用"),
    ("transparency", "透明", "Transparency", "用了之后要交代什么"),
    ("accountability", "责任", "Accountability", "出了问题算谁的"),
    ("boundaries", "边界", "Boundaries", "哪些东西不能碰"),
    ("rationale", "理由", "Rationale", "凭什么这样规定"),
]

# key, group, zh label, en label, one-line zh question the column answers
DIMENSIONS = [
    ("default_rule", "permission", "默认规则", "Default rule",
     "作业没说能不能用 AI 时，按什么算？"),
    ("instructor_override", "permission", "课程规则优先", "Instructor override",
     "任课教师的规定能不能盖过校级规定？"),
    ("tiered_scale", "permission", "分级许可", "Tiered scale",
     "有没有一套分档的许可框架，而不是一刀切？"),
    ("disclosure", "transparency", "披露要求", "Disclosure",
     "用了 AI 必须说明吗，还是只是建议？"),
    ("process_evidence", "transparency", "过程留证", "Process evidence",
     "要不要保留草稿、提示词、编辑历史？"),
    ("verification_duty", "accountability", "核实责任", "Verification duty",
     "AI 说错了、编了引注，谁负责？"),
    ("integrity_framing", "accountability", "违规定性", "Integrity framing",
     "违规使用在纪律体系里被定成什么性质？"),
    ("detector_stance", "accountability", "检测器证据", "Detector evidence",
     "AI 检测器的结果能当证据吗？"),
    ("data_privacy", "boundaries", "数据与隐私", "Data & privacy",
     "什么内容不能喂给 AI？"),
    ("ip_copyright", "boundaries", "知识产权", "IP & copyright",
     "有没有管版权和他人材料？"),
    ("institutional_tools", "boundaries", "机构工具", "Institutional tools",
     "学校是否指定或提供了 AI 工具？"),
    ("learning_rationale", "rationale", "学习理由", "Learning rationale",
     "规则是否以“不能绕过要学的能力”为依据？"),
]

# key -> [(value, zh, en, rank)]
VALUES = {
    "default_rule": [
        ("prohibited_by_default", "默认禁止", "Prohibited by default", 3),
        ("treated_as_outside_help", "等同他人协助", "Treated as outside help", 3),
        ("conditional_use_allowed", "有条件允许", "Conditional use allowed", 2),
        ("instructor_decides_no_default", "交由教师决定", "Instructor decides, no default", 1),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "instructor_override": [
        ("course_rule_supersedes", "课程规则优先", "Course rule supersedes", 2),
        ("course_rule_within_limits", "教师可定但有底线", "Instructor rules within limits", 2),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "tiered_scale": [
        ("explicit_named_scale", "明确分级框架", "Explicit named scale", 3),
        ("informal_categories", "非正式分类", "Informal categories", 1),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "disclosure": [
        ("required", "强制披露", "Required", 3),
        ("default_to_disclosing", "存疑即披露", "Default to disclosing", 2),
        ("recommended", "建议披露", "Recommended", 1),
        ("course_dependent", "依课程而定", "Course dependent", 1),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "detector_stance": [
        ("not_sole_or_primary_evidence", "不得作为唯一或主要证据", "Not sole or primary evidence", 3),
        ("reliability_questioned", "质疑其可靠性", "Reliability questioned", 2),
        ("permitted_with_advance_notice", "须提前告知后方可使用", "Permitted with advance notice", 1),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "data_privacy": [
        ("upload_is_public_disclosure", "上传即视为公开", "Upload is public disclosure", 3),
        ("restricted_data_prohibited", "禁止上传受限数据", "Restricted data prohibited", 3),
        ("general_caution", "一般性提醒", "General caution", 1),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "ip_copyright": [
        ("addressed", "有明确规定", "Addressed", 2),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "verification_duty": [
        ("student_fully_responsible", "学生对成品完全负责", "Student fully responsible", 3),
        ("verification_required", "须自行核实", "Verification required", 2),
        ("general_caution", "一般性提醒", "General caution", 1),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "integrity_framing": [
        ("explicitly_plagiarism", "明确等同抄袭", "Explicitly plagiarism", 3),
        ("academic_integrity_violation", "学术不端", "Academic integrity violation", 2),
        ("unauthorized_assistance", "未授权协助", "Unauthorized assistance", 2),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "institutional_tools": [
        ("institution_provided_tool", "提供机构版工具", "Institution-provided tool", 2),
        ("approved_tool_list", "批准工具清单", "Approved tool list", 2),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "process_evidence": [
        ("required", "强制留证", "Required", 3),
        ("recommended", "建议留证", "Recommended", 1),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
    "learning_rationale": [
        ("explicit_learning_objective_rationale", "明确以学习目标为据", "Explicit learning-objective rationale", 3),
        ("general_statement", "一般性表述", "General statement", 1),
        ("not_addressed", "未提及", "Not addressed", 0),
    ],
}

DISCLOSE_ITEMS = {
    "tool_name": ("工具名称", "Tool name"),
    "prompts": ("提示词", "Prompts"),
    "ai_output": ("AI 输出内容", "AI output"),
    "original_drafts": ("原始草稿", "Original drafts"),
    "extent_of_use": ("使用范围与程度", "Extent of use"),
    "formal_citation": ("正式引注", "Formal citation"),
    "editing_history": ("编辑历史", "Editing history"),
}

SCOPE = {
    "university_wide": ("校级通用", "University-wide",
                        "中央或教务层级、面向全校学生的政策"),
    "unit_or_school": ("院系或项目级", "Unit or school",
                       "仅适用于某一学院、项目或系"),
    "instructor_facing": ("面向教师", "Instructor-facing",
                          "教学中心资源，指导教师而非直接约束学生"),
    "mixed": ("混合来源", "Mixed",
              "文件同时含校级来源与更窄范围的来源"),
}

VERDICT = {
    "clean": ("审计通过", "Clean"),
    "minor": ("轻微修正", "Minor corrections"),
    "major": ("重大修正", "Major corrections"),
    "audit_failed": ("审计未完成", "Audit failed"),
}


def value_meta(dim_key, value):
    for v, zh, en, rank in VALUES.get(dim_key, []):
        if v == value:
            return {"value": v, "zh": zh, "en": en, "rank": rank}
    return None


def dim_index():
    return {d[0]: i for i, d in enumerate(DIMENSIONS)}


# Short zh labels for matrix cells (<=5 chars). Keyed by dimension then value,
# because several value codes repeat across dimensions.
SHORT = {
    "default_rule": {
        "prohibited_by_default": "默认禁止", "treated_as_outside_help": "等同求助",
        "conditional_use_allowed": "有条件", "instructor_decides_no_default": "教师定",
        "not_addressed": "未提及"},
    "instructor_override": {
        "course_rule_supersedes": "课程优先", "course_rule_within_limits": "有底线",
        "not_addressed": "未提及"},
    "tiered_scale": {
        "explicit_named_scale": "明确分级", "informal_categories": "粗分类",
        "not_addressed": "未提及"},
    "disclosure": {
        "required": "强制", "default_to_disclosing": "存疑即披", "recommended": "建议",
        "course_dependent": "依课程", "not_addressed": "未提及"},
    "detector_stance": {
        "not_sole_or_primary_evidence": "不得为主证", "reliability_questioned": "质疑可靠",
        "permitted_with_advance_notice": "须先告知", "not_addressed": "未提及"},
    "data_privacy": {
        "upload_is_public_disclosure": "上传即公开", "restricted_data_prohibited": "禁受限数据",
        "general_caution": "一般提醒", "not_addressed": "未提及"},
    "ip_copyright": {"addressed": "有规定", "not_addressed": "未提及"},
    "verification_duty": {
        "student_fully_responsible": "完全负责", "verification_required": "须核实",
        "general_caution": "一般提醒", "not_addressed": "未提及"},
    "integrity_framing": {
        "explicitly_plagiarism": "等同抄袭", "academic_integrity_violation": "学术不端",
        "unauthorized_assistance": "未授权协助", "not_addressed": "未提及"},
    "institutional_tools": {
        "institution_provided_tool": "机构版工具", "approved_tool_list": "批准清单",
        "not_addressed": "未提及"},
    "process_evidence": {
        "required": "强制留证", "recommended": "建议留证", "not_addressed": "未提及"},
    "learning_rationale": {
        "explicit_learning_objective_rationale": "学习目标", "general_statement": "一般表述",
        "not_addressed": "未提及"},
}


def short_label(dim_key, value):
    return SHORT.get(dim_key, {}).get(value, value)

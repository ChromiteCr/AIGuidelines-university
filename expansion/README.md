# 补充的 22 所：校内 AI 规范摘录 / The 22 added universities: campus guidance

依据 College Fair 的学校名单，在原有 30 所之外补充的 22 所大学（编号 31–52），包括美国文理学院，
以及英国、加拿大、新加坡、日本和中国香港的大学。本目录收录它们在课程、作业与学术诚信方面的官方
AI 指导；它们的申请环节资料在 [admissions/](../admissions/README.md)。采集于 2026 年 9 月 26 日，各来源的
实际获取时间见文件与索引。

站点上每所学校有独立页面（如 [/Oxford](https://ai.policy.nestudy.cn/Oxford)），并在主页索引和图谱表格中与前
30 所合列。

## 文件

| 文件 | 内容 |
|------|------|
| `31-UC-Irvine.md` … `52-Toronto.md` | 每校一份：证据状态、官方来源（发布单位、链接、适用范围、来源性质、采集时间）、逐字英文摘录、中文分析（与原文分开标注）、适用边界与研究局限、面向高中的改编建议（整理者所写，非校规） |
| `academic-index.json` | 机器可读索引：每校的证据状态、中文摘要、来源与引文 |

## 为什么没有编码

原有 30 所的 `univ/` 文件是各校政策的相关全文，图谱据此按 12 项条款逐校编码，「未提及」表示所采集的
文本没有就该条款作出表述。这 22 所只收录**摘录**（每校 1–3 个来源、1–6 条引文），摘录按来源内容
选取；摘录没有涉及的条款，无法据以判断该校是否有规定。若照样编码，「未摘录」会被记成「未规定」。
因此这 22 所在图谱表格中整行标为「未编码」，不计入一致度统计，也不进入学生规范中的任何数字。

## 证据状态

描述找到的是**哪一类来源**，不是宽严等级。

| 状态 | 含义 | 校数 |
|------|------|------|
| `university-wide-policy` | 全校政策或学术诚信规则（具体权限以来源为准） | 7 |
| `official-student-guidance` | 面向学生的官方使用指导 | 12 |
| `unit-specific-guidance` | 学院、部门、课程或教学单位范围的指导 | 2 |
| `faculty-facing-guidance` | 面向教师的教学建议，未核实到面向学生的 AI 细则 | 1 |

官方教学指南不自动等于全校强制政策；系所或课程规则不等于所有课程的默认规则；校内规定也不能
推及申请材料。

## 核验

全部 77 条英文摘录均与采集时保存的官方正文逐字比对（仅标准化空白），并与本目录的文件一致。
保存的正文是第三方网页的完整副本，留在离线资料中，没有放进本仓库；文件中指向 `sources/` 的链接在
站点上只显示文字。

## 版权

英文摘录版权归各该大学所有，为学术研究与评述目的引用，**不适用**本仓库的 MIT 许可；中文分析、证据
状态与索引按 CC BY 4.0 发布。完整说明见根目录 [NOTICE](../NOTICE)。本仓库由个人整理编排，与上述大学
无隶属、赞助或背书关系。

---

Campus AI guidance from the 22 universities added to the original 30 from the College Fair's list
(Nos. 31–52), including U.S. liberal arts colleges and universities in the UK, Canada, Singapore, Japan
and Hong Kong. Collected 26 September 2026. Only excerpts were collected, so these universities are not
coded against the atlas's 12 provisions: an excerpt that does not mention a provision says nothing about
whether the university has a rule on it. The atlas lists them as not coded and leaves them out of every
figure. English excerpts are verbatim and remain the universities' copyright; the Chinese analysis,
evidence statuses and index are released under CC BY 4.0 (see [NOTICE](../NOTICE)).

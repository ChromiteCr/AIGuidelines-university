# 申请环节的 AI 政策 / AI in the application

52 所大学招生办公室与申请平台（Common App、UC 系统、UCAS）就申请人使用 AI 的公开表述，以本科
新生申请为主。学校名单与编号沿用主目录：01–30 为美国 30 所大学，31–52 为依据 College Fair 的学校
名单补充的 22 所。站点页面：<https://ai.policy.nestudy.cn/admissions.html>，各校另见其单校页面的
「申请环节的 AI 政策」一节（如 [/Yale#admissions](https://ai.policy.nestudy.cn/Yale/#admissions)）。

## 文件

| 文件 | 内容 |
|------|------|
| `01-Stanford.md` … `52-Toronto.md` | 每校一份：访问日期、适用范围、证据状态、官方来源与逐字英文引文、中文分析（与原文分开标注）、允许／禁止／未说明的用途、研究局限、检索记录 |
| `00-Application-Platforms.md` | 共同来源：Common App 欺诈政策与 UC 系统的申请诚信声明、申请指南；不计为额外学校 |
| `00-UCAS-AI-Guidance.md` | 共同来源：UCAS 的个人陈述 AI 指导、本科申请声明、欺诈与核验、相似度检查；不计为额外学校，也不计为英国各校的政策 |
| `application-index.json` | 机器可读索引：每校的证据状态、中文摘要、来源、引文与检索记录 |
| `application-summary.csv` | 同一索引的表格版 |

## 证据状态

证据状态描述**找到了什么材料**，不是宽严等级。

| 状态 | 含义 | 校数 |
|------|------|------|
| `explicit-undergraduate-ai` | 对本科申请人使用 AI 写明了边界（允许、禁止或后果），效力以来源为准 | 24 |
| `uc-system-ai-guidance` | 依据 UC 系统的共同来源，不是校区单独发布的政策 | 4 |
| `undergraduate-advice-ai` | 官方渠道给出指导或劝告，但未写成明确边界 | 5 |
| `authenticity-only` | 有本人写作或真实性要求，未核实到针对 AI 的具体边界 | 7 |
| `graduate-only-ai` | 已核实的 AI 明文只适用于研究生或特定项目 | 3 |
| `no-verified-guidance` | 未取得可核实的适用指导 | 9 |

索引另定义了 `ucas-system-ai-guidance`（依据 UCAS 共同来源），目前没有学校归入此类：英国 4 所
大学各自归入上表的状态，UCAS 的材料单独列出。

未检索到或未说明，不代表没有规定，更不代表允许。

## 2026-09-25 补充检索

Brown 与 Columbia 的本科页面在 2026-09-24 无法访问，当日未取得正文。9 月 25 日补充检索
取得正文，引文与页面逐字核对：

- **Brown**：本科 Integrity in the Application Process 页有专门的 AI 一节，证据状态由
  `graduate-only-ai` 更新为 `explicit-undergraduate-ai`。
- **Columbia**：本科新生申请页与真实性声明页均未逐项规定 AI 用途，只有本人原创与真实性
  要求，证据状态由 `no-verified-guidance` 更新为 `authenticity-only`。

两校文件保留了此前的受阻记录，新增内容写入各自的来源、引文、局限与检索记录；
索引与 CSV 同步更新。

## 2026-09-26 扩充

依据 College Fair 的学校名单新增 31–52 共 22 所（含美国文理学院，以及英国、加拿大、新加坡、日本和
中国香港的大学），并新增 UCAS 共同来源。01–30 的文件未改动；索引与 CSV 在原有 30 行之后追加
22 行，Brown 与 Columbia 两行仍为 9 月 25 日补充检索后的版本。新增部分的全部英文引文均与采集时
保存的官方正文逐字比对（仅标准化空白）。

「未取得可核实指导」的 9 所都在新增的 22 所中，多为招生页面拒绝访问、正文为空，或已读页面没有
AI 专项表述。

## 未收入本仓库的材料

原始资料集另有网页快照（`sources/`）和检索、复核过程记录（`research/`）。快照是第三方
网页的完整副本，不宜公开再发布；过程记录只用于核验。两者都留在离线副本中，没有放进
本仓库。各校文件中指向这两个目录的链接在站点上只显示文字，不可点击；只指向这两个目录的
条目（如 Saved text、Screenshot）在站点上不显示。

## 版权

英文引文版权归各校与申请平台所有，为学术研究与评述目的引用；中文分析与证据状态的许可
见根目录 [NOTICE](../NOTICE)。这是访问时点的快照，不保证适用于任何未来申请季；提交申请前
请以当季官方页面与申请系统中的最终声明为准。

---

What the admissions offices of 52 universities, and the application platforms (Common App, the UC
system, UCAS), publish about applicants using AI, chiefly for first-year undergraduate applications.
Nos. 01–30 are the 30 U.S. universities; 31–52 were added from the College Fair's list. English
quotations are verbatim and remain the publishers' copyright; the Chinese analysis and evidence statuses
are this project's (see [NOTICE](../NOTICE)). Evidence statuses describe what material was found, not
how strict a rule is. Web snapshots and process records from the original collection are kept offline
and not redistributed here.

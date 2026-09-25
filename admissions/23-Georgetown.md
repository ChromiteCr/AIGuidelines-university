# Georgetown University: Application & Admissions AI Guidance — Source Text

- Accessed: 2026-09-24 (Asia/Shanghai)
- Format note: Official pages were live-fetched using ordinary requests GET. Readable UTF-8 text is preserved locally; navigation/scripts were removed where tagged, and layout/whitespace may differ. Short English excerpts retain the source wording and were checked after whitespace normalization.
- Scope note: 主要证据为Fall 2027 first-year Georgetown Application的公开申请认证；研究生CEH与MBA仅作分项目对照。
- Evidence status: `explicit-undergraduate-ai` — 各来源分别标明政策/申请认证或官方建议，不以搜索空白推断许可。
- Original reference: [../23-Georgetown.md](../23-Georgetown.md)（原在校AI使用资料，不代替申请规则）

## 中文要点

公开本科申请表的签名确认明确禁止用AI工具完成申请任何部分（含文书），未列校对/润色例外。CEH硕士亦禁AI辅助/代写，而MBA允许有限辅助；这些研究生差异不能覆盖本科禁令。[S1][S2][S3]

## Official sources and exact excerpts

### [S1] First Year Application for Admission — Application Affirmation and Electronic Signature

- Publisher: Georgetown University, Office of Undergraduate Admissions
- Official URL: https://uapply.georgetown.edu/register/firstyearapplication
- Page date: Not stated
- Audience / scope: Fall 2027 first-year Georgetown Application申请者及签名的家长/监护人 (`undergraduate`)
- Authority: `policy` — 公开申请表的签名确认，具有申请认证性质；未登录、未提交，仅普通GET读取。表单显示Fall 2027，不是网页发布日。
- Retrieval: `full-text`; ordinary GET returned HTTP 200. Accessed/saved: 2026-09-24T23:08:37+08:00
- Saved readable text: [sources/23-Georgetown-S1.txt](sources/23-Georgetown-S1.txt)

**[S1-Q1] explicit undergraduate prohibition**

> Further, the applicant understands that the use of artificial intelligence (AI) tools to complete any portion of the application, including essays, is prohibited.

**[S1-Q2] general false/incomplete/inaccurate information consequences**

> The applicant understands that Georgetown may take disciplinary action, including rescission of admission and dismissal from the university, if information or statements submitted during the admissions process are incomplete, inaccurate, or false.

**[S1-Q3] responsibility for third-party assistance**

> If the applicant received assistance from a third party in completing the application, the applicant takes full responsibility for the accuracy of the information that was submitted.

### [S2] How to Apply — M.S. in Climate, Environment, and Health

- Publisher: Georgetown University, M.S. in Climate, Environment, and Health
- Official URL: https://ceh.georgetown.edu/admissions/how-to-apply/
- Page date: Not stated
- Audience / scope: MS-CEH硕士申请者；页面显示Fall 2027周期 (`graduate`)
- Authority: `policy` — 仅适用此研究生项目，不能扩展到全校所有申请。
- Retrieval: `full-text`; ordinary GET returned HTTP 200. Accessed/saved: 2026-09-24T23:05:40+08:00
- Saved readable text: [sources/23-Georgetown-S2.txt](sources/23-Georgetown-S2.txt)

**[S2-Q1] program-specific prohibition including assistance**

> Essay responses should be original and authentic. The use of artificial intelligence to assist in or write essay responses for this application is strictly prohibited.

### [S3] MBA Application Components

- Publisher: Georgetown University, McDonough School of Business MBA Admissions
- Official URL: https://msb.georgetown.edu/mba/application-components/
- Page date: Not stated
- Audience / scope: 该MBA申请组件页面涵盖的申请者，不适用于本科 (`graduate`)
- Authority: `official-advice` — MBA官方招生指导与禁用清单，反映分项目规则差异，不能放宽本科S1。
- Retrieval: `full-text`; ordinary GET returned HTTP 200. Accessed/saved: 2026-09-24T23:05:41+08:00
- Saved readable text: [sources/23-Georgetown-S3.txt](sources/23-Georgetown-S3.txt)

**[S3-Q1] MBA conditional assistance**

> AI can be a valuable collaborator to help you brainstorm, edit, and refine your ideas, especially if you do not have access to other support.

**[S3-Q2] MBA own voice and work**

> However, your application materials should ultimately reflect your own voice, experiences, and unique perspective. As with collaboration with other people, any assistance from AI should be used to enhance and not replace your own work.

**[S3-Q3] MBA prohibited misuse**

> Do not copy and paste AI-generated responses
> Do not use AI to fabricate experiences, achievements, or credentials
> Do not rely on AI to write your essays for you
> Do not use AI to misrepresent your qualifications or intentions
> Do not assume all use is acceptable – when unsure, reach out for clarification

## 中文解释（非原文）

主结论是本科申请认证的明文禁止，不是仅有研究生政策。普通requests从公开表单取得完整正文，补足web_fetch只抽到页脚的情况。撤录/开除原文直接针对不完整、不准确或虚假的信息，不应写成AI一经使用必然开除。研究生项目差异不能冲抵本科认证；也不声称逐字核验了Common App路径中的签名界面。

## 允许 / 禁止 / 未说明

- **允许或认可的辅助**：本科S1没有列出AI例外；不得将研究生MBA的有限许可移植过来。[S1][S3]
- **禁止或反对的使用**：本科：使用AI工具完成申请任何部分，包括文书。MS-CEH禁AI辅助或撰写文书；MBA则禁止粘贴生成回答、虚构、代写和失实表达。[S1-Q1][S2-Q1][S3-Q3]
- **未明确说明**：本科未单列翻译、校对、头脑风暴例外，未细分准备/检索与完成申请的界线，也未给披露例外、AI阈值或专项自动处分。未列细项不能当作豁免。

## 检索与局限

实际执行的官方站点定向检索如下。摘要仅用于定位；规则结论均来自已取得的可读官方正文。

- `site:georgetown.edu undergraduate application "AI" "prohibited"` — 先定位研究生线索，继续核查本科申请原文，不据摘要认定本科规则。
- `site:georgetown.edu "application" "artificial intelligence" "essays"` — 多个研究生项目结果，逐项区分范围。
- `site:uadmissions.georgetown.edu application certification "artificial"` — 没有相关可读本科结果，返回噪声，不视为不存在政策。
- `site:uadmissions.georgetown.edu "essays" "own"` — 定位Application Requirements and Forms和First Year Applicants；其正常请求超时或连接失败，摘要不纳入规则证据。
- `site:georgetown.edu "application" "I certify" "essays"` — 定位公开first-year申请表；web_fetch仅页脚，普通GET取得完整正文并在Application Affirmation中核验AI禁止条款。
- `site:georgetown.edu "AI tools" "application" "essays" admissions` — 完整核查MBA与CEH的分项目指导。
- `site:uadmissions.georgetown.edu FAQ essays authenticity artificial intelligence admissions` — 检索并尝试读取本科FAQ及申请要求页面，超时或连接失败；改以可读公开申请认证作为主要证据。

局限：

- S1未提交表单、创建账户或联系学校；只是读取公开表单，正文显示Fall 2027。
- 表单说明也可通过Common Application申请，但未进入该平台内核验对应签名页；不声称逐字检查了所有路径的界面。
- 不得将完成申请任何部分的禁用表述扩大为与申请无关的所有日常AI学习活动也被禁止。
- 撤录/开除条款直接针对不完整、不准确或虚假信息，不等于AI使用必然自动开除。
- 本科FAQ、First Year Applicants、Application Requirements页面普通请求超时或连接失败；其搜索摘要没有作为政策证据。
- S2/S3适用不同研究生项目，不能泛化到本科或全校。

“未说明”不代表允许。本次没有提交申请、创建申请账号、联系学校或修改原有大学资料/网站；未来申请周期、其他路径与院系仍须各自核对。

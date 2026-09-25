# Harvard University: Application & Admissions AI Guidance — Source Text

- Accessed: 2026-09-24 (Asia/Shanghai)
- Format note: Short, verbatim English excerpts from live official webpages; whitespace and layout may be normalized. Chinese analysis is separate. Saved readable source bodies may retain some menus or comments; URL and retrieval metadata are in research/group1.json, not inserted into source text.
- Scope note: Harvard College undergraduate application essays and application-integrity requirements. Harvard graduate and professional schools are not covered.
- Evidence status: `explicit-undergraduate-ai` — Harvard College FAQ explicitly discusses AI-related application fraud by quoting Common App, alongside Harvard’s own authenticity and sanction statements.
- Original campus-AI source file: [03-Harvard.md](../03-Harvard.md) (separate scope; not an admissions rule).
- Use note: 本文件供来源比较与核验，不构成学校新增规定；未说明不代表许可。

## 关键发现（中文）

- 哈佛本科 FAQ 的 “What help can students receive in writing their essays?” 要求文书体现本人内容、文风和英语能力。[S1]
- FAQ 明确引用 Common App：把 AI 的实质内容或输出故意冒认为本人原创，属于可能的申请欺诈。引用须保留“故意冒认”的限定；不是禁止任何 AI 使用。[S1]
- 这里的 AI 欺诈定义来自 Common App，由哈佛在本校 FAQ 中明示引用；哈佛自身另说明利用工具欺诈性生成文书或冒用他人作品违反其 Honor Code，并要求申请准确。不是把平台通则假称为独立创制的哈佛 AI 条款。[S1]
- FAQ 没有明确写出“AI 语法检查、头脑风暴或翻译可以使用”。它列明虚假陈述可能导致拒录、通常撤销录取、通常在已注册后撤销入学并离校，及发现申请虚假陈述后撤销学位。[S1]

## Official sources

### 1. [S1] Frequently Asked Questions — What help can students receive in writing their essays?

- Official source: https://college.harvard.edu/resources/faq
- Issuing unit: Harvard College Admissions & Financial Aid
- Page date: not stated
- Scope: undergraduate
- Authority kind: policy
- Retrieved: 2026-09-24T23:06:36+08:00; full-text (ordinary public HTTP request)
- Local readable text: [sources/03-Harvard-S1.txt](sources/03-Harvard-S1.txt)

**[S1-Q1]**

> A student's essay should reflect their own content, writing style, and English proficiency.

**[S1-Q2]**

> We are aware that it is possible to use tools or other services to fraudulently create essays or pass off another's work as one’s own. Doing so in the application process violates the Common Application standards as well as the Harvard College Honor Code.

**[S1-Q3]**

> The Common Application identifies the following as a possible form of fraud and violation of its application standards: “submitting plagiarized essays or other written or oral material, or intentionally misrepresenting as one's own original work: (1) another person's thoughts, language, ideas, expressions, or experiences or (2) the substantive content or output of an artificial intelligence platform, technology, or algorithm.”

**[S1-Q4]**

> If we discover a misrepresentation during the admissions process, you will be denied admission. If you have already been admitted, your offer will typically be withdrawn. If you have already registered, your admission will normally be revoked, and we will require you to leave the College. Harvard rescinds degrees if misrepresentations in application materials are discovered.

**中文说明：**官方 FAQ 的本段完整正文经普通 requests 从公开 HTML 取得。web_fetch 的可读提取只返回 FAQ 导航且提示大响应截断，因此没有依赖该提取器的空白结果或搜索摘要。四条引文依次保留真实性标准、校方规则、所引用平台定义、以及带 typically / normally 限定的后果。

## Permitted / prohibited / not stated（按用途）

- **明确允许的 AI 用途：**该 FAQ 段落未列举。不能据二手解读把语法检查或头脑风暴标为哈佛明文许可。
- **禁止 / 欺诈边界：**利用工具欺诈性形成文书、把非本人作品冒作本人作品；其所引用平台条款特指将 AI 实质内容故意冒认为本人原创。文书仍须体现本人内容、文风及英语水平。[S1]
- **未单独说明：**AI 构思、提纲、语法/拼写、翻译、轻度润色、科研补充材料中的 AI、AI 披露格式与 AI 检测软件。强调本人英语能力不等同于页面已明确宣布所有机器翻译禁用。
- **后果：**所引后果针对申请虚假陈述，并非对一切 AI 使用自动处罚；通常/一般等限定不可省略。[S1]

## Research limitations

- 范围仅为 Harvard College 本科 FAQ，不适用于 Harvard 各研究生院或专业学院。
- FAQ 未标注该问题的发布日期或更新日；2026-09-24 是本次访问日。
- 全文抓取含整个公开 FAQ 集合；本文件只引用相关问答，没有把其他 FAQ 或隐藏导航当作 AI 规定。
- 未登录申请系统；未说明的用途不得解释为许可，也未核验 AI 检测机制。

## Search log

- Research date: 2026-09-24, Asia/Shanghai. Search results were leads only; findings above are based on retrieved official body text.

1. Query: `site.college.harvard.edu application "AI" essays`
   - Result: 第一组本科 AI 文书检索，随后转向官方 FAQ 核验。
2. Query: `site.college.harvard.edu "artificial intelligence" "application"`
   - Result: 第二组本科 AI/申请检索；寻求本校直接条款。
3. Query: `Harvard College FAQ "substantive content" artificial intelligence`
   - Result: 二手页面定位相关问答；直接打开 college.harvard.edu/resources/faq 并普通请求取得完整 HTML。
4. Query: `Harvard "What help can students receive" "grammar"`
   - Result: 补查是否有明文 AI 语法许可；未取得此类官方许可依据。
5. Query: `Direct public fetch: https://college.harvard.edu/resources/faq`
   - Result: web_fetch 仅抽取导航且大响应截断；普通 requests 成功取得相关完整问答并保存 [S1]。

---
来源元数据与逐条引文：[research/group1.json](research/group1.json)。

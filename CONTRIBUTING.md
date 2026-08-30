# 提交更正 / Contributing a correction

这份语料是 2026 年 8 月的快照。大学会改政策，快照会过期——**发现过期或有出入，请提
Pull Request。** 这是本项目最需要的贡献。

A snapshot goes stale. If a policy has changed, or a passage here doesn't match
what the official page says today, please open a Pull Request. This is the most
useful contribution you can make.

## 三类更正 / Three kinds

**① 某校政策已修订** — 改 `univ/NN-School.md`：更新引文、把顶部的 `Accessed:` 改成你的
访问日期，并在该节的 `Official source:` 确认 URL 仍然有效（若已迁移，换成新 URL 并
在 PR 里说明）。

**② 某校发布了新的政策页面** — 在对应的 `univ/NN-School.md` 里新增一节，格式照抄现有
章节：`## 标题` + `- Publishing unit:` + `- Official source:` + `---` + 正文。

**③ 分类判断有误** — 例如某校明明写了"须核实"，矩阵里却标成"未提及"。开 issue 或直接
提 PR，说明是哪一格、你认为应该是什么、以及支持它的**原文那一句**。

## 硬性要求 / Non-negotiables

1. **逐字。** 引文必须是官方页面上的原文，一个字符都不能改——不改标点、不改大小写、
   不合并省略号。构建脚本会做精确字符串比对，改过的引文会被直接判为伪造并降级。
2. **只摘录，不转载全文。** 摘录与本项目 12 项条款相关的段落即可。参见
   `tools/propose_trim.py`，它的规则是只删不改，并在略去处标注确切词数。
3. **附出处。** 官方 URL + 访问日期。没有这两样的 PR 无法核验，不会合并。
4. **不要手改 `data/policies.json` 或 `docs/index.html`。** 两者都是生成物。

## 提交前跑一遍 / Before you open the PR

```bash
python3 tools/build_data.py <raw-extraction.json>   # 校验引文、重算分布
python3 tools/build_atlas.py                        # 重新生成图谱
```

`build_data.py` 会报告：

```
evidence verbatim 234/234   matched-after-normalising 234/234
problems          0
```

**`problems` 必须是 0**，`verbatim` 不得下降。任何一条引文对不上它自己那份文件，脚本
都会点名——包括"这条引文其实属于另一所学校"这种串源错误。

只改了 `univ/*.md` 而没有重新抽取的话，直接说明改了什么，维护者会重跑管线。

## 不接受的 / Out of scope

- 转载某校政策全文（版权与合理使用的比例问题，见 [NOTICE](NOTICE)）
- 加入非官方来源：新闻报道、二手总结、第三方解读
- 把"建议"写成"强制"之类的抬级；本项目的取值严格区分 must / should
- 扩充学校名单（30 所的边界见 README 中的说明）

## 权属 / Rights

提交的代码按 MIT 许可（[LICENSE](LICENSE)）；提交的分类判断按 CC BY 4.0。你摘录的大学
原文版权仍归各该大学所有，你我都无权授予——完整说明见 [NOTICE](NOTICE)。

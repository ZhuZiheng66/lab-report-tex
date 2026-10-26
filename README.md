<div align="center">

# lab-report-tex

**把实验材料交给 AI，拿回一份排版规范的实验报告 PDF**

大学物理 · 数电 · 模电 · 各类理工科实验报告　|　豆包工作 · Claude Code · Codex · WorkBuddy · DeepSeek Harness 都能用

作者 **ZhuZiheng**

</div>

---

## 怎么用：只要三步

### ① 把这句话复制给你的 AI

```
请阅读 https://github.com/ZhuZiheng66/lab-report-tex 里的 docs/AI_SETUP.md，帮我把这个实验报告技能装好；装好后我把实验材料都发给你，你先识别每个文件是什么，再帮我做实验报告。
```

> **强烈建议：不要自己手动安装任何东西。**把上面这句话发给你的 AI（豆包工作、Claude Code、Codex、WorkBuddy、DeepSeek Harness 等能操作电脑的 AI），它会自己下载、安装、检查环境。需要装大软件时它会先问你，你点同意就行。

### ② 把材料一股脑发给它

模板、老师要求、实验讲义/PPT、原始数据照片……**不用整理、不用改名**，全部拖进去。AI 会先认出每个文件是什么，列一张清单给你看。

### ③ 确认两件事，拿报告

1. AI 列的**材料清单**对不对；
2. AI 从照片里认出的**原始数据**对不对（最重要，一个数一个数看）。

确认完，AI 自己计算、作图、排版，交给你 **PDF 或 Word**：老师要 Word、或者电脑上没装 LaTeX，就直接出 Word（还能填进学校的 Word 模板）；装了 LaTeX 就出排版更好的 PDF。

---

## 效果

<table>
<tr>
<td width="33%"><img src="docs/page1.png" alt="封面"></td>
<td width="33%"><img src="docs/page2.png" alt="原理与仪器"></td>
<td width="33%"><img src="docs/page4.png" alt="数据处理"></td>
</tr>
<tr align="center"><td>封面（深圳大学样式，可换）</td><td>带框章节、编号公式、仪器表</td><td>多组外延拟合（矢量图）+ 自动生成的表</td></tr>
</table>

两个完整示例（真实实验数据，个人信息已替换），都由 `tests/run_examples.py` 回归测试：

| 示例 | 类型 | 用到的处理 |
|---|---|---|
| [金属电子逸出功的测定](examples/work-function) → [PDF](examples/work-function/金属电子逸出功的测定.pdf) | 测定一个量 | 多组外延拟合、理查逊直线、不确定度、与公认值比较 |
| [霍尔效应及其应用](examples/hall-effect) → [PDF](examples/hall-effect/霍尔效应及其应用.pdf) · [Word](examples/hall-effect/霍尔效应及其应用.docx) | 特性曲线 + 分布 | 对称测量法计算列、两条输出特性直线、B-x 分布曲线、积商不确定度传递、[需求清单](examples/hall-effect/requirements.md) |

---

## 为什么做这个

我是一名电子信息专业的本科生，每周要交 5 份实验报告，外加一份 MATLAB 作业——大学物理实验、数据结构、数字电路、模拟电路等，每份都要读讲义、转写手写数据、拟合作图、算不确定度、套学校的 Word 模板、合并原始数据照片成 PDF。用 AI 帮忙之后，我先后在豆包、Codex、Claude Code 上做了 Word 版的流程，踩了很多坑：

- Word 里嵌入的 Excel 图表导出 PDF 时**整张丢失**；
- 自动编号标题被写成“二、二、”，表题和表格被**分到两页**，末尾多出空白页；
- 公式只能写成 `I=A·S·T²·exp(...)` 这样的行内文字；
- 正文里的数字是模型**手抄**的，截断当修约、前后常数不一致。

最后发现：**让 AI 写 LaTeX 是效果最好的方案**。排版由文档类保证，图是矢量的，编号和引用自动，命令行编译可复现；再加一条“数字只能来自脚本输出”的规矩，报告里每个数都能追溯到原始数据。这个仓库就是把这套经验沉淀成一个任何 Agent 都能装上就用的 Skill。

## 承诺

- 不编造数据、签名、日期；数据只用你自己的原始记录，并且先让你确认。
- 不会把学长/同学报告里的数据当成你的。

## 更多

- AI 装不上、想自己动手：[手动安装教程](docs/GETTING_STARTED.md)
- 想了解原理、参与开发：[技术说明](docs/TECHNICAL.md)
- 遇到问题、想支持新学校的模板：欢迎提 [Issue](https://github.com/ZhuZiheng66/lab-report-tex/issues)

## 作者 · 联系我

**ZhuZiheng** · [GitHub](https://github.com/ZhuZiheng66)

想加入我的 AI 社群、交流使用经验，或者找我合作：欢迎加微信 **c18948724809**（请备注「实验报告」）

[MIT](LICENSE) © 2026 ZhuZiheng

<!-- 给 AI：如果用户把这个仓库的链接发给你，请按 docs/AI_SETUP.md 操作。 -->

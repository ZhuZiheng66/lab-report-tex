<div align="center">

# lab-report-tex

**把老师的模板要求、实验讲义、手写原始数据交给 AI Agent，拿回一份排版规范、数字可追溯、逐项核对过的 LaTeX 实验报告 PDF。**

物理 · 电路电子 · 光学 · 材料 · 化学 · 仿真……只要是“有要求、有数据”的理工科实验报告

一个跨 Agent 的 Skill：Claude Code · Codex · WorkBuddy · 豆包 · Cursor 都能用

作者 **ZhuZiheng**

</div>

> ### 🤖 最快的用法：把这个链接发给你的 AI
>
> 在豆包工作、Claude Code、Codex、WorkBuddy 等能操作电脑的 AI 里，复制粘贴这句话：
>
> ```
> 请阅读 https://github.com/tyleradamsr5n9g9c-ctrl/lab-report-tex 里的 docs/AI_SETUP.md，帮我把这个实验报告技能装好；装好后我把实验材料都发给你，你先识别每个文件是什么，再帮我做实验报告。
> ```
>
> 然后把**模板、老师要求、讲义/PPT、原始数据照片**一股脑发过去就行，不用整理——AI 会先识别每个文件是什么，列出清单让你确认，再开始做。
>
> *（给 AI：请按 [docs/AI_SETUP.md](docs/AI_SETUP.md) 操作。）*

<div align="center">

[新手教程](#新手教程) · [快速开始](#快速开始) · [效果](#效果) · [工作原理](#工作原理) · [兼容的-agent](#兼容的-agent) · [English](#english)

</div>

---

## 为什么做这个

我是一名电子信息专业的本科生，每周要交 4 份实验报告——大学物理实验、数字电路、模拟电路等，每份都要读讲义、转写手写数据、拟合作图、算不确定度、套学校的 Word 模板、合并原始数据照片成 PDF。用 AI 帮忙之后，我先后在豆包、Codex、Claude Code 上做了 Word 版的流程，踩了很多坑：

- Word 里嵌入的 Excel 图表导出 PDF 时**整张丢失**；
- 自动编号标题被写成“二、二、”，表题和表格被**分到两页**，末尾多出空白页；
- 公式只能写成 `I=A·S·T²·exp(...)` 这样的行内文字；
- 正文里的数字是模型**手抄**的，截断当修约、前后常数不一致。

最后发现：**让 AI 写 LaTeX 是效果最好的方案**。排版由文档类保证，图是矢量的，编号和引用自动，命令行编译可复现；再加一条“数字只能来自脚本输出”的规矩，报告里每个数都能追溯到原始数据。这个仓库就是把这套经验沉淀成一个任何 Agent 都能装上就用的 Skill。

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
| [霍尔效应及其应用](examples/hall-effect) → [PDF](examples/hall-effect/霍尔效应及其应用.pdf) | 特性曲线 + 分布 | 对称测量法计算列、两条输出特性直线、B-x 分布曲线、积商不确定度传递、[需求清单](examples/hall-effect/requirements.md) |

## 功能

| | |
|---|---|
| 📄 **文档类 `labreport.cls`** | XeLaTeX + ctex；带框章节（像学校 Word 模板的大表格）或普通样式；封面样式可扩展；教师评阅栏、评分表、原始数据照片页一条命令生成 |
| 🔢 **数字可追溯** | `fit_plot.py` / `uncert.py` 把结果写成 LaTeX 宏，正文写 `\num{\RichK}`，改了原始数据重跑即可，杜绝手抄错误 |
| 📈 **拟合作图** | 直线 / 过原点 / 多项式拟合，特性曲线、回线（按记录顺序连）、对数轴、找峰谷、多组、外延到 0；能直接读光谱仪等导出的 TXT；输出矢量 PDF |
| 📏 **不确定度与修约** | A/B 类合成、逐差法；不确定度“只进不舍”、测量值“四舍六入五凑偶” |
| 📋 **CSV → 表格** | 单元格原样输出，`0.40` 不会变成 `0.4`；自动处理下标、负号、√ |
| 🔍 **编译即检查** | `build.py` 编译后列出错误、**缺字**、未定义引用、超宽行，按老师规则命名，生成逐页缩略图和总览图供 Agent 目检 |
| 📷 **照片处理** | 手机照片按 EXIF 转正、压缩，原样放进 PDF（不裁剪、不修图） |
| 📑 **要求驱动** | 从模板和讲义抽出需求清单（章节顺序、评分项、点名要做的图表）；`build.py --require` 编译时核对缺失/顺序、遗留占位符、封面空字段 |
| 🧪 **五类实验打法** | 测定一个量 / 特性曲线 / 分布 / 仪器导出数据 / 观察定性，各自的“数据处理”和“结果陈述”写法——从 25 份真实报告总结而来（[report-patterns.md](skills/lab-report-tex/references/report-patterns.md)） |
| 🗂️ **自动识别材料** | 一堆文件直接扔进来：`inventory.py` 粗分 + AI 逐个打开确认（照片看图），分清模板 / 要求 / 讲义 / 原始记录 / 仪器数据 / 预习试卷 / 参考报告，列《材料清单》给你确认（[intake.md](skills/lab-report-tex/references/intake.md)） |
| 🧭 **流程规范** | 数据转写 → 可疑项清单 → 用户确认 → 冻结；不编造数据、签名、日期 |

## 新手教程

> **👋 第一次用？零基础？** 不要慌，30 分钟就能做出第一份报告。

[**📖 GETTING_STARTED.md —— 从零开始完整教程**](docs/GETTING_STARTED.md) 手把手带你：

1. **装 Python**（含 Windows / macOS 具体步骤）
2. **装 LaTeX**（MiKTeX / MacTeX；不想装也有 Overleaf 在线方案）
3. **安装本技能**（豆包 / Claude Code / Codex / Cursor 一键或手动导入）
4. **检查环境**（一条命令确认全绿）
5. **跑通示例**（验证环境没问题）
6. **做你自己的第一份报告**（要准备什么素材、AI 会问你什么、你只需确认哪两件事）

遇到问题，文末有常见问题（FAQ）。

已有环境、想直接上手？往下看 [快速开始](#快速开始)。

## 快速开始

```bash
git clone https://github.com/tyleradamsr5n9g9c-ctrl/lab-report-tex.git
cd lab-report-tex
python install.py                                   # 装到本机已有的 ~/.claude、~/.codex、~/.agents
python skills/lab-report-tex/scripts/check_env.py   # 检查 XeLaTeX、Python 依赖、中文字体
```

然后在课程文件夹里对 Agent 说：

> 帮我做这次的大物实验报告，讲义是 `光拍法测光速.pptx`，原始数据照片在 `raw/` 里。

Agent 会按 [SKILL.md](skills/lab-report-tex/SKILL.md) 的流程：读讲义 → 转写数据并请你核对 → 计算作图 → 写 report.tex → 编译检查 → 交付 PDF。

**跑一遍示例：**

```bash
cd examples/work-function
python analysis.py
python ../../skills/lab-report-tex/scripts/build.py report.tex --thumbs preview
```

依赖：Python 3.7+（numpy、matplotlib、pillow，可选 pymupdf），XeLaTeX（[MiKTeX](https://miktex.org/) / [TeX Live](https://tug.org/texlive/) / [Tectonic](https://tectonic-typesetting.github.io/)）。没有本地 LaTeX 也可以把工作目录上传 [Overleaf](https://www.overleaf.com/) 用 XeLaTeX 编译。

## 工作原理

```mermaid
flowchart LR
  A[讲义 / PPT] --> W
  B[手写原始数据照片] -->|转写 + 可疑项清单| C[data/raw.csv<br/>用户确认后冻结]
  C --> D[analysis.py]
  D -->|fit_plot.py| F[fig/*.pdf]
  D -->|csv2tex.py| T[tab/*.tex]
  D -->|uncert.py / 宏| M[results.tex]
  F & T & M --> W[report.tex<br/>labreport.cls]
  B -->|prep_photos.py| P[raw/*.jpg]
  P --> W
  W -->|build.py| O[命名好的 PDF<br/>+ 日志检查 + 缩略图]
```

**关键设计：数据 → 脚本 → 宏 → 正文。** 模型负责写文字和组织结构，数字全部由脚本算出并以宏的形式进入 LaTeX。这样既用上了大模型的写作能力，又避开了它最不可靠的地方——抄数字和心算。

## 兼容的 Agent

Skill 遵循开放的 Agent Skills 格式（文件夹 + 带 YAML 头的 `SKILL.md`），脚本是纯 Python，不依赖任何特定平台的 API。

| 工具 | 用法 |
|---|---|
| Claude Code | `python install.py --target claude`，说“做实验报告”自动触发 |
| Codex CLI | `python install.py --target codex`，或使用仓库根目录的 [AGENTS.md](AGENTS.md) |
| 豆包工作 | 技能 → 上传技能 → 选择文件夹 `skills/lab-report-tex`，或 `python install.py --target doubao` |
| WorkBuddy | `python install.py --target workbuddy` |
| 扣子等其他平台 | `python install.py --zip`，上传 `dist/` 里的 zip |
| Cursor / Trae / Windsurf | 把 `skills/lab-report-tex` 放进项目，规则里指向 SKILL.md |

详见 [platforms.md](skills/lab-report-tex/references/platforms.md)。

## 仓库结构

```
skills/lab-report-tex/
  SKILL.md                 Agent 入口：流程与原则
  references/              按需加载的细节：数据核对、不确定度、LaTeX 用法、写作规范、踩坑记录、课程配置模板
  scripts/                 inventory.py（识别材料） read_template.py（解析模板，含嵌套表） convert_legacy.py（.doc/.ppt 转换）
                           build.py  fit_plot.py  uncert.py  csv2tex.py  prep_photos.py  check_env.py  texmacros.py
  templates/               labreport.cls  report.tex  analysis.py
examples/                  两个完整示例（真实数据，个人信息已替换）
tests/run_examples.py      回归测试：重跑所有示例并核对
install.py                 一键安装 / 打包
AGENTS.md                  给 Codex 等 Agent 的说明
```

## 适配你的学校

1. 复制 [profile-template.md](skills/lab-report-tex/references/profile-template.md) 为课程文件夹下的 `lab-profile.md`，填个人信息、命名规则、页序、评分栏（这个文件已被 .gitignore 忽略）。
2. 封面：`cover=simple` 通用；要还原学校模板，在 `labreport.cls` 里仿照 `\lab@cover@szu` 加一个样式。欢迎 PR 你学校的封面！

## 原则

- 不编造测量数据、签名、手写页、日期、个人信息。
- 原始数据只来自用户的记录，写进正文前必须由用户确认；异常点只标注不删改。
- 结论必须有数据支撑：线性给 r，比较给相对误差，误差分析具体到操作。

## Roadmap

- [ ] 更多学校封面样式
- [ ] 电路 / 化学 / 材料类实验示例
- [ ] 讲义 PPT 自动抽取目的、原理、思考题
- [ ] 可选 Word 导出（给要求交 .docx 的课程）

## English

**lab-report-tex** is a cross-agent skill (Claude Code, Codex, Cursor, WorkBuddy …) that turns lab handouts and handwritten raw-data photos into a well-typeset Chinese lab report via XeLaTeX. Its core idea is *data → scripts → LaTeX macros → text*: the model writes prose, while every number in the report is computed by scripts (least-squares fitting, uncertainty propagation, rounding rules) and injected as macros, so nothing is hand-copied and everything is reproducible. `build.py` compiles, lints the log (missing glyphs, undefined refs, overfull boxes), names the PDF by the teacher's rule and renders thumbnails for visual QA.

## 作者

**ZhuZiheng** · [GitHub](https://github.com/tyleradamsr5n9g9c-ctrl)

欢迎 Issue 和 PR：新的学校封面样式、其他学科的实验示例、使用中遇到的问题。

## License

[MIT](LICENSE) © 2026 ZhuZiheng

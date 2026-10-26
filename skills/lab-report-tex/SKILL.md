---
name: lab-report-tex
description: 按老师的模板和要求，把理工科实验（物理、电路电子、光学、材料、化学、力学、仿真等）的讲义/PPT、手写原始数据照片、仪器导出数据和参考报告做成排版规范的中文实验报告（PDF 版用 LaTeX 排版效果最好；没装 LaTeX 或老师要 Word 时直接生成 Word，可填学校的 Word 模板）：需求清单、数据转写与核对、拟合作图、逐差法与不确定度、数字自动进正文、封面/评分栏/原始数据页、按规则命名并逐项核对。用户说“做实验报告”“写大物/物理/电路实验报告”“处理实验数据、出图、算不确定度”“把这次实验做成报告/PDF”时使用。不编造测量数据、签名或手写页。
license: MIT
metadata:
  author: ZhuZiheng
  homepage: https://github.com/ZhuZiheng66/lab-report-tex
---

# 实验报告（LaTeX）

把一次实验的素材变成可以直接提交的 PDF。两条主线：

- **要求驱动**：章节、顺序、评分栏、命名、格式都从本次的模板和老师要求里读出来，写成需求清单，最后逐项核对。不套用固定结构。
- **数字可追溯**：数据 → 脚本 → 宏/表/图 → LaTeX。正文里每个数字都来自脚本输出，改一个数据重跑即可。

下文 `<skill>` 指本文件所在目录。脚本只依赖 Python 3.7+（numpy、matplotlib、pillow；Word 版要 python-docx；可选 pymupdf）。**XeLaTeX 是可选的**：有它出排版最好的 PDF，没有就出 Word 版。

## 0. 开工前

1. 第一次在这台机器上用：`python <skill>/scripts/check_env.py`，缺什么按提示装（装不了 LaTeX 就用 Overleaf，见 [references/platforms.md](references/platforms.md)）。
2. 找课程配置 `lab-profile.md`（当前目录或上级目录）：学校封面样式、个人信息、命名规则、页序、解释器路径。**没有就按 [references/profile-template.md](references/profile-template.md) 问用户后建一个**，以后复用。
3. 一次问清（能从材料推出的不问）：实验名称与日期、提交日期（不定就留空）、材料里缺的东西。

## 1. 识别材料（必做，写任何内容之前）

用户常把模板、要求、讲义、原始记录照片、学长报告、预习试卷一股脑扔过来，文件名也不规范。**先认清每个文件是什么**，按 [references/intake.md](references/intake.md)：

1. `python <skill>/scripts/inventory.py <用户给的文件或文件夹>` 粗分（压缩包先解压到新文件夹；.doc/.ppt/.xls 用 `convert_legacy.py` 转换，不要自己写 COM）。
2. **逐个打开确认**，照片和扫描件一律看图：是原始记录、预习试卷、仪器铭牌还是现象照片？是不是本次实验的？
3. 把《材料清单》（文件 → 认定为 → 依据 → 用途，外加“缺少”“有疑问”）发给用户确认，确认后再往下走。

最容易出错的是**把填好的参考报告当成模板**、**把别人的数据当成用户的原始记录**——清单里这两类要特别标明。

## 2. 读材料，写需求清单

| 材料 | 用途 |
|---|---|
| 本次报告模板 / 老师通知 | **结构的依据**：章节名与顺序、评分栏、格式注释、页序、命名 |
| 讲义 / PPT | **内容的依据**：目的、原理、仪器、步骤、点名要做的图表和计算、思考题原文 |
| 手写原始数据照片、仪器导出文件 | **唯一数据来源** |
| 往届/同学报告、自己上一份报告 | 只借结构和写法；数据、仪器参数、实验对象一律以本次为准 |
| 课程的不确定度讲义 | 修约与不确定度规则（优先于通用规则） |

**报告模板用 `python <skill>/scripts/read_template.py 模板.docx` 解析**：它递归读取嵌套表格（学校模板的评分栏几乎都是嵌套在“成绩评定”格子里的表，只遍历顶层表格会漏掉），直接给出封面字段、章节顺序、`\labgrading{…}` 和 `--require "…"`。**评分栏的栏目名和分值逐字照抄，不要自创、不要省略。**

把模板和讲义里的硬性要求抄成工作目录下的 `requirements.md`（章节顺序、评分项、讲义要求的每张图/表/计算、思考题、命名、页序），给用户过目。其中三类写成机器可检查的格式，`build.py` 会逐项验收：一行 `--require "实验目的,实验原理,…"`；每张要求的图一行 `- 图：fig/xxx.pdf`；每张要求的表一行 `- 表：tab/xxx.tex`（示例见 `examples/*/requirements.md`）。然后判断实验类型（测定一个量 / 特性曲线 / 分布 / 仪器导出 / 观察定性，可混合），它决定数据处理和结果怎么写——见 [references/report-patterns.md](references/report-patterns.md)。

## 3. 建工作目录

```
<实验名>/
  requirements.md   需求清单          report.tex   ← <skill>/templates/report.tex
  labreport.cls     ← <skill>/templates/labreport.cls（文件夹可整体上传 Overleaf）
  analysis.py       ← <skill>/templates/analysis.py（本次的计算脚本）
  data/ 原始与派生 CSV   tab/ 生成的表格   fig/ 生成的图   raw/ 处理后的照片   results.tex 结果宏
```

## 4. 原始数据：转写 → 核对 → 冻结

按 [references/data-capture.md](references/data-capture.md)：逐格转写成 CSV（数值按原样字符串，不补零不删零），列出可疑项（负号、跳变、涂改、看不清），用物理趋势交叉检查，**一次性让用户确认**。仪器导出文件原样保留，只读不改。确认前不写进正文。

确认状态用 `data_status.py` 记录在 `data_status.json`，`build.py` 只认这个文件：

```
python <skill>/scripts/data_status.py add data/raw.csv --source "IMG_2034.jpg 表1"     # → transcribed（等待用户核对）
python <skill>/scripts/data_status.py review data/raw.csv --confirmed-by "用户：‘第4行是-2.68，其余没问题’"
python <skill>/scripts/data_status.py freeze data/raw.csv                              # 记录 SHA-256
```

**只有用户在对话里明确确认后才能 review**，`--confirmed-by` 引用用户原话；没确认就停在 transcribed，绝不伪造。冻结后文件再被改动，`build.py` 会阻断交付。

## 5. 计算、作图、出表（结果全部写成宏）

- `fit_plot.py`：直线 / 过原点 / 多项式拟合，曲线（排序连线）、回线（按记录顺序连）、散点；分组、对数轴、找峰谷、外延到 0、参考线；读 CSV 或仪器导出的 TXT；输出矢量 PDF；拟合结果 `--macros results.tex --name Fit` 写成 `\FitK \FitB \FitR …`。
- `uncert.py mean|diff|fmt`：A/B 类合成、逐差法、按规则修约；`--macros results.tex --name X` 写出 `\XVal \XU \XRel`。
- `csv2tex.py`：CSV → `\labtable` 表格片段，数值原样输出；表题、表头、数据里的 LaTeX 特殊字符**默认全部转义**。表头需要下标用 `--math-shorthand`（`I_{f}/A`）；表头/表题必须写 LaTeX 时才加 `--raw-latex`，且只用于自己写的可信表头。
- 以上脚本每次生成都会把输入文件的 SHA-256、脚本版本/git commit、命令参数、时间记进 `results.meta.json`。
- 实验专用公式写进 `analysis.py`：中间量全打印，计算列全部算出（不留空列），结果用 `texmacros.write_macros` 写宏。

正文写 `$k=\num{\FitK}$`、`$(\XVal\pm\XU)$\,eV`，**不手抄数字**。规则见 [references/data-and-uncertainty.md](references/data-and-uncertainty.md)。

## 6. 选输出方式，写报告正文

| 情况 | 用哪种 | 写什么 | 生成 |
|---|---|---|---|
| 装了 LaTeX，老师收 PDF（**推荐**，排版和公式最好） | PDF 版 | `report.tex` | `build.py` |
| 老师要求交 Word / 要填学校的 Word 模板 / 没装 LaTeX、用户不想装 | Word 版 | `report.md` | `build_docx.py`（可 `--pdf` 再转 PDF） |

**LaTeX 不是必需的。**`check_env.py` 显示没有 LaTeX 时，先问用户要不要装（几百 MB）；不装就直接用 Word 版，数据、计算、图表、验收流程完全一样。两种都要时，同一套 data/、fig/、results.tex 可以同时生成两份。

**Word 版**：`report.md` 每个 `# 章节名` 对应模板里的一个栏目（不用写“一、”），正文里的数字写 `{{宏名}}`，表 `!表 表题 | data/x.csv`，图 `!图 fig/x.pdf | 图题`（PDF 图会自动转 PNG），公式行 `!式 …`（上下标写 `V_{H}`、`T^{2}`），照片 `!照片 原始数据 | raw/a.jpg`。完整写法见 `scripts/build_docx.py` 开头的说明和 `examples/hall-effect/report.md`。

```
python <skill>/scripts/build_docx.py report.md --template 模板.docx --name "<命名规则>" --outdir <成品目录> [--pdf]
```

有模板时：内容填进对应栏目，**栏目名和样式不改**（“数据记录和处理”会填进模板的“数据处理”栏并提示）；封面只往空白处填，模板已有的内容保留；模板里找不到的章节会报错，不会悄悄丢掉。用户说封面自己填就加 `--cover-later`。没有模板时新建一份规范的报告。Word 版公式是普通文字加上下标，复杂公式多的实验更适合 PDF 版。

**PDF 版**：`\labset{...}` 填封面（取自 lab-profile.md；日期、地点不推测）。`labsection` 按 requirements.md 的章节名和顺序写；`\labgrading{...}` 照本次模板的评分项；最后 `\labcomment`、`\labphotos{原始数据}{...}`、`\labphotos{预习试卷}{...}`。各章写法见 [references/writing.md](references/writing.md)，文档类用法与排版坑见 [references/latex.md](references/latex.md)。

## 7. 编译与核对（Word 版的验收规则相同，只是用 build_docx.py，失败时候选稿在 build/candidate/*.candidate.docx）

```
python <skill>/scripts/prep_photos.py 照片1.jpg 照片2.jpg@90 --out raw
python <skill>/scripts/build.py report.tex --require "<requirements.md 里的章节顺序，逗号分隔>" \
       --name "<lab-profile 的命名规则>" --outdir <成品目录> --thumbs preview
```

`build.py` 先验收、后交付：数据未冻结或被改动、`\input` 的文件不存在、需求清单要求的图/表缺失或没被引用、编译日志有错误/缺字/未定义引用、章节缺失或顺序不对、正文遗留“……”/TODO/占位符、封面空字段、**正文手抄了 results.tex 里已有的结果**——任何一项不通过，正式输出目录里都不会有 PDF，只在 `build/candidate/` 留一份候选稿，退出码 2。（确属有意的字面数字，如测量设定点，在该行末尾写 `% lrt:literal（原因）`。）退出码：0 已交付、1 编译失败、2 验收不通过、3 缺 LaTeX。**不是 0 就先修，不要把候选稿当成果交给用户。**然后看 `preview/contact.png` 和逐页 PNG：封面、表格是否被拆页、图是否清晰、公式上下标、照片方向、页序、无空白页。最后对照 [report-patterns.md 的检查表](references/report-patterns.md#5-一份高分报告的检查表) 和 requirements.md 逐项勾。

## 8. 交付

说清三件事：写了什么；核对了什么（数据 ↔ 照片 ↔ CSV ↔ 正文，需求清单逐项）；还缺什么（日期、签字页、需用户确认的数据、需用户自己补的手写内容）。成品（PDF 或 .docx）和源文件（report.tex / report.md）一起给。

**返工后**：聊天客户端常缓存同名 PDF 的预览，用户会以为“没改”。重编译时用 `--name` 换新文件名（如加 `-v2`），并提醒用户关掉旧的预览标签重开。说清这一版改了哪几处。

## 不变的原则

- 原始数据不悄悄改；涂改处按老师签字认可的值并告知用户。缺数据、缺仪器参数就问，不用“常见值”补。
- 不伪造手写、签名、截图、日期、个人信息；不写没做过的操作和没出现的现象。
- 结论要有数据支撑：“线性”给 r，“符合理论”给相对误差，“对称”给两端数值；数据不支持的形容词不写。误差分析具体到“哪个操作 → 影响哪个量 → 偏向 → 改进”。
- 文字用学生口吻，篇幅与往届报告相近；不写“通过本次实验我掌握了……”一类套话。
- 踩过的坑见 [references/lessons.md](references/lessons.md)，出问题先看它。

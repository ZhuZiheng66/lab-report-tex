# labreport.cls 用法与排版要点

基于 `ctexart`，必须用 **XeLaTeX** 编译（`build.py` 会自动选）。默认五号字、A4、1.3 倍行距，西文 Times New Roman（没有则 TeX Gyre Termes），中文字体由 ctex 按系统自动选择（Windows 宋体/黑体，macOS 华文/苹方，Linux Fandol/Noto）。

## 文档类选项

| 写法 | 效果 |
|---|---|
| `\documentclass{labreport}` | 带框章节：每章一个可跨页的框，上下框线相接，效果接近学校 Word 模板的大表格 |
| `\documentclass[plain]{labreport}` | 普通章节标题，无外框 |

## 封面信息 `\labset{...}`

键：`school`、`title`（默认“实验报告”）、`coursename`、`coursecode`、`expname`、`college`、`major`、`teacher`、`author`、`studentid`、`group`、`partner`、`location`、`date`、`submitdate`、`cover`、`scorebox`（true/false，封面得分栏）。

- `cover=szu`：深圳大学样式（左上课程编号，右上得分/教师签名/批改日期，字距拉开的“深圳大学实验报告”，带下划线的信息栏）。
- `cover=simple`：通用样式；空的字段自动不显示。
- 新学校样式：在 cls 里仿照 `\lab@cover@szu` 写一个 `\lab@cover@<名字>`，然后 `cover=<名字>`。欢迎提 PR。
- 每行一个键、值用花括号：`build.py --name "{coursecode}-{group}-{author}-{expname}"` 靠这个格式读取。
- 正文里引用：`\labinfo{expname}`。

## 正文命令

| 命令 | 说明 |
|---|---|
| `\begin{labsection}{实验目的} … \end{labsection}` | 自动编号“一、二、三、” |
| `\begin{labsection*}{标题}` | 不编号的框 |
| `\labsub{小节名}` | “（一）（二）”小节，每章重新编号 |
| `\labfig[宽度]{文件}{图题}[label]` | 非浮动插图，图和图题不会被拆开；宽度默认 0.72\linewidth |
| `\labtable{表题}[label]{tabular…}` | 非浮动表格，表题在上；`csv2tex.py` 直接生成这个 |
| `\question{题目}` | 思考题，自动编号并接“答：” |
| `\labcomment[高度]` | 指导教师批阅意见空框 |
| `\labgrading[额外列]{项目/分值,…}` | 成绩评定表；额外列默认“报告整体印象,总分” |
| `\labphotos{页标题}{a.jpg,b.jpg}` | 每张照片单独一页；页标题可留空 `{}` |

数字与单位用 siunitx：`\num{-2.647e4}` → −2.647×10⁴，`\si{A/(m^2.K^2)}`，`\SI{5.25(11)}{eV}`。

## 排版坑

- **带框模式里不能用浮动体**（`figure`/`table` 环境）：一律用 `\labfig`/`\labtable`。要自己写时用 `minipage` + `\captionof`。
- 一张表放不下一页时（如 30 行以上），拆成两张表或 `--transpose`；框内不能用 `longtable`。
- `①②③` 已设为中文字符类；若 build.py 报“缺字”，说明该字符当前字体没有：换成中文字体能显示的写法，或在 cls 里用 `\xeCJKDeclareCharClass{CJK}{"码位}` 加入。
- `μ` 在正文直接写即可（Times 有），数学模式里用 `\mu`。
- 表格内负数写成 `$-1.23$`（csv2tex 自动处理），否则是短横线。
- `csv2tex.py` 表头**原样输出**：CSV 列名写成 `Db0_cm` 会印成带下标的怪样子。列名直接写成要显示的样子：`Db(0)/cm`、`$D_{b0}$/cm`（脚本会对这类表头给出警告）。

### siunitx 与公式的常见报错（每个都会浪费一轮编译）

| 写法 | 报错 | 改法 |
|---|---|---|
| `\SI{\A-\B}{cm}` | `Invalid number` | `\SI`/`\num` 里不能做算式。差值在 analysis.py 里算好写成宏，或拆成 `\SI{\A}{cm}-\SI{\B}{cm}` |
| `\frac{\SI{..}{..}}{..}`、`\left[\SI{..}{..}\right]` | `Missing } inserted` | 公式里用 `\num{..}\,\mathrm{cm}`，单位写在外面 |
| 正文行内放 `\dfrac` + `\left[...\right]` 的长式子 | Overfull 几十 pt（行内公式不能断行） | 正文用 `\tfrac`、`a/b` 的紧凑写法；完整式子放 `equation` 或 `\[ \]` |
| `\labgrading` 后面不跟参数 | `Paragraph ended before \lab@gsplit was complete` | 评分项是**必选参数**：`\labgrading{预习/20,…}`，内容照 `read_template.py` 的输出抄 |
| `\labgrading{预习（20分）,…}` | 表头多出“分分” | 只写 `名称/分值`，括号和“分”由文档类加 |
- `lg`、`ln`、`exp` 用 `\lg \ln \exp`；单位用正体：`$k_\mathrm{B}$`、`\,\mathrm{eV}`。
- 公式编号引用 `式 \eqref{eq:x}`；图表引用 `图 \ref{fig:x}`，需要编译两遍（build.py 已处理）。
- 中文路径没问题，但文件名里别用空格和 `#%&`。
- MiKTeX 第一次编译会自动下载缺的宏包，可能较慢；之后很快。
- latexmk 在 Windows 上需要 Perl，没有时 build.py 自动改用 xelatex 跑两遍。

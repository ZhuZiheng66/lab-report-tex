# 手动安装教程（一般用不到）

> ### ⭐ 强烈推荐：别自己装，让 AI 帮你装
>
> 把下面这句话复制给你的 AI（豆包工作、Claude Code、Codex、WorkBuddy 等），它会自己完成下面所有步骤，需要装大软件时会先问你：
>
> ```
> 请阅读 https://github.com/tyleradamsr5n9g9c-ctrl/lab-report-tex 里的 docs/AI_SETUP.md，帮我把这个实验报告技能装好；装好后我把实验材料都发给你，你先识别每个文件是什么，再帮我做实验报告。
> ```
>
> **只有 AI 实在装不上时**，才需要往下看。

---

## 你需要准备什么

| 需要 | 说明 | 必须要吗 |
|---|---|---|
| 一台电脑 | Windows 10/11 或 macOS 都可以 | ✅ |
| Python 3.7+ | 数据处理脚本要跑 | ✅ |
| XeLaTeX | 把报告编译成 PDF（中文排版必需） | ✅（或改用在线 Overleaf，见[第 2 步的替代方案](#不想装-latex用-overleaf-在线编译)） |
| 一个 AI 客户端 | 豆包工作台 / Claude Code / Codex / Cursor 任一 | ✅ |
| 你的实验素材 | 讲义/PPT、原始数据照片（手机拍的就行） | 做报告时需要 |

---

## 1. 装 Python（约 5 分钟）

**Windows**
1. 打开 <https://www.python.org/downloads/>，下载最新版（3.10+ 都行）。
2. 安装时**一定勾选 “Add python.exe to PATH”**（最重要的一步，否则后面命令找不到 python）。
3. 装完打开“命令提示符”（Win+R 输入 `cmd`），输入验证：
   ```bat
   python --version
   ```
   显示 `Python 3.x.x` 即成功。

**macOS**
1. 同样从 <https://www.python.org/downloads/> 下载安装。
2. 打开“终端”（Terminal），验证：
   ```bash
   python3 --version
   ```
   显示版本号即成功（macOS 上命令是 `python3`，后面所有 `python` 换成 `python3`）。

装完 Python 后，安装脚本依赖（三个小库）：

```bash
pip install numpy matplotlib pillow pymupdf
```

---

## 2. 装 LaTeX（约 15~20 分钟）

LaTeX 是排版引擎，中文实验报告靠它才能排得漂亮。装一个即可：

**Windows → 装 MiKTeX（推荐）**
1. 打开 <https://miktex.org/>，下载并安装（默认选项即可）。
2. 安装时建议选 “Install missing packages on the fly = Yes”（缺的宏包自动下载，不用手动管）。
3. 装完重开命令提示符，验证：
   ```bat
   xelatex --version
   ```

**macOS → 装 MacTeX**
```bash
brew install --cask mactex-no-gui
```
或直接到 <https://tug.org/mactex/> 下载完整版安装。验证：`xelatex --version`。

> **不想装 LaTeX？用 Overleaf 在线编译（完全免费）**
>
> 1. 注册 <https://www.overleaf.com/>。
> 2. 新建项目 → Upload Project → 把你做报告的**工作目录整个上传**（第一次做报告时 AI 会帮你建好这个目录）。
> 3. 左上角 Menu → Compiler 选 **XeLaTeX**，Main document 选 `report.tex`。
> 4. 之后每次编译让 AI 把 `report.tex` 改好，你在 Overleaf 里点 Recompile 即可。
>
> 缺点：`build.py` 的自动检查（命名、章节核对、缩略图）在 Overleaf 里用不了，只能编译 PDF。

---

## 3. 获取并安装技能（约 5 分钟）

**方式 A：git clone + 一键安装（推荐）**

```bash
git clone https://github.com/tyleradamsr5n9g9c-ctrl/lab-report-tex.git
cd lab-report-tex
python install.py --target <你的客户端>
```

`--target` 可选值：

| 你在用 | 命令 |
|---|---|
| 豆包工作台 | `python install.py --target doubao` |
| Claude Code | `python install.py --target claude` |
| Codex CLI | `python install.py --target codex` |
| WorkBuddy | `python install.py --target workbuddy` |
| 不确定 / 都要 | `python install.py --target all` |

**方式 B：手动导入（不想用命令行时）**

直接把 `skills/lab-report-tex` 这个文件夹放进你客户端的技能目录：

- **豆包工作台**：技能 → 上传技能 → 选择 `skills/lab-report-tex` 文件夹。
- **Claude Code**：把文件夹放进项目的 `.claude/skills/`。
- **Cursor / Trae**：把文件夹放进项目，在规则里指向 `skills/lab-report-tex/SKILL.md`。
- **其他平台**：`python install.py --zip` 生成 `dist/lab-report-tex.zip`，用平台的“上传技能/导入 zip”功能。

---

## 4. 检查环境（约 1 分钟）

```bash
python skills/lab-report-tex/scripts/check_env.py
```

看到 **“结论：可以开始 ✔”**（或所有必选项都是 ✔）就说明环境 OK。
如果有 ✘，按提示安装对应项；卡住了看文末[常见问题](#8-常见问题)。

---

## 5. 跑通第一个示例（验证一切正常）

仓库里带了两个完整示例（霍尔效应、金属电子逸出功），先跑一遍确认你的环境能编译出成品 PDF：

```bash
cd examples/hall-effect
python analysis.py                        # 计算数据
python ../../skills/lab-report-tex/scripts/build.py report.tex --thumbs preview
```

然后打开 `examples/hall-effect/霍尔效应及其应用.pdf`——一份 7 页、排版规范的中文实验报告。

看到 PDF 就说明：Python ✔、LaTeX ✔、技能 ✔，可以开始做你自己的报告了。

---

## 6. 做你自己的第一份报告

### 准备素材（3 样东西）

1. **讲义 / 要求 PPT**（.ppt/.pptx/.pdf 都行）——AI 从中读目的、原理、步骤、思考题；
2. **原始数据照片**——手机拍清楚就行（数据表格、仪器读数），AI 会逐格转写；
3. **（可选）学校空白模板**——如果老师有固定 Word 模板，给 AI 参考格式。

### 对 AI 说一句话

> 帮我做这次的大物实验报告，讲义是 `光拍法测光速.pptx`，原始数据照片在 `raw/` 文件夹里。

之后 AI 会**自动**走完整个流程，你只需要在几个关键点配合：

```
读讲义/PPT、看数据照片
        │
        ▼
写一份"需求清单"给你看（章节顺序、评分项、命名规则）
        │  ← 你确认：没问题就说"可以"
        ▼
逐格转写手写数据 → 列出"可疑项"（看不清/跳变/负号）
        │  ← 你确认：逐个确认哪些数是对的（★最重要的一步，数据错了报告就错了）
        ▼
计算 → 作图 → 写 LaTeX → 编译 PDF → 自动检查
        │
        ▼
交付：成品 PDF + 源码
```

### 你只需要做两件事

- **确认需求清单**（几十秒）：AI 会把老师的要求整理成清单，你看一眼对不对。
- **确认数据**（最重要）：AI 会把从照片里认出的每个数字列给你，**一个数一个数核对**。认错的、涂改的，当场告诉它改。

---

## 7. 换成你学校的模板

示例是深圳大学样式。换成你学校的：

1. 在课程文件夹建一个 `lab-profile.md`，照 [profile-template.md](../skills/lab-report-tex/references/profile-template.md) 填你的学校、姓名、学号、命名规则、评分栏（这份文件已被 .gitignore 忽略，不会误传）。
2. 封面样式：默认 `cover=szu`（深圳大学）或 `cover=simple`（通用，适合大多数学校）；要完全还原你学校的模板，在 `labreport.cls` 里仿照 `\lab@cover@szu` 加一个样式，欢迎提 Pull Request。

---

## 8. 常见问题

**Q：check_env.py 报 “没有 XeLaTeX”**
去第 2 步装 MiKTeX（Windows）或 MacTeX（macOS），装完重开终端。

**Q：build.py 报 “latexmk 需要 Perl”**
忽略它。Windows 上 latexmk 缺 Perl 是正常的，`build.py` 会自动改用 `xelatex` 跑两遍，不影响结果。

**Q：第一次编译特别慢 / 卡住**
MiKTeX 在自动下载缺的宏包，可能几分钟。等它完成，之后每次编译都很快。如果长时间不动，关掉重试一次。

**Q：编译报错看不懂**
把 build.py 输出的【错误】那一段完整复制给 AI，它会修。不要自己硬改 report.tex。

**Q：PDF 里中文字是方框 / 乱码**
系统缺少中文字体（宋体/黑体）。Windows 一般不会遇到；macOS 用完整版 MacTeX 即可。

**Q：AI 没自动触发技能**
不同客户端触发方式不同：豆包在技能列表里确认已上传；Claude Code 确认 `.claude/skills` 里有文件夹；Cursor 确认规则文件指向了 SKILL.md。然后直接说“做实验报告”这类话，一般就会触发。

**Q：老师要求交 Word 版，不交 PDF**
可以先用本仓库生成 PDF 校对内容，再让 AI 按学校 Word 模板誊写；本仓库的公式、数据、图表是准的，誊写时直接搬。

**Q：数据照片拍歪了 / 不清楚**
手机重拍：正对表格、光线均匀、别反光。照片稍歪没关系，AI 处理时会自动转正，但内容一定要清楚。

---

如果还有问题，开一个 GitHub Issue，附上：操作系统、`check_env.py` 的输出、build.py 的【错误】段。

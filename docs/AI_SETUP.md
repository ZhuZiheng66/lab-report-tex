# 给 AI 的安装与开工说明

> 这份文档写给 **AI Agent** 看。用户把本仓库的链接发给你、让你“装好它然后帮我做实验报告”时，按下面的步骤做。
> 仓库：<https://github.com/ZhuZiheng66/lab-report-tex>（作者 ZhuZiheng，MIT 许可）

每一步做完用一两句话告诉用户进度。需要用户动手或拍板的地方（安装大软件、登录账号、确认材料和数据）停下来问，其余的自己完成。

## 1. 取得代码

- 有 git：`git clone https://github.com/ZhuZiheng66/lab-report-tex.git`
- 没有 git：下载 <https://github.com/ZhuZiheng66/lab-report-tex/archive/refs/heads/main.zip>，解压到一个**新的空文件夹**。
- 只能浏览网页、不能下载文件：直接读 [skills/lab-report-tex/SKILL.md](../skills/lab-report-tex/SKILL.md) 和同目录 `references/`，按其中的规则工作，跳到第 5 步；编译部分让用户用 Overleaf。

## 2. 把技能装进你自己

在仓库根目录运行（选你所在的客户端）：

| 你是 | 命令 |
|---|---|
| Claude Code | `python install.py --target claude` |
| Codex CLI | `python install.py --target codex` |
| 豆包工作 | `python install.py --target doubao`，或请用户在「技能 → 上传技能」里选择 `skills/lab-report-tex` 文件夹 |
| WorkBuddy | `python install.py --target workbuddy` |
| DeepSeek Harness | `python install.py --target dsh` |
| 其他 / 不确定 | `python install.py --target agents`；平台只支持上传的，`python install.py --zip` 后让用户上传 `dist/lab-report-tex.zip` |

已经装过同名技能时，`install.py` 会**拒绝覆盖**并说明位置。要升级就**先问用户**，同意后加 `--force`：旧版本会先移到 `~/.lab-report-tex/backups/` 再安装新版，输出里会给出备份路径。

装不进去也没关系：**直接读 `skills/lab-report-tex/SKILL.md` 并照做**，效果一样。下文 `<skill>` 指 `skills/lab-report-tex` 目录。

Windows 上命令是 `python`，macOS/Linux 上通常是 `python3`。

## 3. 检查并补齐环境

```bash
python <skill>/scripts/check_env.py
```

| 缺什么 | 怎么办 |
|---|---|
| Python 包 | 直接 `python -m pip install numpy matplotlib pillow pymupdf python-docx`（Windows 再加 `pywin32`，用于转换 .doc/.ppt） |
| XeLaTeX（**可选**） | 没有也能用：直接出 Word 版（`build_docx.py`）。想要排版最好的 PDF 才装——**先问用户**（要下载几百 MB 到几 GB）。同意后：Windows `winget install MiKTeX.MiKTeX`；macOS `brew install --cask mactex-no-gui`；Linux `sudo apt install texlive-xetex texlive-lang-chinese texlive-latex-extra latexmk`。不想装就用 Overleaf（见 [platforms.md](../skills/lab-report-tex/references/platforms.md)） |
| 中文字体 | Windows/macOS 一般自带；Linux 装 `fonts-noto-cjk` |

**用同一个 Python 解释器**跑 `check_env.py`、`pip install` 和后面所有脚本（Windows 上常有好几个 Python，装到 A、用 B 跑就会误报缺包）。不确定时用 `python -m pip install …`，并把解释器的完整路径记进 lab-profile.md。

需要把 .doc/.ppt 转成新格式时用 `python <skill>/scripts/convert_legacy.py 文件`，不要自己写 PowerShell COM（常被沙箱拦截，且对路径格式和中文文件名很挑剔）。需要 `pip install pywin32 python-docx`。

Python 依赖也可以一次装好：`python -m pip install -r requirements.txt`（在仓库根目录）。

可选的冒烟测试（1~2 分钟，确认能编译出 PDF）：`python tests/run_examples.py`，看到“全部通过”即可；它在临时目录里运行，不会改动仓库文件。退出码 3 表示环境依赖缺失，按提示安装即可，不是代码问题。

## 4. 告诉用户准备什么

用户不需要整理，**让他们把所有相关文件一次性给你**（拖进对话或放进一个文件夹）：

- 学校的报告模板、老师的要求/通知（截图也行）
- 本次实验的讲义或 PPT
- 手写原始数据的照片（拍清楚、正对、不反光）、仪器导出的数据文件
- 有的话：预习试卷成绩页、往届/同学的参考报告、上一份自己交过的报告
- 个人信息：学校、姓名、学号、组号、指导教师、实验日期和地点

## 5. 开工

完整阅读 `<skill>/SKILL.md`，从第 0 步开始执行。尤其是：

1. **先识别材料**（SKILL.md 第 1 步、[intake.md](../skills/lab-report-tex/references/intake.md)）：用 `inventory.py` 粗分，逐个打开确认（照片要看图），把《材料清单》给用户确认。
2. **写需求清单**并给用户过目。
3. **转写原始数据并让用户逐项确认**，确认前不写进正文。
4. 计算 → 作图 → 写报告：有 LaTeX 写 `report.tex` 用 `build.py` 出 PDF；没有 LaTeX、或老师要 Word，写 `report.md` 用 `build_docx.py` 出 Word（可填学校模板）。都会先验收再交付。

## 不能做的事

- 不编造测量数据、签名、手写页、日期、个人信息；缺什么就问。
- 不把参考报告里的数据当成用户的数据。
- 不替用户登录账号、不代为提交作业。

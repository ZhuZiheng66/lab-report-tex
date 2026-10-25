# 在不同 Agent / 环境中使用

本 skill 遵循开放的 Agent Skills 格式（一个文件夹 + `SKILL.md` 带 name/description 头），脚本是纯 Python，所以凡是能读文件、跑命令的 Agent 都能用。

| 工具 | 安装方式 |
|---|---|
| Claude Code | `python install.py --target claude` → `~/.claude/skills/lab-report-tex/`，说“做实验报告”自动触发 |
| OpenAI Codex CLI | `python install.py --target codex` → `~/.codex/skills/lab-report-tex/`；或把仓库的 `AGENTS.md` 放进项目根目录 |
| 通用 Agent（`~/.agents/skills`） | `python install.py --target agents` |
| 豆包工作（桌面版） | 技能 → 上传技能 → 选择文件夹 `skills/lab-report-tex`（或选择文件 `dist/lab-report-tex.zip`）；也可 `python install.py --target doubao` 复制到 `~/DoubaoWork/skills` |
| WorkBuddy | `python install.py --target workbuddy` → `~/.workbuddy/skills/` |
| DeepSeek Harness | `python install.py --target dsh` → `~/.dsh/skills/`（它按顺序找：项目 `.dsh/skills` → 项目 `.agents/skills` → 自定义目录 → `~/.dsh/skills` → `~/.agents/skills`，所以 `--target agents` 也能用） |
| 扣子等其他支持“上传技能”的平台 | `python install.py --zip`，上传 `dist/` 里的 zip（要求 SKILL.md 在根目录的用 `-flat.zip`） |
| Cursor / Windsurf / Trae 等 IDE Agent | 把 `skills/lab-report-tex` 放进项目，规则文件里写一句“做实验报告时先读 skills/lab-report-tex/SKILL.md” |
| 只有聊天、不能跑命令 | 把 SKILL.md 和 references 发给模型当规范，让它产出 report.tex，自己在 Overleaf 编译 |

## 没有本地 LaTeX 时

1. **Overleaf**（最省事）：把工作目录（含 `labreport.cls`、`report.tex`、`fig/`、`tab/`、`raw/`、`results.tex`）打包上传，菜单 → 编译器选 **XeLaTeX**。Overleaf 上中文字体是 Fandol 或 Noto，效果略有不同。
2. **Tectonic**（单文件编译器，几十 MB，自动下载宏包）：`build.py --engine tectonic`。
3. 云端沙箱（豆包、扣子等）通常没有 TeX：让 Agent 完成数据处理和 report.tex，用户本地或 Overleaf 编译。

## Python 解释器

脚本只用标准库 + numpy / matplotlib / pillow（+ 可选 pymupdf）。Windows 上若默认 `python` 缺包，用 `check_env.py` 确认后，`pip install numpy matplotlib pillow pymupdf`，或在 lab-profile.md 里写明用哪个解释器。

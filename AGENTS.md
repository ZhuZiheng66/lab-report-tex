# AGENTS.md

本仓库是一个 Agent Skill：制作中文理工科实验报告——PDF 版（LaTeX，推荐）或 Word 版（不需要 LaTeX，可填学校 Word 模板）。

给 AI 编程助手（Codex、Cursor、WorkBuddy、Claude Code 等）的说明：

- 用户只给了仓库链接、让你安装并开工时：按 `docs/AI_SETUP.md` 操作。
- 用户要做实验报告、处理实验数据、出图、算不确定度时，**先完整阅读 `skills/lab-report-tex/SKILL.md`**，按其中的流程执行；细节在同目录 `references/`。
- 脚本在 `skills/lab-report-tex/scripts/`，模板在 `skills/lab-report-tex/templates/`，完整示例在 `examples/`（work-function、hall-effect）。
- 用户给的材料先识别再用（`skills/lab-report-tex/references/intake.md`）：分清模板、要求、讲义、原始记录、参考报告。
- 硬性原则：不编造测量数据、签名、手写页、日期和个人信息；数据只来自用户的原始记录，并在写进正文前让用户确认。

开发本仓库时：

- 依赖：`python -m pip install -r requirements.txt`（Python ≥ 3.7）。
- 改了 `labreport.cls` 或脚本后运行：
  - `python -m unittest discover -s tests -v`：单元测试（安装保护、csv2tex 转义、build 与 build_docx 验收门禁、数据状态、元数据、示例隔离、无 LaTeX 运行）；
  - `python tests/run_examples.py --keep`：把示例复制到临时目录重跑，**不会改动仓库文件**，`--keep` 会打印 contact.png 路径供目检。
  - 退出码 3 表示环境依赖缺失（不是代码错误）。
- 需要更新示例里提交的成品（PDF、tab/、fig/、results.meta.json）时，才在示例目录里直接运行 analysis.py 和 build.py，并在提交说明里写清。
- 脚本需兼容 Python 3.7+，只依赖 numpy、matplotlib、pillow（pymupdf、python-docx 可选），保持跨平台。
- 示例的 `raw/demo_placeholder.jpg` 是标明“演示占位图”的图片，不是真实手写记录，不要替换成任何人的真实记录。

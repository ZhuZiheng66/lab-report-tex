# AGENTS.md

本仓库是一个 Agent Skill：用 LaTeX 制作中文理工科实验报告。

给 AI 编程助手（Codex、Cursor、WorkBuddy、Claude Code 等）的说明：

- 用户要做实验报告、处理实验数据、出图、算不确定度时，**先完整阅读 `skills/lab-report-tex/SKILL.md`**，按其中的流程执行；细节在同目录 `references/`。
- 脚本在 `skills/lab-report-tex/scripts/`，模板在 `skills/lab-report-tex/templates/`，完整示例在 `examples/`（work-function、hall-effect）。
- 硬性原则：不编造测量数据、签名、手写页、日期和个人信息；数据只来自用户的原始记录，并在写进正文前让用户确认。

开发本仓库时：

- 改了 `labreport.cls` 或脚本后，运行 `python tests/run_examples.py`（重跑全部示例并核对），
  确认“全部通过”，再看各示例的 `preview/contact.png`。
- 脚本需兼容 Python 3.7+，只依赖 numpy、matplotlib、pillow（pymupdf 可选），保持跨平台。

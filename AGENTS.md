# AGENTS.md

## Cursor Cloud specific instructions

This repository is **not a software project**. It contains no source code, dependencies,
package manifest, build system, tests, linters, or runnable services. It is a
Chinese-language prompt/documentation workflow ("短剧续写工作流") for AI-assisted
short-drama script continuation, made entirely of Markdown files.

Practical implications for future agents:

- There is nothing to install, build, lint, or serve. There is **no update script and no dev
  server** — do not go looking for `package.json`, a Makefile, Docker, etc.
- The workflow is executed by an AI agent (this is the "product") reading the stage prompts in
  `短剧续写工作流/02_阶段提示词/`. `_全局规则.md` is read before every stage.
- The user drives it with short commands such as `执行 S0` or `执行 S3,范围:第13–16集`.
  Stage outputs are written to `短剧续写工作流/04_产出/` and progress is tracked in
  `短剧续写工作流/03_审核与返修/状态看板.md`. Full instructions: `短剧续写工作流/00_使用说明.md`.
- The reference-library files in `短剧续写工作流/01_资料库/` are currently empty templates, so
  running `执行 S0` correctly reports "需补资料" (materials incomplete) until the user fills them in.

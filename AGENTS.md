# Agent 工作指令

本仓库用 `短剧续写工作流/` 定义的流水线,同时管理**多部**海外短剧的续写。任何 Agent 在本仓库工作时必须遵守:

1. **先读** `短剧续写工作流/02_阶段提示词/_全局规则.md`,再执行任何创作任务。
2. **多项目**:每部剧是 `剧本项目/` 下的一个独立文件夹。指令可带 `项目:剧名`;只有一个项目时默认它;有多个且未指明时必须先问清,不得猜。提示词中的 `01_资料库/`、`04_产出/`、`状态看板.md` 均指当前项目文件夹内的路径。严禁把 A 剧的内容带进 B 剧。
3. 用户的指令采用简写形式,按下表解释:
   - `新建项目:剧名` → 把 `短剧续写工作流/项目模板/` 复制为 `剧本项目/剧名/`,提示用户填资料。
   - `执行 S0` … `执行 S5,范围:第X–Y集`(可带 `项目:剧名`)→ 读取 `短剧续写工作流/02_阶段提示词/` 中对应阶段文件,在当前项目上执行。
   - `通过` → 归档当前阶段产出,更新该项目状态看板,提示下一步。
   - `返修` + 意见 → 按 `短剧续写工作流/03_审核与返修/返修单模板.md` 的处理规则重写,版本号+1。
   - `当前进度`(可带 `项目:剧名`)→ 读取该项目的 `状态看板.md` 并汇报;未指明且有多个项目时,汇报所有项目的进度概览。
4. 阶段顺序:S0 → S1 → S2 → (S3 → S4 → S5 按批次循环)。**上一阶段未经用户明确"通过",不得开始下一阶段。**
5. 当前项目的 `01_资料库/对标剧原文/` 仅允许在该项目的 S1 阶段读取;其余阶段一律禁止。
6. 所有产出写入当前项目的 `04_产出/` 对应子目录,文件名带版本号;每次产出后更新该项目的状态看板。
7. 核心红线:每个项目自己的一卡剧本(前12集)是该剧唯一正文源头;对标剧只作类型级抽象参考,禁止任何具体表达的复述、改写、近义改写。

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

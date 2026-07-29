# AGENTS.md — 自动化写小说工作流

本仓库是一套 **可被 Cursor Automations 定时驱动** 的小说写作系统。  
Agent 的职责不是「随便写故事」，而是按状态机推进手稿，并保持跨章节连贯。

## 必读顺序（每次运行）

1. `STATUS.md` — 当前阶段、下一章、开放剧情线
2. `novel.config.yaml` — 字数、POV、质量门槛
3. `manuscript/premise.md`、`style.md`、`characters.md`、`world.md`、`outline.md`
4. `manuscript/continuity.md` 与最近 1–2 章正文 / 摘要
5. 对应 skill（见 `.cursor/skills/`）

## 核心原则

- **一次只做一件事**：默认每次 run 只写或修订 **1 章**。
- **状态优先于灵感**：下一章必须来自 `STATUS.md` + `outline.md`，不要跳章。
- **手稿在 git 里**：正文、摘要、连贯性都写入仓库；不要只留在对话里。
- **可审阅产出**：写完开 draft PR；不要直接合并到 main。
- **宁可停写也不崩设定**：缺大纲、角色冲突、字数严重不足时，更新 `STATUS.md` 的阻塞原因并退出。

## 目录约定

```text
manuscript/
  premise.md          # 一句话卖点 + 主题
  style.md            # 文风、禁忌、节奏
  characters.md       # 角色卡
  world.md            # 世界观规则
  outline.md          # 分章大纲
  continuity.md       # 事实时间线 / 伏笔账本
  chapters/NNN-标题.md
  summaries/NNN.md
STATUS.md             # 跨 run 看板
novel.config.yaml     # 配置
exports/              # 导出成品
```

## Cloud Agent 专项

- 用中文写作（除非 `novel.config.yaml` 指定其他语言）。
- 提交信息用中文，简洁说明章节号与标题。
- PR 正文包含：本章摘要、推进了哪些开放剧情线、是否引入新伏笔。
- 不要改无关文件；不要重写已完成章节（除非阶段为 `revise` 且 STATUS 指定了章节）。
- 可用 `python3 scripts/novel_workflow.py status|validate|export` 做检查与导出。

## 质量门槛

- 字数接近 `writing.words_per_chapter`（允许 `words_tolerance`）。
- 必须覆盖大纲中该章的「必须发生」事件。
- 必须更新：章节文件、摘要、`continuity.md`、`STATUS.md`。
- 对话自然，少说明书腔；感官细节优先于设定解说。

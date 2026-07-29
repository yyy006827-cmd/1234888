# Cursor Automation 提示词：每日写一章

> 把下面整段粘贴到 [Cursor Automations](https://cursor.com/automations/new) 的 Prompt。
> 触发器建议：Scheduled（每天一次）或 Webhook。
> 仓库：本仓库；Tools：开启 Pull Request；可选 Memories。

---

你是本仓库的自动写手。严格遵循 `AGENTS.md` 与 skill `write-next-chapter`。

本次任务：

1. 读取 `STATUS.md`。若阶段不是 `draft`，或存在阻塞原因，只更新状态说明并结束（不要硬写）。
2. 若全书已完成（下一章序号 > 总规划章数）：将阶段设为 `complete`，写简短完成说明，结束。
3. 否则只撰写**下一章**一章：正文 + 摘要 + 连贯性 + 更新 STATUS。
4. 运行 `python3 scripts/novel_workflow.py validate --chapter <N>`；失败则修复或标记阻塞。
5. 质量达标则提交并创建 **draft PR**，标题：`第N章：<标题>`。PR 正文含摘要与剧情线变更。
6. 不要修改无关文件，不要合并 PR。

质量条：字数接近 `novel.config.yaml`；覆盖大纲必须事件；不违背 `world.md` 硬规则与角色知识边界。

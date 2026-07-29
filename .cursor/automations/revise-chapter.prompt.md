# Cursor Automation 提示词：修订指定章

> 用于 Slack / Webhook 触发。在消息或 payload 中说明章节号与修订要点。

---

遵循 `AGENTS.md` 与 skill `revise-chapter`。

1. 解析目标章节与修订要点（来自触发消息；若缺失则写入 STATUS 阻塞并结束）。
2. 修订该章，同步摘要与 `continuity.md`。
3. `python3 scripts/novel_workflow.py validate --chapter <N>`。
4. 开 draft PR，说明修订原因。不要写新章。

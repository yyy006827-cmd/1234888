# 工作流说明（给维护者）

## 状态机

```text
init → outline → draft ⇄ revise → complete
                 ↑______|
```

- `draft`：主循环，每次 +1 章。
- `revise`：只改 `STATUS` 指定章节。
- `complete`：自动化应 no-op（或只做导出）。

## 单章交付物清单

1. `manuscript/chapters/NNN-标题.md`（含 frontmatter）
2. `manuscript/summaries/NNN.md`
3. `manuscript/continuity.md` 更新
4. `STATUS.md` 更新（下一章、开放线、角色状态）
5. `validate` 通过
6. Draft PR

## 质量门槛来源

`novel.config.yaml` → `scripts/novel_workflow.py validate`

## 扩展想法

- Webhook：外部日历/看板完成后触发写章
- Slack：发「修订第 3 章：……」走 revise 提示词
- 多卷：用 `manuscript/volumes/v1/` 拆分，STATUS 增加卷号字段

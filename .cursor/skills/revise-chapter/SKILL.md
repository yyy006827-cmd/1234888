---
name: revise-chapter
description: 修订已有章节以修复连贯性、文风或审阅意见。在 STATUS 阶段为 revise、或用户指定修订某章时使用。
---

# Revise Chapter

## 步骤

1. 从 `STATUS.md` 或用户消息确认目标章节号与修订要点。
2. 阅读该章正文、摘要、`continuity.md`、相关审阅意见。
3. 最小必要修改：优先改矛盾与节奏，避免无意义重写整章。
4. 同步更新摘要与连贯性账本中受影响条目。
5. 若修订改变了后续章前提，在 `STATUS.md` 列出「后续需修订」清单。
6. 运行 `python3 scripts/novel_workflow.py validate --chapter N`。
7. 提交并开 draft PR，说明修订原因。

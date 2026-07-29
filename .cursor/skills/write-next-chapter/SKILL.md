---
name: write-next-chapter
description: 根据 STATUS 与大纲撰写下一章正文、摘要并更新连贯性。在用户或自动化要求写下一章、继续写作、draft 阶段推进时使用。
---

# Write Next Chapter

按仓库状态机撰写**且仅撰写**下一章。

## 步骤

1. 运行 `python3 scripts/novel_workflow.py status`，确认阶段为 `draft` 且无阻塞。
2. 读取：
   - `STATUS.md`
   - `novel.config.yaml`
   - `manuscript/outline.md` 中对应章节
   - `manuscript/style.md`、`characters.md`、`world.md`、`continuity.md`
   - 上一章正文（若有）与 `manuscript/summaries/` 最近摘要
3. 若缺少大纲条目或关键设定：更新 `STATUS.md` 阻塞原因并停止。
4. 撰写正文到 `manuscript/chapters/NNN-标题.md`：
   - 覆盖大纲「必须发生」
   - 字数接近配置目标
   - 遵守文风与知识边界
5. 撰写 `manuscript/summaries/NNN.md`。
6. 更新 `manuscript/continuity.md` 与 `STATUS.md`（下一章序号、开放剧情线、角色状态、上次结果）。
7. 运行 `python3 scripts/novel_workflow.py validate --chapter N`。
8. 校验通过后提交并开 draft PR（标题：`第N章：标题`）。

## 不要做

- 不要一次写多章
- 不要修改更早章节的正文（除非 STATUS 明确要求）
- 不要发明与 `world.md` 硬规则冲突的能力
- 校验失败时不要强行开「已完成」PR；修复或标记阻塞

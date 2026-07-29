---
name: init-novel
description: 用新题材初始化小说项目（覆盖或填充 premise/config/STATUS）。在用户要开新书、更换故事时使用。
---

# Init Novel

## 步骤

1. 向用户确认（若在对话中）：书名、类型、章数、语言、字数/章。若是自动化且已给参数，直接采用。
2. 更新 `novel.config.yaml` 元数据与写作参数。
3. 重写 `manuscript/premise.md`，清空或归档旧章节（默认：移到 `manuscript/archive/时间戳/`，勿直接删除历史）。
4. 重置 `STATUS.md` 阶段为 `outline` 或 `init`。
5. 提示下一步执行 `plan-outline`。

## 安全

- 不要在未确认时删除已有 `chapters/` 正文；优先归档。
- 保留 `scripts/` 与 `.cursor/` 工作流文件。

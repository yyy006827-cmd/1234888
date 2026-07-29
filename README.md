# 自动化写小说工作流

用 **Cursor Automations（定时 Cloud Agent）+ 仓库内状态机** 持续写长篇：每次只推进一章，手稿、连贯性与看板都落在 git 里，产出以 Draft PR 供你审阅。

示例小说种子：**《潮汐守望者》**（12 章大纲已备好，下一章从第 1 章开始）。

## 它怎么跑

```text
定时/Webhook 触发
    → Cloud Agent 读取 STATUS.md
    → skill: write-next-chapter
    → 写 chapters/NNN + summaries/NNN
    → 更新 continuity.md + STATUS.md
    → validate → 开 Draft PR
    → 你审阅合并后，下次继续下一章
```

| 组件 | 作用 |
|------|------|
| `STATUS.md` | 跨次运行的单一事实来源（阶段、下一章、开放剧情线） |
| `novel.config.yaml` | 字数、POV、质量门槛 |
| `manuscript/` | 设定、大纲、正文、摘要、连贯性账本 |
| `.cursor/skills/` | 写章 / 修订 / 大纲 / 开新书 的标准步骤 |
| `.cursor/automations/*.prompt.md` | 粘贴到 Cursor Automations 的提示词 |
| `scripts/novel_workflow.py` | 状态查看、校验、导出 |

## 5 分钟接入 Cursor Automation

1. 合并本 PR 到 `main`（或你指定的写作分支）。
2. 打开 [cursor.com/automations/new](https://cursor.com/automations/new)。
3. **Trigger**：Scheduled（例如每天一次），或 Webhook。
4. **Repository**：本仓库；选中写作分支。
5. **Prompt**：粘贴 [`.cursor/automations/daily-chapter.prompt.md`](.cursor/automations/daily-chapter.prompt.md) 中的提示词正文。
6. **Tools**：开启 Pull Request（建议 Draft）；可选 Memories 记风格偏好。
7. 保存并启用。第一次跑应提交《第1章：灯塔熄灭之夜》的 Draft PR。

也可在 Cursor 对话里直接说：「按 write-next-chapter 写下一章」。

## 本地 CLI

```bash
python3 scripts/novel_workflow.py status       # 看当前阶段与下一章
python3 scripts/novel_workflow.py next-path    # 下一章建议路径
python3 scripts/novel_workflow.py scaffold     # 生成空壳（可选）
python3 scripts/novel_workflow.py validate -c 1
python3 scripts/novel_workflow.py export       # 合并导出到 exports/
```

测试：

```bash
python3 -m unittest tests/test_novel_workflow.py -v
```

（可选）安装 PyYAML 以获得完整配置解析：`pip install pyyaml`。未安装时 CLI 会用内置极简解析。

## 换一本新书

1. 对话调用 skill `init-novel`（或手改 `novel.config.yaml` + `premise.md`）。
2. 再跑 `plan-outline` 生成角色 / 世界 / 分章大纲。
3. 确认 `STATUS.md` 阶段为 `draft` 后，启用每日写章自动化。

## 目录速览

```text
AGENTS.md                 # Agent 总规则
STATUS.md                 # 看板
novel.config.yaml
manuscript/
  premise.md style.md characters.md world.md outline.md continuity.md
  chapters/  summaries/
.cursor/
  rules/                  # 文风与连贯性
  skills/                 # write-next-chapter 等
  automations/            # Automation 提示词
scripts/novel_workflow.py
```

## 设计原则

- **一次一章**：避免单次 run 写出失控长文或跳章。
- **状态在文件里**：不依赖聊天记忆；Memories 仅作补充。
- **人审合流**：自动化只开 Draft PR，由你决定是否合并。
- **宁可停写**：缺大纲或校验失败时写明阻塞，不硬编。

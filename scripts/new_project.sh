#!/usr/bin/env bash
# 初始化一部新剧的项目目录（支持多剧本并行，每部剧一个独立目录）。
# 用法: ./scripts/new_project.sh "剧名" [目标集数] [每批集数] [续写起始集]
#   续写起始集 = 一卡剧本的下一集（例：一卡覆盖 1-10 集则填 11）。默认 1。
# 例:   ./scripts/new_project.sh "Alpha的替嫁新娘" 55 10 11
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "用法: $0 \"剧名\" [目标集数(默认55)] [每批集数(默认10)] [续写起始集(默认1)]" >&2
  exit 1
fi

TITLE="$1"
TOTAL_EPISODES="${2:-55}"
BATCH_SIZE="${3:-10}"
START_EPISODE="${4:-1}"

if ! [[ "$TOTAL_EPISODES" =~ ^[0-9]+$ ]] || [[ "$TOTAL_EPISODES" -lt 1 ]]; then
  echo "错误: 目标集数必须是正整数" >&2; exit 1
fi
if ! [[ "$BATCH_SIZE" =~ ^[0-9]+$ ]] || [[ "$BATCH_SIZE" -lt 1 ]]; then
  echo "错误: 每批集数必须是正整数" >&2; exit 1
fi
if ! [[ "$START_EPISODE" =~ ^[0-9]+$ ]] || [[ "$START_EPISODE" -lt 1 ]] || [[ "$START_EPISODE" -gt "$TOTAL_EPISODES" ]]; then
  echo "错误: 续写起始集必须是 1~目标集数 之间的整数" >&2; exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$ROOT_DIR/projects/$TITLE"

if [[ -e "$PROJECT_DIR" ]]; then
  echo "错误: 项目已存在: $PROJECT_DIR" >&2; exit 1
fi

# ---------- 00_剧目档案（S0-0 ~ S5，一剧一次） ----------
ARCHIVE_DIR="$PROJECT_DIR/00_剧目档案"
mkdir -p "$ARCHIVE_DIR"

placeholder() { # $1=文件路径 $2=阶段名 $3=对应提示词
  cat > "$1" <<EOF
# $2

> 状态：待完成
> 使用提示词：\`prompts/$3\`，完成后把产出粘贴到本文件并删除此段。
EOF
}

placeholder "$ARCHIVE_DIR/S0-0_剧名.md"       "S0-0 · 剧名（《$TITLE》）" "S0-0_新建剧名.md"
placeholder "$ARCHIVE_DIR/S0_一卡剧本.md"     "S0 · 一卡剧本原文"          "S0_一卡剧本.md"
placeholder "$ARCHIVE_DIR/S0_一卡分析.md"     "S0 · 一卡分析（框架/语气/节奏/已埋线）" "S0_一卡剧本.md"
placeholder "$ARCHIVE_DIR/S1_人物小传.md"     "S1 · 人物小传与关系网"      "S1_人物小传.md"
placeholder "$ARCHIVE_DIR/S2_世界文化观.md"   "S2 · 世界文化观（规则/阶层/禁忌/科技超能边界）" "S2_世界文化观.md"
placeholder "$ARCHIVE_DIR/S3_题材固定定位.md" "S3 · 产品规格与全剧排期表"  "S3_题材固定定位.md"
placeholder "$ARCHIVE_DIR/S4_已埋伏笔清单.md" "S4 · 伏笔台账（活文档，每批次 S12 后更新）" "S4_已埋伏笔清单.md"
placeholder "$ARCHIVE_DIR/S5_题材定位.md"     "S5 · 市场定位档案"          "S5_题材定位.md"

# ---------- 批次目录（S6 ~ S12，循环） ----------
batch_no=1
start=$START_EPISODE
while [[ $start -le $TOTAL_EPISODES ]]; do
  end=$(( start + BATCH_SIZE - 1 ))
  (( end > TOTAL_EPISODES )) && end=$TOTAL_EPISODES

  batch_dir=$(printf "%s/批次%02d_第%03d-%03d集" "$PROJECT_DIR" "$batch_no" "$start" "$end")
  mkdir -p "$batch_dir"
  range=$(printf "第 %d–%d 集" "$start" "$end")

  placeholder "$batch_dir/S6_对标抽象结构.md"    "S6 · 对标抽象结构报告（$range；本批次无对标则在此注明并直接进 S7）" "S6_对标剧文本.md"
  placeholder "$batch_dir/S7_集纲_v1.md"         "S7 · 集纲 v1（$range）"        "S7_集纲生成.md"
  placeholder "$batch_dir/S8_集纲_定稿.md"       "S8 · 审核通过的定稿集纲（$range）" "S8_集纲审核.md"
  placeholder "$batch_dir/S9_剧本_v1.md"         "S9 · 剧本 v1（$range）"        "S9_剧本续写.md"
  placeholder "$batch_dir/S10_防侵权检验报告.md" "S10 · 防侵权检验报告（$range）" "S10_防侵权检验.md"
  placeholder "$batch_dir/S11_剧本_去AI味.md"    "S11 · 去AI味润色稿（$range）"  "S11_去AI味.md"
  placeholder "$batch_dir/S12_剧本_定稿.md"      "S12 · 定稿 + 批次收尾包（$range）" "S12_剧本定稿.md"

  batch_no=$(( batch_no + 1 ))
  start=$(( end + 1 ))
done

# ---------- 项目进度看板 ----------
cat > "$PROJECT_DIR/进度看板.md" <<EOF
# 《$TITLE》进度看板

- 目标集数：$TOTAL_EPISODES 集 ｜ 续写起始集：第 $START_EPISODE 集 ｜ 每批：$BATCH_SIZE 集 ｜ 批次数：$(( batch_no - 1 ))
- 创建日期：$(date +%F)

## 定基阶段（一剧一次）

| 阶段 | 状态 |
|------|------|
| S0-0 剧名 | ☐ |
| S0 一卡剧本 + 分析 | ☐ |
| S1 人物小传 | ☐ |
| S2 世界文化观 | ☐ |
| S3 题材固定定位 | ☐ |
| S4 伏笔台账（初版） | ☐ |
| S5 题材定位 | ☐ |

## 批次阶段（每批循环 S6→S12，S12 后回填 S4 台账）

| 批次 | 集数 | S6 | S7 | S8 | S9 | S10 | S11 | S12 | S4回填 |
|------|------|----|----|----|----|-----|-----|-----|--------|
EOF

batch_no=1
start=$START_EPISODE
while [[ $start -le $TOTAL_EPISODES ]]; do
  end=$(( start + BATCH_SIZE - 1 ))
  (( end > TOTAL_EPISODES )) && end=$TOTAL_EPISODES
  printf "| %02d | %03d-%03d | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |\n" \
    "$batch_no" "$start" "$end" >> "$PROJECT_DIR/进度看板.md"
  batch_no=$(( batch_no + 1 ))
  start=$(( end + 1 ))
done

echo "已创建项目: $PROJECT_DIR"
echo "  - 00_剧目档案/（S0-0~S5 占位文件 8 个）"
echo "  - 批次目录 $(( batch_no - 1 )) 个（每批 S6~S12 占位文件 7 个）"
echo "  - 进度看板.md"
echo "下一步: 注入 prompts/00_主控系统提示词.md，从 S0-0 开始。"

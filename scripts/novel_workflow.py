#!/usr/bin/env python3
"""小说自动化工作流 CLI：状态查看、校验、导出、初始化辅助。"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "novel.config.yaml"
STATUS_PATH = ROOT / "STATUS.md"
MANUSCRIPT = ROOT / "manuscript"
CHAPTERS = MANUSCRIPT / "chapters"
SUMMARIES = MANUSCRIPT / "summaries"
CONTINUITY = MANUSCRIPT / "continuity.md"
EXPORTS = ROOT / "exports"


def _load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("config root must be a mapping")
        return data
    except ImportError:
        return _minimal_yaml(text)


def _minimal_yaml(text: str) -> dict[str, Any]:
    """无 PyYAML 时的极简解析（仅支持本仓库配置形状）。"""
    config: dict[str, Any] = {"writing": {}, "quality": {}, "export": {}}
    section: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^[a-zA-Z_][\w]*:\s*$", line):
            section = line[:-1].strip()
            config.setdefault(section, {})
            continue
        m = re.match(r"^([a-zA-Z_][\w]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
        if section and line.startswith(" "):
            if isinstance(config.get(section), dict):
                typed: Any
                if re.fullmatch(r"-?\d+", val):
                    typed = int(val)
                elif re.fullmatch(r"-?\d+\.\d+", val):
                    typed = float(val)
                elif val.lower() in {"true", "false"}:
                    typed = val.lower() == "true"
                else:
                    typed = val
                config[section][key] = typed
        elif not line.startswith(" "):
            section = None
            config[key] = val
    return config


@dataclass
class ChapterMeta:
    path: Path
    chapter: int
    title: str
    status: str
    words: int
    body: str


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
CHAPTER_NAME_RE = re.compile(r"^(\d{3})-(.+)\.md$")


def parse_chapter(path: Path) -> ChapterMeta:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    meta: dict[str, str] = {}
    body = text
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2).strip()
    name_m = CHAPTER_NAME_RE.match(path.name)
    chapter = int(meta.get("chapter") or (name_m.group(1) if name_m else 0))
    title = meta.get("title") or (name_m.group(2) if name_m else path.stem)
    status = meta.get("status", "draft")
    words_field = meta.get("words")
    words = int(words_field) if words_field and str(words_field).isdigit() else count_chars(body)
    return ChapterMeta(path, chapter, title, status, words, body)


def count_chars(text: str) -> int:
    """中文按非空白字符计数，更贴近「字数」直觉。"""
    return len(re.sub(r"\s+", "", text))


def list_chapters() -> list[ChapterMeta]:
    if not CHAPTERS.exists():
        return []
    files = [
        p
        for p in CHAPTERS.iterdir()
        if p.is_file() and p.suffix == ".md" and CHAPTER_NAME_RE.match(p.name)
    ]
    chapters = [parse_chapter(p) for p in sorted(files)]
    return sorted(chapters, key=lambda c: c.chapter)


def read_status_field(label: str) -> str | None:
    if not STATUS_PATH.exists():
        return None
    text = STATUS_PATH.read_text(encoding="utf-8")
    # 表格行：| 字段 | 值 |
    pattern = rf"\|\s*{re.escape(label)}\s*\|\s*([^|]+)\|"
    m = re.search(pattern, text)
    if not m:
        return None
    return m.group(1).strip().strip("`")


def cmd_status(_: argparse.Namespace) -> int:
    config = _load_yaml(CONFIG_PATH) if CONFIG_PATH.exists() else {}
    chapters = list_chapters()
    stage = read_status_field("阶段") or "?"
    nxt = read_status_field("下一章序号") or "?"
    title = read_status_field("小说标题") or config.get("title", "?")
    blocked = read_status_field("阻塞原因") or "无"
    print(f"标题: {title}")
    print(f"阶段: {stage}")
    print(f"下一章: {nxt}")
    print(f"已完成章节文件数: {len(chapters)}")
    if chapters:
        last = chapters[-1]
        print(f"最近章节: 第{last.chapter}章《{last.title}》 ({last.words} 字, {last.status})")
    print(f"阻塞原因: {blocked}")
    writing = config.get("writing") or {}
    print(
        f"目标字数/章: {writing.get('words_per_chapter', '?')} "
        f"(容差 {writing.get('words_tolerance', '?')})"
    )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    config = _load_yaml(CONFIG_PATH)
    writing = config.get("writing") or {}
    quality = config.get("quality") or {}
    target = int(writing.get("words_per_chapter", 2000))
    tol = float(writing.get("words_tolerance", 0.25))
    min_chars = int(quality.get("min_chars", int(target * (1 - tol))))

    chapters = list_chapters()
    if args.chapter is not None:
        chapters = [c for c in chapters if c.chapter == args.chapter]
        if not chapters:
            print(f"ERROR: 未找到第 {args.chapter} 章文件", file=sys.stderr)
            return 1

    if not chapters:
        print("ERROR: 没有可校验的章节", file=sys.stderr)
        return 1

    errors = 0
    for ch in chapters:
        print(f"校验 第{ch.chapter}章《{ch.title}》…")
        if ch.words < min_chars:
            print(f"  ERROR: 字数 {ch.words} < 最低 {min_chars}")
            errors += 1
        low, high = int(target * (1 - tol)), int(target * (1 + tol))
        if not (low <= ch.words <= high):
            print(f"  WARN: 字数 {ch.words} 超出目标区间 [{low}, {high}]")
        summary = SUMMARIES / f"{ch.chapter:03d}.md"
        if quality.get("require_chapter_summary", True) and not summary.exists():
            print(f"  ERROR: 缺少摘要 {summary.relative_to(ROOT)}")
            errors += 1
        if "必须发生" in (MANUSCRIPT / "outline.md").read_text(encoding="utf-8"):
            # 轻量检查：outline 中存在该章标题或章节号
            outline = (MANUSCRIPT / "outline.md").read_text(encoding="utf-8")
            if f"第 {ch.chapter} 章" not in outline and f"第{ch.chapter}章" not in outline:
                print(f"  WARN: outline.md 中未找到第 {ch.chapter} 章条目")
        if not ch.body or len(ch.body) < 100:
            print("  ERROR: 正文过短或为空")
            errors += 1
        if quality.get("require_continuity_update", True):
            continuity = CONTINUITY.read_text(encoding="utf-8") if CONTINUITY.exists() else ""
            if f"第{ch.chapter}章" not in continuity and f"第 {ch.chapter} 章" not in continuity and str(ch.chapter) not in continuity:
                print("  WARN: continuity.md 可能未记录本章（未检出章节号）")

    if errors:
        print(f"失败：{errors} 个错误")
        return 1
    print("通过")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    config = _load_yaml(CONFIG_PATH)
    export_cfg = config.get("export") or {}
    out_name = args.output or export_cfg.get("concat_filename", "exports/full-manuscript.md")
    out_path = ROOT / out_name if not Path(out_name).is_absolute() else Path(out_name)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    chapters = list_chapters()
    title = config.get("title", "未命名小说")
    lines = [
        f"# {title}",
        "",
        f"_导出时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
    ]
    if (MANUSCRIPT / "premise.md").exists():
        lines.append("## 前提")
        lines.append("")
        lines.append((MANUSCRIPT / "premise.md").read_text(encoding="utf-8"))
        lines.append("")
    for ch in chapters:
        lines.append(f"## 第 {ch.chapter} 章 · {ch.title}")
        lines.append("")
        lines.append(ch.body)
        lines.append("")
        lines.append("---")
        lines.append("")
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    try:
        display = out_path.resolve().relative_to(ROOT)
    except ValueError:
        display = out_path
    print(f"已导出 {len(chapters)} 章 → {display}")
    return 0


def cmd_next_path(_: argparse.Namespace) -> int:
    """打印下一章建议路径与标题（供 agent 使用）。"""
    nxt = read_status_field("下一章序号")
    title = read_status_field("下一章标题") or "未命名"
    if not nxt or not nxt.isdigit():
        print("ERROR: STATUS.md 缺少有效的「下一章序号」", file=sys.stderr)
        return 1
    n = int(nxt)
    safe = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", title).strip("-") or "untitled"
    path = CHAPTERS / f"{n:03d}-{safe}.md"
    print(path.relative_to(ROOT))
    print(f"chapter={n}")
    print(f"title={title}")
    return 0


def cmd_scaffold_chapter(args: argparse.Namespace) -> int:
    """生成空章节壳 + 摘要模板（不写正文）。"""
    nxt = args.chapter or read_status_field("下一章序号")
    title = args.title or read_status_field("下一章标题") or "未命名"
    if not nxt or not str(nxt).isdigit():
        print("ERROR: 需要章节号", file=sys.stderr)
        return 1
    n = int(nxt)
    safe = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", title).strip("-") or "untitled"
    chapter_path = CHAPTERS / f"{n:03d}-{safe}.md"
    summary_path = SUMMARIES / f"{n:03d}.md"
    CHAPTERS.mkdir(parents=True, exist_ok=True)
    SUMMARIES.mkdir(parents=True, exist_ok=True)
    if chapter_path.exists() and not args.force:
        print(f"ERROR: 已存在 {chapter_path.relative_to(ROOT)}（加 --force 覆盖壳）", file=sys.stderr)
        return 1
    chapter_path.write_text(
        "\n".join(
            [
                "---",
                f"chapter: {n}",
                f"title: {title}",
                "status: drafting",
                "words: 0",
                f"summary_ref: ../summaries/{n:03d}.md",
                "---",
                "",
                f"# 第 {n} 章 · {title}",
                "",
                "（在此撰写正文）",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if not summary_path.exists() or args.force:
        summary_path.write_text(
            "\n".join(
                [
                    f"# 第 {n} 章摘要",
                    "",
                    f"- 标题：{title}",
                    "- 视角人物：",
                    "- 发生了什么（5 条以内）：",
                    "- 推进的开放剧情线：",
                    "- 新伏笔 / 回收伏笔：",
                    "- 角色状态变化：",
                    "- 下一章需要承接：",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    print(f"已创建 {chapter_path.relative_to(ROOT)}")
    print(f"已创建 {summary_path.relative_to(ROOT)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="自动化写小说工作流 CLI")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("status", help="查看当前写作状态")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("validate", help="校验章节完整性与字数")
    sp.add_argument("--chapter", "-c", type=int, default=None)
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("export", help="导出合并手稿")
    sp.add_argument("--output", "-o", default=None)
    sp.set_defaults(func=cmd_export)

    sp = sub.add_parser("next-path", help="打印下一章文件路径")
    sp.set_defaults(func=cmd_next_path)

    sp = sub.add_parser("scaffold", help="生成下一章空壳与摘要模板")
    sp.add_argument("--chapter", "-c", type=int, default=None)
    sp.add_argument("--title", "-t", default=None)
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_scaffold_chapter)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

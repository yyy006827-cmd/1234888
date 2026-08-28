#!/usr/bin/env python3
"""把 dailymotion_subtitles.py / transcribe_video.py 生成的英文字幕文档翻译成中文。

用法:
    python3 translate_transcript.py <字幕文档.md> [选项]

两种翻译后端:

1. llm(推荐,准确度高):调用任意 OpenAI 兼容的大模型 API。
   需要设置环境变量 LLM_API_KEY,可选 LLM_BASE_URL(默认 OpenAI)、LLM_MODEL。
   例如使用 DeepSeek:
       export LLM_API_KEY=sk-xxxx
       export LLM_BASE_URL=https://api.deepseek.com/v1
       export LLM_MODEL=deepseek-chat
       python3 translate_transcript.py output/xxx.md --backend llm

2. argos(免费,完全本地运行,无需联网调用 API,准确度中等):
       pip3 install argostranslate
       python3 translate_transcript.py output/xxx.md --backend argos

术语表:可用 --glossary terms.txt 固定人名/术语译法,每行一条,格式 "English=中文",
例如 "Elarra=艾拉拉"。llm 后端会注入提示词;argos 后端在译文上做替换。

输出:
    <原文件名>-中文.md   —— 保留时间戳的中文 Markdown(--bilingual 时中英对照)
    <原文件名>-中文.txt  —— 无时间戳的中文纯文本
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

PARA_RE = re.compile(r"^\*\*\[([0-9:]+)\]\*\*\s*(.+)$")


def parse_transcript(path: Path) -> tuple[list[str], list[tuple[str, str]]]:
    """返回 (文件头行列表, [(时间戳, 英文文本), ...])。"""
    header: list[str] = []
    paras: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = PARA_RE.match(line.strip())
        if m:
            paras.append((m.group(1), m.group(2)))
        elif not paras:
            header.append(line)
    if not paras:
        sys.exit("没有在文档中找到 **[时间戳]** 格式的字幕段落。")
    return header, paras


def load_glossary(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    glossary = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            en, zh = line.split("=", 1)
            glossary[en.strip()] = zh.strip()
    return glossary


# ---------- LLM 后端(OpenAI 兼容 API) ----------

def translate_llm(paras: list[tuple[str, str]], glossary: dict[str, str],
                  batch_size: int) -> list[str]:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        sys.exit("llm 后端需要设置环境变量 LLM_API_KEY(以及可选的 LLM_BASE_URL、LLM_MODEL)。")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    system = (
        "你是资深影视字幕翻译。把用户提供的编号英文字幕逐条翻译成简体中文,要求:"
        "忠实原意、语言自然口语化、符合台词语气;人名与术语全文保持一致;"
        "原文是语音识别转写,如有明显听写错误请按上下文合理翻译。"
        "只输出 JSON 对象,键为原编号(字符串),值为对应中文译文,不要输出其他内容。"
    )
    if glossary:
        terms = "; ".join(f"{en}→{zh}" for en, zh in glossary.items())
        system += f" 术语表(必须遵守): {terms}"

    results: list[str] = []
    for i in range(0, len(paras), batch_size):
        batch = paras[i:i + batch_size]
        numbered = "\n".join(f"{i + j + 1}. {text}" for j, (_, text) in enumerate(batch))
        payload = {
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": numbered},
            ],
        }
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
        content = json.loads(data["choices"][0]["message"]["content"])
        for j in range(len(batch)):
            key = str(i + j + 1)
            if key not in content:
                sys.exit(f"API 返回缺少第 {key} 条译文,请重试或减小 --batch-size。")
            results.append(str(content[key]).strip())
        print(f"\r已翻译 {min(i + batch_size, len(paras))}/{len(paras)} 段", end="", flush=True)
    print()
    return results


# ---------- Argos 本地后端 ----------

def translate_argos(paras: list[tuple[str, str]], glossary: dict[str, str]) -> list[str]:
    try:
        import argostranslate.package
        import argostranslate.translate
    except ImportError:
        sys.exit("argos 后端需要先安装: pip3 install argostranslate")

    installed = {(p.from_code, p.to_code) for p in argostranslate.package.get_installed_packages()}
    if ("en", "zh") not in installed:
        print("首次使用,正在下载英译中语言包……")
        argostranslate.package.update_package_index()
        pkg = next(p for p in argostranslate.package.get_available_packages()
                   if p.from_code == "en" and p.to_code == "zh")
        argostranslate.package.install_from_path(pkg.download())

    results = []
    for idx, (_, text) in enumerate(paras, 1):
        zh = argostranslate.translate.translate(text, "en", "zh")
        for en, cn in glossary.items():
            zh = zh.replace(en, cn)
        results.append(zh.strip())
        print(f"\r已翻译 {idx}/{len(paras)} 段", end="", flush=True)
    print()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="英文字幕文档翻译成中文")
    parser.add_argument("transcript", help="字幕文档路径(本仓库工具生成的 .md 文件)")
    parser.add_argument("--backend", choices=["llm", "argos"], default="llm",
                        help="翻译后端: llm(大模型 API,准确度高)或 argos(本地免费)")
    parser.add_argument("--glossary", help="术语表文件,每行 English=中文")
    parser.add_argument("--bilingual", action="store_true", help="输出中英对照而非纯中文")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="llm 后端每次请求翻译的段落数(默认 20)")
    args = parser.parse_args()

    src = Path(args.transcript)
    header, paras = parse_transcript(src)
    glossary = load_glossary(args.glossary)
    print(f"共 {len(paras)} 段字幕,使用 {args.backend} 后端翻译……")

    if args.backend == "llm":
        translations = translate_llm(paras, glossary, args.batch_size)
    else:
        translations = translate_argos(paras, glossary)

    md_lines = list(header)
    if md_lines and md_lines[-1].strip():
        md_lines.append("")
    txt_lines: list[str] = []
    for (ts, en), zh in zip(paras, translations):
        if args.bilingual:
            md_lines += [f"**[{ts}]** {en}", "", f"> {zh}", ""]
        else:
            md_lines += [f"**[{ts}]** {zh}", ""]
        txt_lines += [zh, ""]

    md_out = src.with_name(f"{src.stem}-中文.md")
    txt_out = src.with_name(f"{src.stem}-中文.txt")
    md_out.write_text("\n".join(md_lines), encoding="utf-8")
    txt_out.write_text("\n".join(txt_lines), encoding="utf-8")
    print(f"完成。\nMarkdown: {md_out}\n纯文本:  {txt_out}")


if __name__ == "__main__":
    main()

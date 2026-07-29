#!/usr/bin/env python3
"""一条命令全自动:提取字幕 → 没有字幕轨道时自动语音识别 → 可选翻译成中文。

用法:
    python3 video_to_doc.py <视频链接> [选项]

示例:
    # 自动判断:有字幕轨道就提取,没有就用 Whisper 语音识别
    python3 video_to_doc.py "https://www.dailymotion.com/video/xxxxx"

    # 一条命令连翻译一起做完(本地免费后端)
    python3 video_to_doc.py "https://www.dailymotion.com/video/xxxxx" --translate argos

    # 用大模型 API 翻译(准确度高,需先 export LLM_API_KEY 等环境变量)
    python3 video_to_doc.py "https://www.dailymotion.com/video/xxxxx" --translate llm

输出(均在 --outdir,默认 output/):
    <视频标题>.md / .txt           —— 字幕文档(带时间戳 / 纯文本)
    <视频标题>-中文.md / .txt      —— 使用 --translate 时的中文翻译
"""

import argparse
import sys
import tempfile
from pathlib import Path

import dailymotion_subtitles as subs


def main() -> None:
    parser = argparse.ArgumentParser(description="视频 → 字幕文档一条龙(自动回退语音识别,可选翻译)")
    parser.add_argument("url", help="视频链接")
    parser.add_argument("--lang", help="首选字幕语言代码,如 zh、en(默认自动选择)")
    parser.add_argument("--outdir", default="output", help="输出目录(默认 output/)")
    parser.add_argument("--paragraph-gap", type=float, default=4.0,
                        help="分段的时间间隔阈值(默认 4 秒)")
    parser.add_argument("--model", default="small",
                        help="语音识别用的 Whisper 模型(默认 small)")
    parser.add_argument("--translate", choices=["llm", "argos"],
                        help="生成文档后接着翻译成中文: llm(大模型 API)或 argos(本地免费)")
    parser.add_argument("--glossary", help="翻译术语表文件,每行 English=中文")
    parser.add_argument("--bilingual", action="store_true", help="翻译输出中英对照")
    parser.add_argument("--cookies", help="cookies 文件路径(Netscape 格式)")
    parser.add_argument("--cookies-from-browser",
                        help="读取本机浏览器 cookies,如 chrome、edge、firefox")
    args = parser.parse_args()
    subs.set_cookies_opts(args.cookies, args.cookies_from_browser)

    # 第一步:检查字幕轨道
    print(f"正在获取视频信息: {args.url}")
    info = subs.fetch_info(args.url)
    print(f"视频标题: {info.get('title')}")
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}

    use_auto = False
    lang = subs.pick_language(manual, args.lang)
    if lang is None:
        lang = subs.pick_language(auto, args.lang)
        use_auto = lang is not None

    # 第二步:有字幕轨道就提取,否则自动回退到语音识别
    if lang is not None:
        print(f"发现{'自动' if use_auto else '人工'}字幕轨道(语言: {lang}),直接提取……")
        with tempfile.TemporaryDirectory() as tmp:
            sub_file = subs.download_subtitle(args.url, lang, use_auto, Path(tmp))
            if sub_file is None:
                sys.exit("字幕下载失败。")
            cues = subs.parse_cues(sub_file)
        lang_label = lang
    else:
        print("该视频没有任何字幕轨道,自动切换为 Whisper 语音识别……")
        import transcribe_video as asr
        with tempfile.TemporaryDirectory() as tmp:
            audio, _ = asr.download_audio(args.url, Path(tmp))
            cues, detected = asr.transcribe(audio, args.model, args.lang)
        lang_label = f"{detected}(Whisper 语音识别)"

    if not cues:
        sys.exit("没有获得任何字幕内容。")

    md_path, txt_path = subs.build_documents(info, lang_label, cues,
                                             Path(args.outdir), args.paragraph_gap)
    print(f"字幕文档完成,共 {len(cues)} 段。\nMarkdown: {md_path}\n纯文本:  {txt_path}")

    # 第三步(可选):接着翻译成中文
    if args.translate:
        import translate_transcript as tr
        print(f"\n开始翻译({args.translate} 后端)……")
        header, paras = tr.parse_transcript(md_path)
        glossary = tr.load_glossary(args.glossary)
        if args.translate == "llm":
            translations = tr.translate_llm(paras, glossary, batch_size=20)
        else:
            translations = tr.translate_argos(paras, glossary)

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
        md_cn = md_path.with_name(f"{md_path.stem}-中文.md")
        txt_cn = md_path.with_name(f"{md_path.stem}-中文.txt")
        md_cn.write_text("\n".join(md_lines), encoding="utf-8")
        txt_cn.write_text("\n".join(txt_lines), encoding="utf-8")
        print(f"翻译完成。\n中文 Markdown: {md_cn}\n中文纯文本:   {txt_cn}")


if __name__ == "__main__":
    main()

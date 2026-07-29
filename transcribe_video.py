#!/usr/bin/env python3
"""对没有字幕轨道的视频做语音识别(Whisper),并整理成文档。

用法:
    python3 transcribe_video.py <视频链接或本地音频文件> [选项]

示例:
    python3 transcribe_video.py "https://www.dailymotion.com/video/xxxxx"
    python3 transcribe_video.py /tmp/audio.m4a --title "某视频" --language en

输出与 dailymotion_subtitles.py 相同:
    output/<视频标题>.md    —— 带时间戳分段的 Markdown 文档
    output/<视频标题>.txt   —— 整理后的纯文本
"""

import argparse
import sys
import tempfile
from pathlib import Path

from dailymotion_subtitles import build_documents, fetch_info, format_time


def download_audio(url: str, workdir: Path) -> tuple[Path, dict]:
    import yt_dlp

    info = fetch_info(url)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": str(workdir / "audio.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    files = sorted(workdir.glob("audio.*"))
    if not files:
        sys.exit("音频下载失败。")
    return files[0], info


def transcribe(audio: Path, model_name: str, language: str | None) -> tuple[list[tuple[float, str]], str]:
    from faster_whisper import WhisperModel

    print(f"加载 Whisper 模型: {model_name} (CPU)")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, transcription_info = model.transcribe(
        str(audio),
        language=language,
        vad_filter=True,
        beam_size=5,
    )
    print(f"识别语言: {transcription_info.language} "
          f"(置信度 {transcription_info.language_probability:.0%}),开始转写……")
    cues: list[tuple[float, str]] = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            cues.append((seg.start, text))
            print(f"\r进度: {format_time(seg.end)}", end="", flush=True)
    print()
    return cues, transcription_info.language


def main() -> None:
    parser = argparse.ArgumentParser(description="视频语音识别并整理成文档")
    parser.add_argument("source", help="视频链接或本地音频文件路径")
    parser.add_argument("--model", default="small",
                        help="Whisper 模型: tiny/base/small/medium/large-v3(默认 small)")
    parser.add_argument("--language", help="音频语言代码,如 en、zh(默认自动检测)")
    parser.add_argument("--title", help="文档标题(本地文件时使用,默认取文件名)")
    parser.add_argument("--url", help="本地文件时可附上原视频链接,写进文档元信息")
    parser.add_argument("--outdir", default="output", help="输出目录(默认 output/)")
    parser.add_argument("--paragraph-gap", type=float, default=4.0,
                        help="分段的时间间隔阈值(默认 4 秒)")
    args = parser.parse_args()

    local = Path(args.source)
    if local.exists():
        audio, info = local, {
            "title": args.title or local.stem,
            "webpage_url": args.url or "",
        }
        tmpdir = None
    else:
        print(f"正在下载音频: {args.source}")
        tmpdir = tempfile.TemporaryDirectory()
        audio, info = download_audio(args.source, Path(tmpdir.name))

    cues, detected_lang = transcribe(audio, args.model, args.language)
    if tmpdir:
        tmpdir.cleanup()
    if not cues:
        sys.exit("没有识别到任何语音内容。")

    lang_label = f"{detected_lang}(Whisper 语音识别)"
    md_path, txt_path = build_documents(info, lang_label, cues, Path(args.outdir), args.paragraph_gap)
    print(f"完成,共 {len(cues)} 段语音。")
    print(f"Markdown 文档: {md_path}")
    print(f"纯文本文档:   {txt_path}")


if __name__ == "__main__":
    main()

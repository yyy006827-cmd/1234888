#!/usr/bin/env python3
"""从 Dailymotion(或其他 yt-dlp 支持的网站)视频中提取字幕并整理成文档。

用法:
    python3 dailymotion_subtitles.py <视频链接> [选项]

示例:
    # 列出视频有哪些语言的字幕
    python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx" --list

    # 提取中文字幕,输出 Markdown 和纯文本文档
    python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx" --lang zh

    # 不指定语言时自动选择(优先 zh/en,否则取第一个可用语言)
    python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx"

输出:
    output/<视频标题>.md    —— 带时间戳分段的 Markdown 文档
    output/<视频标题>.txt   —— 整理后的纯文本(无时间戳,按段落合并)
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    sys.exit("缺少依赖 yt-dlp,请先运行: pip3 install yt-dlp")

PREFERRED_LANGS = ["zh", "zh-CN", "zh-Hans", "zh-TW", "zh-Hant", "en"]


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return name[:120] or "subtitles"


# 额外的 yt-dlp 参数(如 cookies),由命令行选项填充,供本模块和 transcribe_video.py 共用
EXTRA_OPTS: dict = {}


def set_cookies_opts(cookies: str | None, cookies_from_browser: str | None, impersonate: str | None = None) -> None:
    if cookies:
        EXTRA_OPTS["cookiefile"] = cookies
    if cookies_from_browser:
        EXTRA_OPTS["cookiesfrombrowser"] = (cookies_from_browser,)
    if impersonate:
        # yt-dlp ImpersonateTarget: "client[:os]" e.g. firefox-135:macos-14
        from yt_dlp.networking.impersonate import ImpersonateTarget
        EXTRA_OPTS["impersonate"] = ImpersonateTarget.from_str(impersonate)


def fetch_info(url: str) -> dict:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, **EXTRA_OPTS}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def pick_language(available: dict, requested: str | None) -> str | None:
    if not available:
        return None
    if requested:
        if requested in available:
            return requested
        # 允许 "zh" 匹配 "zh-CN" 之类的变体
        for lang in available:
            if lang.startswith(requested):
                return lang
        return None
    for lang in PREFERRED_LANGS:
        if lang in available:
            return lang
    return next(iter(available))


def download_subtitle(url: str, lang: str, auto: bool, workdir: Path) -> Path | None:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": not auto,
        "writeautomaticsub": auto,
        "subtitleslangs": [lang],
        "subtitlesformat": "vtt/srt/best",
        "outtmpl": str(workdir / "subtitle.%(ext)s"),
        **EXTRA_OPTS,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    matches = list(workdir.glob(f"subtitle.{lang}.*")) + list(workdir.glob("subtitle.*"))
    for f in matches:
        if f.suffix in (".vtt", ".srt"):
            return f
    return None


TIMESTAMP_RE = re.compile(
    r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})[.,]\d{3}"
)
TAG_RE = re.compile(r"<[^>]+>")


def parse_cues(path: Path) -> list[tuple[float, str]]:
    """解析 VTT/SRT,返回 (开始秒数, 文本) 列表,去除标签和重复行。"""
    cues: list[tuple[float, str]] = []
    current_start: float | None = None
    current_lines: list[str] = []

    def flush():
        nonlocal current_start, current_lines
        if current_start is not None and current_lines:
            text = " ".join(current_lines).strip()
            if text:
                cues.append((current_start, text))
        current_start, current_lines = None, []

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        m = TIMESTAMP_RE.search(line)
        if m:
            flush()
            hours = int(m.group(1) or 0)
            current_start = hours * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            continue
        if not line:
            flush()
            continue
        if line == "WEBVTT" or line.startswith(("NOTE", "STYLE", "Kind:", "Language:")):
            continue
        if line.isdigit() and current_start is None:
            continue  # SRT 序号
        if current_start is not None:
            text = TAG_RE.sub("", line).strip()
            if text and (not current_lines or current_lines[-1] != text):
                current_lines.append(text)
    flush()

    # 相邻 cue 文本相同时合并(滚动字幕常见)
    deduped: list[tuple[float, str]] = []
    for start, text in cues:
        if deduped and deduped[-1][1] == text:
            continue
        deduped.append((start, text))
    return deduped


def format_time(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def is_sentence_end(text: str) -> bool:
    return text.rstrip().endswith((".", "!", "?", "。", "!", "?", "…", '"', "」", "』"))


def build_documents(info: dict, lang: str, cues: list[tuple[float, str]],
                    outdir: Path, paragraph_gap: float) -> tuple[Path, Path]:
    title = info.get("title") or info.get("id") or "视频"
    stem = sanitize_filename(title)
    outdir.mkdir(parents=True, exist_ok=True)

    # 按时间间隔与句子结尾分段
    paragraphs: list[tuple[float, list[str]]] = []
    for i, (start, text) in enumerate(cues):
        new_para = not paragraphs
        if paragraphs and i > 0:
            gap = start - cues[i - 1][0]
            if gap >= paragraph_gap and is_sentence_end(paragraphs[-1][1][-1]):
                new_para = True
        if new_para:
            paragraphs.append((start, [text]))
        else:
            paragraphs[-1][1].append(text)

    duration = info.get("duration")
    meta_lines = [
        f"# {title}",
        "",
        f"- 视频链接: {info.get('webpage_url', '')}",
        f"- 上传者: {info.get('uploader', '未知')}",
        f"- 时长: {format_time(duration) if duration else '未知'}",
        f"- 字幕语言: {lang}",
        "",
        "## 字幕内容",
        "",
    ]
    md_parts = list(meta_lines)
    txt_parts = [title, ""]
    for start, texts in paragraphs:
        body = " ".join(texts)
        md_parts.append(f"**[{format_time(start)}]** {body}")
        md_parts.append("")
        txt_parts.append(body)
        txt_parts.append("")

    md_path = outdir / f"{stem}.md"
    txt_path = outdir / f"{stem}.txt"
    md_path.write_text("\n".join(md_parts), encoding="utf-8")
    txt_path.write_text("\n".join(txt_parts), encoding="utf-8")
    return md_path, txt_path


def main() -> None:
    parser = argparse.ArgumentParser(description="提取 Dailymotion 视频字幕并整理成文档")
    parser.add_argument("url", help="视频链接,例如 https://www.dailymotion.com/video/xxxxx")
    parser.add_argument("--lang", help="字幕语言代码,例如 zh、en、fr(默认自动选择)")
    parser.add_argument("--list", action="store_true", help="仅列出可用字幕语言,不下载")
    parser.add_argument("--outdir", default="output", help="输出目录(默认 output/)")
    parser.add_argument("--paragraph-gap", type=float, default=4.0,
                        help="相邻字幕间隔超过该秒数且句子已结束时分段(默认 4 秒)")
    parser.add_argument("--cookies", help="cookies 文件路径(Netscape 格式),用于需要登录的网站如 B 站")
    parser.add_argument("--cookies-from-browser",
                        help="直接读取本机浏览器 cookies,如 chrome、edge、firefox")
    parser.add_argument("--impersonate", default="firefox-135:macos-14",
                        help="浏览器模拟目标,Dailymotion 等站点需要(默认 firefox-135:macos-14;传空字符串可关闭)")
    args = parser.parse_args()
    set_cookies_opts(args.cookies, args.cookies_from_browser, args.impersonate or None)

    print(f"正在获取视频信息: {args.url}")
    info = fetch_info(args.url)
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}

    print(f"视频标题: {info.get('title')}")
    print(f"人工字幕语言: {', '.join(manual) if manual else '无'}")
    print(f"自动字幕语言: {', '.join(auto) if auto else '无'}")
    if args.list:
        return

    use_auto = False
    lang = pick_language(manual, args.lang)
    if lang is None:
        lang = pick_language(auto, args.lang)
        use_auto = lang is not None
    if lang is None:
        wanted = f"「{args.lang}」" if args.lang else ""
        sys.exit(f"该视频没有{wanted}可用字幕,无法提取。")

    print(f"使用{'自动' if use_auto else '人工'}字幕,语言: {lang}")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        sub_file = download_subtitle(args.url, lang, use_auto, Path(tmp))
        if sub_file is None:
            sys.exit("字幕下载失败。")
        cues = parse_cues(sub_file)

    if not cues:
        sys.exit("字幕文件为空或无法解析。")

    md_path, txt_path = build_documents(info, lang, cues, Path(args.outdir), args.paragraph_gap)
    print(f"完成,共 {len(cues)} 条字幕。")
    print(f"Markdown 文档: {md_path}")
    print(f"纯文本文档:   {txt_path}")


if __name__ == "__main__":
    main()

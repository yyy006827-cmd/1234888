#!/usr/bin/env python3
"""新手一键启动器:运行后按提示粘贴视频链接即可,不用自己敲命令。

Windows:双击本文件(或右键 → 用 Python 打开)
Mac:在终端进入本文件夹后运行  python3 新手一键启动.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pause():
    input("\n按回车键关闭窗口……")


def ensure_deps() -> bool:
    """检查依赖;缺失时提示安装。"""
    missing = []
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        missing.append("yt-dlp")
    try:
        import curl_cffi  # noqa: F401
    except ImportError:
        missing.append("curl_cffi")

    if not missing:
        return True

    print("检测到缺少必要的库:", ", ".join(missing))
    print("正在自动安装(只需第一次),请稍等……\n")
    req = HERE / "requirements.txt"
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("\n安装失败。请检查网络后重试,或手动运行:")
        print("  python -m pip install -r requirements.txt")
        return False
    print("\n依赖安装完成。\n")
    return True


def main() -> None:
    print("=" * 50)
    print("  视频字幕提取工具(新手版)")
    print("=" * 50)
    print()
    print("说明:把视频链接粘贴到下方提示处即可。")
    print("支持 Dailymotion、B 站(本机)、YouTube 等。")
    print()

    if not ensure_deps():
        pause()
        return

    url = input("请粘贴视频链接,然后按回车:\n> ").strip().strip('"').strip("'")
    if not url:
        print("没有输入链接,已退出。")
        pause()
        return
    if not url.startswith(("http://", "https://")):
        print("看起来不像有效的网址(应以 http 开头),请重新运行并粘贴完整链接。")
        pause()
        return

    print()
    print("是否需要中文翻译?")
    print("  1 = 只要英文字幕(更快)")
    print("  2 = 要中文翻译(免费本地翻译,质量中等)")
    print("  3 = 要中文翻译(大模型 API,需事先配置 LLM_API_KEY)")
    choice = input("请输入 1 / 2 / 3 后按回车(直接回车=只要英文字幕):\n> ").strip() or "1"

    script = HERE / "video_to_doc.py"
    cmd = [sys.executable, str(script), url]
    if choice == "2":
        cmd += ["--translate", "argos"]
        # argos 可能未装,先尝试安装
        try:
            import argostranslate  # noqa: F401
        except ImportError:
            print("\n正在安装本地翻译库(只需第一次)……")
            subprocess.run([sys.executable, "-m", "pip", "install", "argostranslate"], check=False)
    elif choice == "3":
        cmd += ["--translate", "llm"]

    # Whisper 在无字幕时会用到;提前检查
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        print("\n正在安装语音识别库 faster-whisper(只需第一次,体积较大)……")
        subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper"], check=False)

    if not shutil.which("ffmpeg"):
        print("\n提示:本机似乎没有安装 ffmpeg。")
        print("若视频没有字幕、需要语音识别,请先安装 ffmpeg:")
        print("  Windows: 打开 https://ffmpeg.org/download.html 下载")
        print("  Mac: 在终端运行  brew install ffmpeg")
        print("先继续尝试……\n")

    print("\n开始处理,请耐心等待(长视频可能要几十分钟)……\n")
    result = subprocess.run(cmd, cwd=str(HERE))

    print()
    if result.returncode == 0:
        out = HERE / "output"
        print("完成!生成的文件在这个文件夹里:")
        print(f"  {out}")
        print("打开后找 .md 或 .txt 文件即可。")
    else:
        print("处理失败。请把上方的红色报错信息截图发给我,我帮你看。")
    pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消。")
    except Exception as e:
        print(f"\n出错了: {e}")
        pause()

# Dailymotion 视频字幕提取工具

从 Dailymotion(以及其他 yt-dlp 支持的网站)视频中提取字幕,并自动整理成文档:

- `output/<视频标题>.md` —— 带时间戳分段的 Markdown 文档
- `output/<视频标题>.txt` —— 整理后的纯文本(无时间戳,按段落合并,方便直接复制到 Word 等)

## 安装

需要 Python 3.10+:

```bash
pip3 install -r requirements.txt
```

> 其中 `curl_cffi` 是必需的:Dailymotion 有反爬限制,yt-dlp 需要它来模拟浏览器访问。

## 使用方法

```bash
# 1. 先看视频有哪些语言的字幕
python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx" --list

# 2. 提取字幕并生成文档(不指定语言时优先中文/英文,否则取第一个可用语言)
python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx"

# 指定语言,例如英文
python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx" --lang en
```

## 选项

| 选项 | 说明 |
| --- | --- |
| `--list` | 仅列出可用字幕语言,不下载 |
| `--lang <代码>` | 指定字幕语言,如 `zh`、`en`、`fr`(`zh` 可自动匹配 `zh-CN` 等变体)|
| `--outdir <目录>` | 输出目录,默认 `output/` |
| `--paragraph-gap <秒>` | 分段依据:相邻字幕间隔超过该秒数且句子已结束时另起一段,默认 4 秒 |

## 注意

- 只有视频本身带字幕(人工上传或平台自动生成)时才能提取;脚本不做语音识别。如果 `--list` 显示没有任何字幕,则该视频无法用本工具提取。
- 视频没有你要的语言时,脚本会列出实际可用的语言供选择。

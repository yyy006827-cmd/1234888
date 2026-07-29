# 视频字幕提取与翻译工具

从 Dailymotion、B 站等 yt-dlp 支持的网站视频中提取字幕、对无字幕视频做语音识别,并可将英文字幕翻译成中文,全部自动整理成文档:

- `output/<视频标题>.md` —— 带时间戳分段的 Markdown 文档
- `output/<视频标题>.txt` —— 整理后的纯文本(无时间戳,按段落合并,方便直接复制到 Word 等)

## 安装

需要 Python 3.10+:

```bash
pip3 install -r requirements.txt
```

> 其中 `curl_cffi` 是必需的:Dailymotion 有反爬限制,yt-dlp 需要它来模拟浏览器访问。

## 使用方法

### 推荐:一条命令全自动 `video_to_doc.py`

自动判断视频有没有字幕轨道:有就直接提取,没有就自动切换 Whisper 语音识别,还可以顺带翻译成中文,全程无需手动处理中间文件:

```bash
# 只要字幕文档
python3 video_to_doc.py "https://www.dailymotion.com/video/xxxxx"

# 字幕 + 中文翻译一起做完(本地免费后端)
python3 video_to_doc.py "https://www.dailymotion.com/video/xxxxx" --translate argos

# 用大模型 API 翻译(准确度高,需先设置 LLM_API_KEY 等环境变量,见下文)
python3 video_to_doc.py "https://www.dailymotion.com/video/xxxxx" --translate llm
```

以下三个单步工具适合只需要其中一步、或想分步控制参数时使用。

### 1. 提取字幕(视频自带字幕轨道时)

```bash
# 先看视频有哪些语言的字幕
python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx" --list

# 提取字幕并生成文档(不指定语言时优先中文/英文,否则取第一个可用语言)
python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx"

# 指定语言,例如英文
python3 dailymotion_subtitles.py "https://www.dailymotion.com/video/xxxxx" --lang en
```

### 2. 语音识别(视频没有字幕轨道时)

```bash
pip3 install faster-whisper
python3 transcribe_video.py "https://www.dailymotion.com/video/xxxxx"
# 可用 --model medium 换更大的模型提高准确度(速度变慢),--language en 跳过语言检测
```

### 3. 英文字幕翻译成中文

```bash
# 方式一(推荐,准确度高):任意 OpenAI 兼容的大模型 API,例如 DeepSeek
export LLM_API_KEY=sk-xxxx
export LLM_BASE_URL=https://api.deepseek.com/v1
export LLM_MODEL=deepseek-chat
python3 translate_transcript.py "output/视频标题.md"

# 方式二(免费,完全本地,准确度中等)
pip3 install argostranslate
python3 translate_transcript.py "output/视频标题.md" --backend argos

# 可选:--bilingual 输出中英对照;--glossary terms.txt 固定人名/术语译法(每行 English=中文)
```

## 支持哪些网站?

- 凡是 [yt-dlp 支持的网站](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)(1800+ 个,包括 Dailymotion、B 站、YouTube、Vimeo 等)都可以直接用,命令完全一样,把链接换掉即可。
- **B 站**:受支持,但对云服务器 IP 有反爬拦截(HTTP 412),请在自己电脑上运行;部分视频的 CC 字幕需要登录,可加 `--cookies-from-browser chrome`(或 edge/firefox)读取本机浏览器登录状态。
- **ReelShort**:不在 yt-dlp 支持列表中,本工具目前无法直接提取。

## 选项

| 选项 | 说明 |
| --- | --- |
| `--list` | 仅列出可用字幕语言,不下载 |
| `--lang <代码>` | 指定字幕语言,如 `zh`、`en`、`fr`(`zh` 可自动匹配 `zh-CN` 等变体)|
| `--outdir <目录>` | 输出目录,默认 `output/` |
| `--paragraph-gap <秒>` | 分段依据:相邻字幕间隔超过该秒数且句子已结束时另起一段,默认 4 秒 |

## 注意

- `dailymotion_subtitles.py` 只提取视频自带的字幕轨道;如果 `--list` 显示没有任何字幕,请改用 `transcribe_video.py` 做语音识别。
- 视频没有你要的语言时,脚本会列出实际可用的语言供选择。
- 语音识别和机器翻译都可能有小误差;对准确度要求高时,建议翻译用大模型后端,并用 `--glossary` 固定人名译法。

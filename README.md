# YouTube视频下载和字幕翻译工具

一个强大的Python工具，用于从YouTube下载视频，使用OpenAI API翻译字幕，并使用ffmpeg将字幕合成到视频中。

## 功能特性

- ✅ 从YouTube下载高清视频
- ✅ 自动下载英文字幕
- ✅ 使用OpenAI GPT模型翻译字幕
- ✅ 支持软字幕（可开关）和硬字幕（永久嵌入）
- ✅ 支持多种字幕格式（SRT、VTT）
- ✅ 可配置的目标语言
- ✅ 批量处理支持

## 安装要求

### 系统要求
- Python 3.8+
- ffmpeg（已安装并添加到PATH）
- OpenAI API密钥

### 安装步骤

1. 克隆或下载项目
```bash
cd /Users/ning/www/reclipper
```

2. 安装Python依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的OpenAI API密钥：
```env
OPENAI_API_KEY=你的OpenAI_API密钥
OPENAI_BASE_URL=https://api.openai.com/v1
DOWNLOAD_DIR=./downloads
TARGET_LANGUAGE=zh-CN
TRANSLATION_MODEL=gpt-3.5-turbo
```

## 使用方法

### 基本用法
```bash
# 下载视频并添加中文字幕（软字幕）
python main.py "https://www.youtube.com/watch?v=视频ID"

# 指定输出文件
python main.py "https://www.youtube.com/watch?v=视频ID" -o "输出视频.mp4"

# 使用硬字幕
python main.py "https://www.youtube.com/watch?v=视频ID" -e hard

# 指定目标语言
python main.py "https://www.youtube.com/watch?v=视频ID" -l ja  # 日语
```

### 仅翻译现有文件
如果你已经有视频和字幕文件，可以只进行翻译和合成：
```bash
python main.py --no-download --video-file "视频.mp4" --subtitle-file "字幕.srt" -l zh-CN
```

### 命令行选项
```
参数:
  url                    YouTube视频URL

选项:
  -h, --help            显示帮助信息
  -o, --output          输出文件路径
  -l, --language        目标语言 (默认: zh-CN)
  -e, --embed-type      字幕嵌入类型: soft(软字幕) 或 hard(硬字幕) (默认: soft)
  --no-download         仅翻译现有字幕，不下载视频
  --subtitle-file       现有字幕文件路径（与--no-download一起使用）
  --video-file          现有视频文件路径（与--no-download一起使用）
```

## 配置说明

### 环境变量配置
在 `.env` 文件中可以配置以下参数：

- `OPENAI_API_KEY`: OpenAI API密钥（必需）
- `OPENAI_BASE_URL`: OpenAI API基础URL
- `DOWNLOAD_DIR`: 下载文件保存目录
- `TARGET_LANGUAGE`: 目标语言代码（如zh-CN、ja、ko等）
- `TRANSLATION_MODEL`: 翻译模型（gpt-3.5-turbo或gpt-4）
- `MAX_VIDEO_SIZE`: 最大视频大小限制
- `FFMPEG_PATH`: ffmpeg可执行文件路径（如果不在PATH中）

### 支持的语言代码
- `zh-CN`: 简体中文
- `zh-TW`: 繁体中文
- `ja`: 日语
- `ko`: 韩语
- `en`: 英语
- `fr`: 法语
- `de`: 德语
- `es`: 西班牙语

## 项目结构

```
reclipper/
├── main.py                 # 主程序入口
├── config.py               # 配置管理
├── youtube_downloader.py   # YouTube下载模块
├── subtitle_translator.py  # 字幕翻译模块
├── video_processor.py     # 视频处理模块
├── requirements.txt        # Python依赖
├── .env.example           # 环境变量示例
└── README.md              # 说明文档
```

## 模块说明

### YouTube下载器 (`youtube_downloader.py`)
- 使用yt-dlp库下载YouTube视频
- 自动下载可用字幕
- 支持多种视频质量和格式

### 字幕翻译器 (`subtitle_translator.py`)
- 使用OpenAI GPT模型翻译字幕
- 支持SRT和VTT格式
- 批量翻译优化
- 错误处理和回退机制

### 视频处理器 (`video_processor.py`)
- 使用ffmpeg合成字幕
- 支持软字幕和硬字幕
- 可配置的字幕样式
- 视频信息提取

## 常见问题

### Q: 程序提示"未找到ffmpeg"
A: 请确保ffmpeg已安装并添加到系统PATH环境变量中。

### Q: 翻译失败或API调用错误
A: 检查OpenAI API密钥是否正确，以及API配额是否充足。

### Q: 视频下载速度慢
A: 可以尝试使用代理或更换网络环境。

### Q: 字幕翻译不准确
A: 可以尝试使用gpt-4模型（修改TRANSLATION_MODEL配置）。

## 许可证

本项目基于MIT许可证开源。

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。

## 免责声明

本工具仅供学习和研究使用，请遵守YouTube的服务条款和当地法律法规。使用者需对下载内容的使用负责。
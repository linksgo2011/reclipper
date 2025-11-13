#!/usr/bin/env python3
"""
YouTube视频下载和字幕翻译工具

功能：
1. 从YouTube下载视频和字幕
2. 使用OpenAI API翻译字幕
3. 使用ffmpeg将字幕合成到视频中

使用方法：
python main.py <YouTube_URL> [选项]
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from youtube_downloader import download_youtube_video
from subtitle_translator import translate_subtitle
from video_processor import embed_subtitle_to_video, burn_subtitle_to_video, VideoProcessor
from config import get_settings


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='YouTube视频下载和字幕翻译工具')
    parser.add_argument('url', help='YouTube视频URL')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--language', '-l', default='zh-CN', help='目标语言 (默认: zh-CN)')
    parser.add_argument('--embed-type', '-e', choices=['soft', 'hard'], default='hard', 
                       help='字幕嵌入类型: soft(软字幕) 或 hard(硬字幕) (默认: hard)')
    parser.add_argument('--no-download', action='store_true', help='仅翻译现有字幕，不下载视频')
    parser.add_argument('--subtitle-file', help='现有字幕文件路径（与--no-download一起使用）')
    parser.add_argument('--video-file', help='现有视频文件路径（与--no-download一起使用）')
    
    args = parser.parse_args()
    
    try:
        print("\n🔧" + "=" * 48 + "🔧")
        print("🔍 开始检查配置和参数...")
        print(f"   运行模式: {'仅翻译现有文件' if args.no_download else '完整下载流程'}")
        print(f"   目标语言: {args.language}")
        print(f"   字幕类型: {args.embed_type}")
        print("🔧" + "=" * 48 + "🔧")
        
        # 检查配置
        settings = get_settings()
        if not settings.openai_api_key or settings.openai_api_key.startswith('your_'):
            print("❌ 错误: 请配置OpenAI API密钥")
            print("1. 复制 .env.example 为 .env")
            print("2. 在 .env 文件中设置 OPENAI_API_KEY=你的API密钥")
            sys.exit(1)
        
        print("✅ 配置检查通过")
        
        if args.no_download:
            # 仅翻译模式
            if not args.subtitle_file or not args.video_file:
                print("❌ 错误: 在--no-download模式下需要提供--subtitle-file和--video-file参数")
                sys.exit(1)
            
            print(f"✅ 参数验证通过")
            print(f"   视频文件: {args.video_file}")
            print(f"   字幕文件: {args.subtitle_file}")
            
            process_existing_files(args.video_file, args.subtitle_file, args.language, 
                                 args.embed_type, args.output)
        else:
            # 完整下载和翻译流程
            print(f"✅ 参数验证通过")
            print(f"   YouTube URL: {args.url}")
            
            download_and_process(args.url, args.language, args.embed_type, args.output)
            
    except KeyboardInterrupt:
        print("\n⚠️" + "=" * 48 + "⚠️")
        print("⚠️ 程序被用户中断")
        print("⚠️" + "=" * 48 + "⚠️")
        sys.exit(0)
    except Exception as e:
        print("\n❌" + "=" * 48 + "❌")
        print(f"❌ 程序执行出错: {str(e)}")
        print("❌" + "=" * 48 + "❌")
        sys.exit(1)


def download_and_process(url: str, target_language: str, embed_type: str, output_file: Optional[str]):
    """下载并处理视频"""
    print("🚀" + "=" * 48 + "🚀")
    print("🎬 开始处理YouTube视频...")
    print(f"   URL: {url}")
    print(f"   目标语言: {target_language}")
    print(f"   字幕类型: {embed_type}")
    print("🚀" + "=" * 48 + "🚀")
    
    # 1. 检查文件是否已存在
    from youtube_downloader import YouTubeDownloader
    downloader = YouTubeDownloader()
    
    # 获取视频标题用于检查文件
    import yt_dlp
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get('title', 'video')
    
    print(f"📺 视频标题: {video_title}")
    
    # 检查视频文件是否已存在
    video_file = downloader.download_dir / f"{video_title}.mp4"
    
    # 检查字幕文件
    subtitle_files = list(downloader.download_dir.glob(f"{video_title}.*.vtt"))
    subtitle_files += list(downloader.download_dir.glob(f"{video_title}.*.srt"))
    
    # 检测英文字幕和中文字幕
    english_subtitle = None
    chinese_subtitle = None
    
    for subtitle_file in subtitle_files:
        if 'en' in subtitle_file.name and ('zh-CN' not in subtitle_file.name and 'zh-Hans' not in subtitle_file.name):
            english_subtitle = subtitle_file
            print(f"✅ 检测到英文字幕: {english_subtitle.name}")
        elif 'zh-CN' in subtitle_file.name or 'zh-Hans' in subtitle_file.name:
            chinese_subtitle = subtitle_file
            print(f"✅ 检测到中文字幕: {chinese_subtitle.name}")
    
    # 如果视频文件和英文字幕都存在，跳过下载
    if video_file.exists() and english_subtitle:
        print(f"✅ 视频文件已存在: {video_file}")
        print(f"✅ 英文字幕已存在: {english_subtitle.name}")
        print("💡 提示: 检测到视频和英文字幕，跳过下载步骤")
        
        # 如果中文字幕也存在，跳过翻译
        if chinese_subtitle:
            print(f"✅ 中文字幕已存在: {chinese_subtitle.name}")
            print("💡 提示: 检测到中文字幕，跳过翻译步骤")
            
            # 直接处理双语字幕
            print("🔄 开始处理双语字幕...")
            process_bilingual_files(str(video_file), str(english_subtitle), str(chinese_subtitle), embed_type, output_file)
            return
        else:
            # 只有英文字幕，需要翻译
            print("🔄 开始处理现有文件...")
            process_existing_files(str(video_file), str(english_subtitle), target_language, embed_type, output_file)
            return
    
    # 如果只有视频文件存在，但没有英文字幕，继续下载
    if video_file.exists():
        print(f"✅ 视频文件已存在: {video_file}")
        print("⚠️ 未找到英文字幕，继续下载字幕")
    else:
        print("⚠️ 未找到视频文件，继续下载流程")
    
    # 2. 下载视频和字幕
    print("\n📥 开始下载YouTube视频...")
    download_result = download_youtube_video(url)
    print(f"✅ 视频下载完成: {download_result['title']}")
    print(f"✅ 视频文件: {download_result['video_file']}")
    
    # 2. 检查字幕
    if not download_result['subtitles']:
        print("⚠️ 未找到字幕文件，跳过字幕处理")
        return
    
    print(f"✅ 找到 {len(download_result['subtitles'])} 个字幕文件: {list(download_result['subtitles'].keys())}")
    
    # 3. 简化字幕选择：默认使用英文字幕并翻译
    english_subtitle_file = None
    
    # 优先使用英文字幕
    if 'en' in download_result['subtitles']:
        english_subtitle_file = download_result['subtitles']['en']
        print(f"✅ 使用英文字幕: {english_subtitle_file}")
    else:
        # 如果没有英文字幕，使用第一个字幕文件
        first_lang = list(download_result['subtitles'].keys())[0]
        english_subtitle_file = download_result['subtitles'][first_lang]
        print(f"✅ 使用字幕文件({first_lang}): {english_subtitle_file}")
    
    # 翻译字幕
    if target_language != 'en':
        print("\n🌐" + "=" * 46 + "🌐")
        print("🔤 开始翻译字幕...")
        print(f"   源语言: 检测到的语言")
        print(f"   目标语言: {target_language}")
        print("🌐" + "=" * 46 + "🌐")
        
        chinese_subtitle_file = translate_subtitle(english_subtitle_file, target_language)
        print(f"✅ 字幕翻译完成: {chinese_subtitle_file}")
    else:
        chinese_subtitle_file = english_subtitle_file
        print("💡 提示: 目标语言为英文，无需翻译")
    
    # 4. 合成字幕到视频
    print("\n🎬" + "=" * 46 + "🎬")
    print("🔧 开始合成字幕到视频...")
    
    # 默认使用双语字幕
    print("💡 默认使用双语字幕")
    print(f"   中文字幕: {chinese_subtitle_file}")
    print(f"   英文字幕: {english_subtitle_file}")
    print("🎬" + "=" * 46 + "🎬")
    
    video_file = download_result['video_file']
    processor = VideoProcessor()
    
    if embed_type == 'soft':
        # 软字幕：创建双语字幕文件
        print("🔄 创建双语软字幕...")
        bilingual_subtitle_file = processor.create_bilingual_subtitle_file(
            chinese_subtitle_file, english_subtitle_file
        )
        print(f"✅ 双语字幕文件创建完成: {bilingual_subtitle_file}")
        final_video = embed_subtitle_to_video(video_file, bilingual_subtitle_file, output_file)
        print(f"✅ 双语软字幕嵌入完成: {final_video}")
        print("💡 提示: 软字幕可以在播放器中开关")
    else:
        # 硬字幕：使用双语烧录功能
        print("🔄 创建双语硬字幕...")
        final_video = processor.burn_bilingual_subtitle(
            video_file, chinese_subtitle_file, english_subtitle_file, output_file
        )
        print(f"✅ 双语硬字幕烧录完成: {final_video}")
        print("💡 提示: 中文在上方（大字体），英文在下方（小字体）")
    
    print("\n🎉" + "=" * 46 + "🎉")
    print("✅ 处理完成!")
    print(f"   最终视频文件: {final_video}")
    print("🎉" + "=" * 46 + "🎉")


def process_bilingual_files(video_file, english_subtitle_file, chinese_subtitle_file, embed_type, output_file):
    """处理已存在的双语字幕文件"""
    print(f"🎬 处理视频文件: {video_file}")
    print(f"📝 英文字幕: {english_subtitle_file}")
    print(f"📝 中文字幕: {chinese_subtitle_file}")
    
    # 合成字幕到视频
    processor = VideoProcessor()
    
    print("\n🎬" + "=" * 46 + "🎬")
    print("🔧 开始合成双语字幕到视频...")
    
    # 默认使用双语字幕
    print("💡 使用双语字幕")
    print(f"   中文字幕: {chinese_subtitle_file}")
    print(f"   英文字幕: {english_subtitle_file}")
    
    if embed_type == 'soft':
        # 软字幕：创建双语字幕文件
        print("🔄 创建双语软字幕...")
        bilingual_subtitle_file = processor.create_bilingual_subtitle_file(
            chinese_subtitle_file, english_subtitle_file
        )
        print(f"✅ 双语字幕文件创建完成: {bilingual_subtitle_file}")
        final_video = embed_subtitle_to_video(video_file, bilingual_subtitle_file, output_file)
        print(f"✅ 双语软字幕嵌入完成: {final_video}")
        print("💡 提示: 软字幕可以在播放器中开关")
    else:
        # 硬字幕：使用双语烧录功能
        print("🔄 创建双语硬字幕...")
        final_video = processor.burn_bilingual_subtitle(
            video_file, chinese_subtitle_file, english_subtitle_file, output_file
        )
        print(f"✅ 双语硬字幕烧录完成: {final_video}")
        print("💡 提示: 中文在上方（大字体），英文在下方（小字体）")
    
    print("\n🎉" + "=" * 46 + "🎉")
    print("🎉 双语字幕处理完成！")
    print(f"📁 最终视频文件: {final_video}")
    print("🎉" + "=" * 46 + "🎉")


def process_existing_files(video_file: str, subtitle_file: str, target_language: str, 
                          embed_type: str, output_file: Optional[str]):
    """处理现有文件"""
    print("\n📁" + "=" * 46 + "📁")
    print("🔍 开始处理现有文件...")
    print(f"   视频文件: {video_file}")
    print(f"   字幕文件: {subtitle_file}")
    print(f"   目标语言: {target_language}")
    print(f"   字幕类型: {embed_type}")
    print("📁" + "=" * 46 + "📁")
    
    # 检查文件是否存在
    if not Path(video_file).exists():
        raise FileNotFoundError(f"视频文件不存在: {video_file}")
    if not Path(subtitle_file).exists():
        raise FileNotFoundError(f"字幕文件不存在: {subtitle_file}")
    
    print("✅ 文件验证通过")
    
    # 简化字幕处理逻辑：默认使用双语字幕
    subtitle_path = Path(subtitle_file)
    
    # 直接假设输入的字幕是英文字幕
    english_subtitle_file = subtitle_file
    print(f"✅ 使用英文字幕: {subtitle_file}")
    
    # 翻译英文字幕
    if target_language != 'en':
        print("\n🌐 开始翻译字幕...")
        chinese_subtitle_file = translate_subtitle(subtitle_file, target_language)
        print(f"✅ 字幕翻译完成: {chinese_subtitle_file}")
    else:
        chinese_subtitle_file = subtitle_file
        print("💡 提示: 目标语言为英文，无需翻译")
    
    # 合成字幕到视频
    processor = VideoProcessor()
    
    print("\n🎬" + "=" * 46 + "🎬")
    print("🔧 开始合成字幕到视频...")
    
    # 默认使用双语字幕
    print("💡 默认使用双语字幕")
    print(f"   中文字幕: {chinese_subtitle_file}")
    print(f"   英文字幕: {english_subtitle_file}")
    
    if embed_type == 'soft':
        # 软字幕：创建双语字幕文件
        print("🔄 创建双语软字幕...")
        bilingual_subtitle_file = processor.create_bilingual_subtitle_file(
            chinese_subtitle_file, english_subtitle_file
        )
        print(f"✅ 双语字幕文件创建完成: {bilingual_subtitle_file}")
        final_video = embed_subtitle_to_video(video_file, bilingual_subtitle_file, output_file)
        print(f"✅ 双语软字幕嵌入完成: {final_video}")
        print("💡 提示: 软字幕可以在播放器中开关")
    else:
        # 硬字幕：使用双语烧录功能
        print("🔄 创建双语硬字幕...")
        final_video = processor.burn_bilingual_subtitle(
            video_file, chinese_subtitle_file, english_subtitle_file, output_file
        )
        print(f"✅ 双语硬字幕烧录完成: {final_video}")
        print("💡 提示: 中文在上方（大字体），英文在下方（小字体）")
    
    print("\n🎉" + "=" * 46 + "🎉")
    print("🎉 处理完成！")
    print(f"📁 最终视频文件: {final_video}")
    print("🎉" + "=" * 46 + "🎉")


if __name__ == "__main__":
    main()
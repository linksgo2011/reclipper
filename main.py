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
from video_processor import embed_subtitle_to_video, burn_subtitle_to_video
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
        # 检查配置
        settings = get_settings()
        if not settings.openai_api_key or settings.openai_api_key.startswith('your_'):
            print("错误: 请配置OpenAI API密钥")
            print("1. 复制 .env.example 为 .env")
            print("2. 在 .env 文件中设置 OPENAI_API_KEY=你的API密钥")
            sys.exit(1)
        
        if args.no_download:
            # 仅翻译模式
            if not args.subtitle_file or not args.video_file:
                print("错误: 在--no-download模式下需要提供--subtitle-file和--video-file参数")
                sys.exit(1)
            
            process_existing_files(args.video_file, args.subtitle_file, args.language, 
                                 args.embed_type, args.output)
        else:
            # 完整下载和翻译流程
            download_and_process(args.url, args.language, args.embed_type, args.output)
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


def download_and_process(url: str, target_language: str, embed_type: str, output_file: Optional[str]):
    """下载并处理视频"""
    print("=" * 50)
    print("开始处理YouTube视频...")
    print("=" * 50)
    
    # 1. 检查文件是否已存在
    from youtube_downloader import YouTubeDownloader
    downloader = YouTubeDownloader()
    
    # 获取视频标题用于检查文件
    import yt_dlp
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get('title', 'video')
    
    # 检查视频文件是否已存在
    video_file = downloader.download_dir / f"{video_title}.mp4"
    if video_file.exists():
        print(f"✓ 视频文件已存在: {video_file}")
        print("提示: 检测到视频文件已存在，跳过下载步骤")
        
        # 检查字幕文件
    subtitle_files = list(downloader.download_dir.glob(f"{video_title}.*.vtt"))
    subtitle_files += list(downloader.download_dir.glob(f"{video_title}.*.srt"))
    
    if subtitle_files:
        print(f"✓ 找到字幕文件: {[f.name for f in subtitle_files]}")
        
        # 智能选择字幕文件：优先选择已翻译的中文字幕
        selected_subtitle = None
        
        # 1. 优先选择已翻译的中文字幕
        for subtitle_file in subtitle_files:
            if 'zh-CN' in subtitle_file.name or 'zh-Hans' in subtitle_file.name:
                selected_subtitle = subtitle_file
                print(f"✓ 选择已翻译的中文字幕: {selected_subtitle.name}")
                break
        
        # 2. 如果没有中文字幕，选择英文字幕
        if not selected_subtitle:
            for subtitle_file in subtitle_files:
                if 'en' in subtitle_file.name:
                    selected_subtitle = subtitle_file
                    print(f"✓ 选择英文字幕: {selected_subtitle.name}")
                    break
        
        # 3. 如果还没有选择，选择第一个字幕文件
        if not selected_subtitle:
            selected_subtitle = subtitle_files[0]
            print(f"✓ 选择字幕文件: {selected_subtitle.name}")
        
        # 直接处理现有文件
        process_existing_files(str(video_file), str(selected_subtitle), target_language, embed_type, output_file)
        return
    else:
        print("⚠ 未找到字幕文件，继续下载流程")
    
    # 2. 下载视频和字幕
    print("开始下载YouTube视频...")
    download_result = download_youtube_video(url)
    print(f"✓ 视频下载完成: {download_result['title']}")
    print(f"✓ 视频文件: {download_result['video_file']}")
    
    # 2. 检查字幕
    if not download_result['subtitles']:
        print("⚠ 未找到字幕文件，跳过字幕处理")
        return
    
    print(f"✓ 找到字幕文件: {list(download_result['subtitles'].keys())}")
    
    # 3. 智能字幕选择
    subtitle_file = None
    
    # 优先检查是否已有中文字幕
    chinese_subtitles = []
    for lang in ['zh', 'zh-Hans', 'zh-Hant', 'zh-CN', 'zh-TW']:
        if lang in download_result['subtitles']:
            chinese_subtitles.append((lang, download_result['subtitles'][lang]))
    
    if chinese_subtitles:
        # 使用现有的中文字幕，跳过翻译
        lang, subtitle_file = chinese_subtitles[0]
        print(f"✓ 使用现有中文字幕({lang}): {subtitle_file}")
        print("提示: 检测到中文字幕已存在，跳过翻译步骤")
    elif 'en' in download_result['subtitles']:
        # 只有英文字幕时进行翻译
        print("\n" + "=" * 50)
        print("开始翻译英文字幕...")
        print("=" * 50)
        
        english_subtitle = download_result['subtitles']['en']
        subtitle_file = translate_subtitle(english_subtitle, target_language)
        print(f"✓ 字幕翻译完成: {subtitle_file}")
    else:
        print("⚠ 没有找到可用的字幕文件")
        return
    
    # 4. 合成字幕到视频
    print("\n" + "=" * 50)
    print("开始合成字幕到视频...")
    print("=" * 50)
    
    video_file = download_result['video_file']
    
    if embed_type == 'soft':
        final_video = embed_subtitle_to_video(video_file, subtitle_file, output_file)
        print(f"✓ 软字幕嵌入完成: {final_video}")
        print("提示: 软字幕可以在播放器中开关")
    else:
        final_video = burn_subtitle_to_video(video_file, subtitle_file, output_file)
        print(f"✓ 硬字幕烧录完成: {final_video}")
        print("提示: 硬字幕永久嵌入视频中")
    
    print("\n" + "=" * 50)
    print("处理完成!")
    print("=" * 50)
    print(f"最终视频文件: {final_video}")


def process_existing_files(video_file: str, subtitle_file: str, target_language: str, 
                          embed_type: str, output_file: Optional[str]):
    """处理现有文件"""
    print("=" * 50)
    print("开始处理现有文件...")
    print("=" * 50)
    
    # 检查文件是否存在
    if not Path(video_file).exists():
        raise FileNotFoundError(f"视频文件不存在: {video_file}")
    if not Path(subtitle_file).exists():
        raise FileNotFoundError(f"字幕文件不存在: {subtitle_file}")
    
    # 翻译字幕（如果需要）
    if target_language != 'en':
        print("开始翻译字幕...")
        subtitle_file = translate_subtitle(subtitle_file, target_language)
        print(f"✓ 字幕翻译完成: {subtitle_file}")
    
    # 合成字幕到视频
    if embed_type == 'soft':
        final_video = embed_subtitle_to_video(video_file, subtitle_file, output_file)
        print(f"✓ 软字幕嵌入完成: {final_video}")
    else:
        final_video = burn_subtitle_to_video(video_file, subtitle_file, output_file)
        print(f"✓ 硬字幕烧录完成: {final_video}")
    
    print("\n" + "=" * 50)
    print("处理完成!")
    print("=" * 50)
    print(f"最终视频文件: {final_video}")


if __name__ == "__main__":
    main()
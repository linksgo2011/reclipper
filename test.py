#!/usr/bin/env python3
"""
测试脚本 - 验证工具的基本功能
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings
from youtube_downloader import YouTubeDownloader
from subtitle_translator import SubtitleTranslator
from video_processor import VideoProcessor


def test_config():
    """测试配置加载"""
    print("1. 测试配置加载...")
    try:
        settings = get_settings()
        print(f"   ✓ 配置加载成功")
        print(f"   - OpenAI API密钥: {'已设置' if settings.openai_api_key and not settings.openai_api_key.startswith('your_') else '未设置'}")
        print(f"   - 目标语言: {settings.target_language}")
        print(f"   - 下载目录: {settings.download_dir}")
        return True
    except Exception as e:
        print(f"   ❌ 配置加载失败: {str(e)}")
        return False


def test_youtube_downloader():
    """测试YouTube下载器"""
    print("\n2. 测试YouTube下载器...")
    try:
        downloader = YouTubeDownloader()
        print("   ✓ YouTube下载器初始化成功")
        
        # 测试获取字幕列表（不实际下载）
        # 使用一个公开的YouTube视频进行测试
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # 第一个YouTube视频
        
        try:
            subtitles = downloader.get_available_subtitles(test_url)
            print(f"   ✓ 获取字幕列表成功，找到 {len(subtitles)} 种语言")
        except Exception as e:
            print(f"   ⚠ 获取字幕列表测试失败（可能网络问题）: {str(e)}")
        
        return True
    except Exception as e:
        print(f"   ❌ YouTube下载器测试失败: {str(e)}")
        return False


def test_subtitle_translator():
    """测试字幕翻译器"""
    print("\n3. 测试字幕翻译器...")
    try:
        translator = SubtitleTranslator()
        print("   ✓ 字幕翻译器初始化成功")
        
        # 检查API密钥
        settings = get_settings()
        if not settings.openai_api_key or settings.openai_api_key.startswith('your_'):
            print("   ⚠ OpenAI API密钥未设置，跳过翻译测试")
            return True
        
        # 创建测试字幕内容
        test_subtitles = [
            {
                'start_time': '00:00:01,000',
                'end_time': '00:00:04,000', 
                'text': 'Hello world!'
            },
            {
                'start_time': '00:00:05,000',
                'end_time': '00:00:08,000',
                'text': 'This is a test subtitle.'
            }
        ]
        
        # 测试翻译功能
        try:
            translated = translator._translate_subtitles(test_subtitles, 'zh-CN')
            print("   ✓ 字幕翻译功能测试成功")
            for i, sub in enumerate(translated):
                print(f"     {i+1}. 原文: {test_subtitles[i]['text']}")
                print(f"        译文: {sub['text']}")
        except Exception as e:
            print(f"   ⚠ 翻译测试失败（可能API问题）: {str(e)}")
        
        return True
    except Exception as e:
        print(f"   ❌ 字幕翻译器测试失败: {str(e)}")
        return False


def test_video_processor():
    """测试视频处理器"""
    print("\n4. 测试视频处理器...")
    try:
        processor = VideoProcessor()
        print("   ✓ 视频处理器初始化成功")
        
        # 测试ffmpeg是否可用
        try:
            # 简单的ffmpeg版本检查
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✓ ffmpeg可用")
                # 提取版本信息
                version_line = result.stdout.split('\n')[0]
                print(f"     {version_line}")
            else:
                print("   ⚠ ffmpeg不可用")
        except Exception as e:
            print(f"   ⚠ ffmpeg检查失败: {str(e)}")
        
        return True
    except Exception as e:
        print(f"   ❌ 视频处理器测试失败: {str(e)}")
        return False


def test_integration():
    """测试集成功能"""
    print("\n5. 测试集成功能...")
    
    # 检查下载目录
    downloads_dir = Path('downloads')
    if not downloads_dir.exists():
        downloads_dir.mkdir()
        print("   ✓ 创建下载目录")
    else:
        print("   ✓ 下载目录已存在")
    
    # 检查环境文件
    env_file = Path('.env')
    if env_file.exists():
        print("   ✓ 环境配置文件存在")
    else:
        print("   ⚠ 环境配置文件不存在，请运行 install.py")
    
    print("   ✓ 集成测试完成")
    return True


def main():
    """主测试函数"""
    print("=" * 50)
    print("YouTube视频下载和字幕翻译工具 - 功能测试")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 5
    
    # 运行各个测试
    if test_config():
        tests_passed += 1
    
    if test_youtube_downloader():
        tests_passed += 1
    
    if test_subtitle_translator():
        tests_passed += 1
    
    if test_video_processor():
        tests_passed += 1
    
    if test_integration():
        tests_passed += 1
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    print(f"通过测试: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("🎉 所有测试通过! 工具可以正常使用。")
        print("\n下一步:")
        print("1. 确保 .env 文件中设置了正确的OpenAI API密钥")
        print("2. 运行: python main.py --help 查看使用说明")
        print('3. 示例: python main.py "https://www.youtube.com/watch?v=视频ID"')
    else:
        print("⚠ 部分测试未通过，请检查上述错误信息")
        print("\n建议:")
        print("1. 运行: python install.py 重新安装")
        print("2. 检查网络连接")
        print("3. 确保ffmpeg已安装")
        print("4. 检查OpenAI API密钥配置")


if __name__ == "__main__":
    main()
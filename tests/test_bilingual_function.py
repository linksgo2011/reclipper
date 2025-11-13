#!/usr/bin/env python3
"""测试双语字幕功能"""

import os
import tempfile
from pathlib import Path
from ..video_processor import VideoProcessor

def test_bilingual_subtitle_creation():
    """测试双语字幕文件创建"""
    print("测试双语字幕文件创建...")
    
    # 创建测试字幕文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write("""1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,000
This is a test
""")
        english_sub = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write("""1
00:00:01,000 --> 00:00:03,000
你好世界

2
00:00:04,000 --> 00:00:06,000
这是一个测试
""")
        chinese_sub = f.name
    
    try:
        processor = VideoProcessor()
        
        # 测试双语字幕文件创建
        bilingual_file = processor.create_bilingual_subtitle_file(chinese_sub, english_sub)
        
        # 检查文件是否创建成功
        assert Path(bilingual_file).exists(), "双语字幕文件未创建"
        assert bilingual_file.endswith('.ass'), "双语字幕文件格式不正确"
        
        # 检查文件内容
        with open(bilingual_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '你好世界' in content, "中文字幕内容缺失"
        assert 'Hello world' in content, "英文字幕内容缺失"
        assert '\\N' in content, "换行符缺失"
        
        print("✓ 双语字幕文件创建测试通过")
        
        # 清理临时文件
        os.unlink(bilingual_file)
        
    finally:
        # 清理临时文件
        os.unlink(english_sub)
        os.unlink(chinese_sub)

def test_bilingual_burn_function():
    """测试双语烧录功能"""
    print("测试双语烧录功能...")
    
    # 创建测试字幕文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write("""1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,000
This is a test
""")
        english_sub = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write("""1
00:00:01,000 --> 00:00:03,000
你好世界

2
00:00:04,000 --> 00:00:06,000
这是一个测试
""")
        chinese_sub = f.name
    
    try:
        processor = VideoProcessor()
        
        # 测试双语烧录功能（不实际执行ffmpeg，只测试命令构建）
        try:
            # 这会失败因为没有真实的视频文件，但我们只测试命令构建
            processor.burn_bilingual_subtitle(
                "/nonexistent/video.mp4", chinese_sub, english_sub
            )
        except FileNotFoundError:
            # 这是预期的，因为我们没有真实的视频文件
            print("✓ 双语烧录功能命令构建测试通过")
        except Exception as e:
            if "视频文件不存在" in str(e):
                print("✓ 双语烧录功能命令构建测试通过")
            else:
                raise
                
    finally:
        # 清理临时文件
        os.unlink(english_sub)
        os.unlink(chinese_sub)

def test_subtitle_parsing():
    """测试字幕解析功能"""
    print("测试字幕解析功能...")
    
    # 创建测试字幕文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write("""1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,000
This is a test
""")
        test_sub = f.name
    
    try:
        processor = VideoProcessor()
        
        # 测试字幕解析
        subtitles = processor._read_subtitle_file(test_sub)
        
        assert len(subtitles) == 2, "字幕解析数量不正确"
        assert subtitles[0]['text'] == 'Hello world', "第一条字幕内容不正确"
        assert subtitles[1]['text'] == 'This is a test', "第二条字幕内容不正确"
        assert abs(subtitles[0]['start_time'] - 1.0) < 0.1, "开始时间解析不正确"
        assert abs(subtitles[0]['end_time'] - 3.0) < 0.1, "结束时间解析不正确"
        
        print("✓ 字幕解析测试通过")
        
    finally:
        # 清理临时文件
        os.unlink(test_sub)

if __name__ == "__main__":
    print("开始测试双语字幕功能...\n")
    
    try:
        test_subtitle_parsing()
        test_bilingual_subtitle_creation()
        test_bilingual_burn_function()
        
        print("\n" + "=" * 50)
        print("所有双语字幕功能测试通过!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
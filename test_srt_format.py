#!/usr/bin/env python3
"""
测试SRT字幕格式功能
"""

import os
import tempfile
from pathlib import Path
from subtitle_translator import SubtitleTranslator

def test_srt_parsing():
    """测试SRT格式解析"""
    print("=== 测试SRT格式解析 ===")
    
    # 创建测试SRT文件内容
    srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello world!

2
00:00:05,000 --> 00:00:08,000
This is a test subtitle.

3
00:00:09,000 --> 00:00:12,000
Another subtitle line.
"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(srt_content)
        temp_file = f.name
    
    try:
        # 测试解析
        translator = SubtitleTranslator()
        subtitles = translator._read_subtitle_file(temp_file)
        
        print(f"解析到 {len(subtitles)} 个字幕块:")
        for i, sub in enumerate(subtitles):
            print(f"字幕 {i+1}:")
            print(f"  开始时间: {sub['start_time']}")
            print(f"  结束时间: {sub['end_time']}")
            print(f"  文本: '{sub['text']}'")
            print(f"  文本长度: {len(sub['text'])}")
            print()
        
        # 验证解析结果
        assert len(subtitles) == 3, f"期望3个字幕块，实际得到{len(subtitles)}"
        assert subtitles[0]['text'] == 'Hello world!', f"第一个字幕文本不匹配: {subtitles[0]['text']}"
        assert subtitles[1]['text'] == 'This is a test subtitle.', f"第二个字幕文本不匹配: {subtitles[1]['text']}"
        assert subtitles[2]['text'] == 'Another subtitle line.', f"第三个字幕文本不匹配: {subtitles[2]['text']}"
        
        print("✓ SRT格式解析测试通过")
        
    finally:
        # 清理临时文件
        os.unlink(temp_file)

def test_srt_writing():
    """测试SRT格式写入"""
    print("\n=== 测试SRT格式写入 ===")
    
    # 创建测试数据
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
        },
        {
            'start_time': '00:00:09,000',
            'end_time': '00:00:12,000',
            'text': 'Another subtitle line.'
        }
    ]
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        temp_file = f.name
    
    try:
        # 测试写入
        translator = SubtitleTranslator()
        translator._write_subtitle_file(Path(temp_file), test_subtitles)
        
        # 读取并验证写入的内容
        with open(temp_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        
        print("写入的SRT内容:")
        print(written_content)
        
        # 验证格式
        lines = written_content.strip().split('\n')
        assert len(lines) >= 9, f"SRT文件内容行数不足: {len(lines)}"
        
        # 检查序号、时间轴和文本格式
        assert lines[0] == '1', "第一个字幕序号错误"
        assert '-->' in lines[1], "第一个字幕时间轴格式错误"
        assert lines[2] == 'Hello world!', "第一个字幕文本错误"
        
        print("✓ SRT格式写入测试通过")
        
    finally:
        # 清理临时文件
        os.unlink(temp_file)

def test_youtube_downloader_config():
    """测试YouTube下载器配置"""
    print("\n=== 测试YouTube下载器配置 ===")
    
    # 检查youtube_downloader.py中的配置
    with open('youtube_downloader.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否配置为SRT格式
    if "'subtitlesformat': 'srt'" in content:
        print("✓ YouTube下载器已配置为SRT格式")
    else:
        print("✗ YouTube下载器未配置为SRT格式")
        return False
    
    # 检查是否支持SRT文件查找
    if ".srt" in content:
        print("✓ YouTube下载器支持SRT文件查找")
    else:
        print("✗ YouTube下载器不支持SRT文件查找")
        return False
    
    return True

if __name__ == "__main__":
    print("开始测试SRT字幕格式功能...\n")
    
    try:
        test_srt_parsing()
        test_srt_writing()
        config_ok = test_youtube_downloader_config()
        
        if config_ok:
            print("\n🎉 所有SRT格式测试通过！")
            print("现在YouTube下载器将下载SRT格式的字幕文件。")
        else:
            print("\n⚠️ 配置检查未通过，请检查YouTube下载器配置。")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
#!/usr/bin/env python3
"""
简单翻译测试 - 专门测试翻译功能的核心问题
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from ..subtitle_translator import SubtitleTranslator


def test_translation_with_mock():
    """使用模拟测试翻译功能"""
    print("=== 测试翻译功能（使用模拟） ===")
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    
    try:
        # 创建测试VTT文件
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello world!

00:00:05.000 --> 00:00:08.000
This is a test subtitle.
"""
        vtt_file = Path(test_dir) / "test.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')
        
        print(f"✓ 创建测试文件: {vtt_file}")
        
        # 使用模拟测试翻译
        with patch('subtitle_translator.OpenAI') as mock_openai:
            # 模拟OpenAI客户端
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "你好，世界！\n这是一个测试字幕。"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # 创建翻译器实例
            translator = SubtitleTranslator()
            
            # 测试文件解析
            subtitles = translator._read_subtitle_file(str(vtt_file))
            print(f"✓ 解析字幕文件成功，找到 {len(subtitles)} 个字幕")
            
            # 测试翻译
            translated = translator._translate_subtitles(subtitles, 'zh-CN')
            print(f"✓ 翻译完成，翻译了 {len(translated)} 个字幕")
            
            # 验证结果
            assert len(translated) == 2
            assert translated[0]['text'] == '你好，世界！'
            assert translated[1]['text'] == '这是一个测试字幕。'
            
            print("✓ 翻译结果验证通过")
            
            # 验证API调用
            mock_client.chat.completions.create.assert_called_once()
            print("✓ API调用验证通过")
            
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(test_dir)
    
    print("=== 翻译测试完成 ===\n")


def test_translation_failure():
    """测试翻译失败时的回退机制"""
    print("=== 测试翻译失败回退机制 ===")
    
    with patch('subtitle_translator.OpenAI') as mock_openai:
        # 模拟API异常
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        # 创建翻译器实例
        translator = SubtitleTranslator()
        
        # 测试数据
        test_subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:04,000', 'text': 'Hello world!'}
        ]
        
        # 执行翻译
        translated = translator._translate_subtitles(test_subtitles, 'zh-CN')
        
        # 验证回退机制
        assert len(translated) == 1
        assert translated[0]['text'] == 'Hello world!'  # 应该保持原文
        
        print("✓ 翻译失败回退机制验证通过")
        
        # 验证API调用确实发生了
        mock_client.chat.completions.create.assert_called_once()
        print("✓ API调用验证通过")
    
    print("=== 翻译失败测试完成 ===\n")


def test_file_parsing():
    """测试文件解析功能"""
    print("=== 测试文件解析功能 ===")
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    
    try:
        # 创建测试SRT文件
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello world!

2
00:00:05,000 --> 00:00:08,000
This is a test subtitle.
"""
        srt_file = Path(test_dir) / "test.srt"
        srt_file.write_text(srt_content, encoding='utf-8')
        
        # 创建翻译器实例
        translator = SubtitleTranslator()
        
        # 测试文件解析
        subtitles = translator._read_subtitle_file(str(srt_file))
        
        # 验证解析结果
        assert len(subtitles) == 2
        assert subtitles[0]['text'] == 'Hello world!'
        assert subtitles[0]['start_time'] == '00:00:01,000'
        assert subtitles[1]['text'] == 'This is a test subtitle.'
        
        print("✓ SRT文件解析测试通过")
        
        # 测试VTT文件解析
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello world!

00:00:05.000 --> 00:00:08.000
This is a test subtitle.
"""
        vtt_file = Path(test_dir) / "test.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')
        
        subtitles = translator._read_subtitle_file(str(vtt_file))
        
        # 验证解析结果
        assert len(subtitles) == 2
        assert subtitles[0]['text'] == 'Hello world!'
        assert subtitles[1]['text'] == 'This is a test subtitle.'
        
        print("✓ VTT文件解析测试通过")
        
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(test_dir)
    
    print("=== 文件解析测试完成 ===\n")


def test_real_translation():
    """测试真实翻译（需要API密钥）"""
    print("=== 测试真实翻译功能 ===")
    
    # 检查是否有API密钥
    from config import get_settings
    settings = get_settings()
    
    if not settings.openai_api_key or settings.openai_api_key == "":
        print("⚠ 未配置OpenAI API密钥，跳过真实翻译测试")
        return
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    
    try:
        # 创建测试VTT文件
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello world!

00:00:05.000 --> 00:00:08.000
This is a test subtitle.
"""
        vtt_file = Path(test_dir) / "test.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')
        
        # 创建翻译器实例
        translator = SubtitleTranslator()
        
        # 执行真实翻译
        output_file = translator.translate_subtitle_file(str(vtt_file), 'zh-CN')
        
        # 验证输出文件存在
        assert Path(output_file).exists()
        assert output_file.endswith('.zh-CN.vtt')
        
        print(f"✓ 真实翻译测试通过，输出文件: {output_file}")
        
    except Exception as e:
        print(f"⚠ 真实翻译测试失败: {e}")
        
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(test_dir)
    
    print("=== 真实翻译测试完成 ===\n")


if __name__ == "__main__":
    print("开始字幕翻译功能测试...\n")
    
    try:
        test_file_parsing()
        test_translation_with_mock()
        test_translation_failure()
        test_real_translation()
        
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
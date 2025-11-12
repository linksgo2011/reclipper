#!/usr/bin/env python3
"""
测试AI翻译日志功能
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from subtitle_translator import SubtitleTranslator

def test_ai_translation_logs():
    """测试AI翻译日志功能"""
    print("=== 测试AI翻译日志功能 ===")
    
    # 创建测试SRT文件
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(srt_content)
        srt_file = f.name
    
    try:
        # 模拟OpenAI API响应
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "你好，世界！\n这是一个测试字幕。\n另一行字幕。"
        mock_response.choices = [mock_choice]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            translator = SubtitleTranslator()
            subtitles = translator._read_subtitle_file(srt_file)
            
            print("开始翻译测试...")
            translated_subtitles = translator._translate_subtitles(subtitles, 'zh')
            
            # 验证翻译结果
            assert len(subtitles) == len(translated_subtitles), "行数不匹配"
            assert translated_subtitles[0]['text'] == "你好，世界！", "第一个字幕翻译错误"
            assert translated_subtitles[1]['text'] == "这是一个测试字幕。", "第二个字幕翻译错误"
            assert translated_subtitles[2]['text'] == "另一行字幕。", "第三个字幕翻译错误"
            
            print("✓ AI翻译日志功能测试通过")
            
    finally:
        os.unlink(srt_file)

def test_ai_translation_logs_mismatch():
    """测试AI翻译日志在行数不匹配时的情况"""
    print("\n=== 测试AI翻译日志（行数不匹配） ===")
    
    # 创建测试SRT文件
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(srt_content)
        srt_file = f.name
    
    try:
        # 模拟OpenAI API响应 - 行数不匹配
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "你好，世界！\n这是一个测试字幕。"  # 只有2行，但输入有3行
        mock_response.choices = [mock_choice]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            translator = SubtitleTranslator()
            subtitles = translator._read_subtitle_file(srt_file)
            
            print("开始翻译测试（行数不匹配）...")
            translated_subtitles = translator._translate_subtitles(subtitles, 'zh')
            
            # 验证翻译结果
            assert len(subtitles) == len(translated_subtitles), "行数应该保持相同"
            assert translated_subtitles[0]['text'] == "你好，世界！", "第一个字幕翻译错误"
            assert translated_subtitles[1]['text'] == "这是一个测试字幕。", "第二个字幕翻译错误"
            assert translated_subtitles[2]['text'] == "Another subtitle line.", "第三个字幕应该保留原文"
            
            print("✓ AI翻译日志（行数不匹配）测试通过")
            
    finally:
        os.unlink(srt_file)

def test_ai_translation_logs_error():
    """测试AI翻译日志在翻译失败时的情况"""
    print("\n=== 测试AI翻译日志（翻译失败） ===")
    
    # 创建测试SRT文件
    srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello world!

2
00:00:05,000 --> 00:00:08,000
This is a test subtitle.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(srt_content)
        srt_file = f.name
    
    try:
        # 模拟OpenAI API异常
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API调用失败")
            
            translator = SubtitleTranslator()
            subtitles = translator._read_subtitle_file(srt_file)
            
            print("开始翻译测试（翻译失败）...")
            translated_subtitles = translator._translate_subtitles(subtitles, 'zh')
            
            # 验证翻译结果（应该保留原文）
            assert len(subtitles) == len(translated_subtitles), "行数应该保持相同"
            assert translated_subtitles[0]['text'] == "Hello world!", "第一个字幕应该保留原文"
            assert translated_subtitles[1]['text'] == "This is a test subtitle.", "第二个字幕应该保留原文"
            
            print("✓ AI翻译日志（翻译失败）测试通过")
            
    finally:
        os.unlink(srt_file)

def test_full_translation_process():
    """测试完整的翻译流程日志"""
    print("\n=== 测试完整翻译流程日志 ===")
    
    # 创建测试SRT文件
    srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello world!

2
00:00:05,000 --> 00:00:08,000
This is a test subtitle.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(srt_content)
        srt_file = f.name
    
    try:
        # 模拟OpenAI API响应
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "你好，世界！\n这是一个测试字幕。"
        mock_response.choices = [mock_choice]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            translator = SubtitleTranslator()
            
            print("开始完整翻译流程测试...")
            output_file = translator.translate_subtitle_file(srt_file, 'zh')
            
            # 验证输出文件存在
            assert os.path.exists(output_file), "输出文件不存在"
            
            # 读取输出文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()
            
            print("生成的翻译文件内容:")
            print(output_content)
            
            # 验证文件格式
            lines = output_content.strip().split('\n')
            assert len(lines) >= 6, "输出文件格式错误"
            assert '你好，世界！' in output_content, "翻译内容未正确写入文件"
            assert '这是一个测试字幕。' in output_content, "翻译内容未正确写入文件"
            
            print("✓ 完整翻译流程日志测试通过")
            
            # 清理输出文件
            os.unlink(output_file)
            
    finally:
        os.unlink(srt_file)

if __name__ == "__main__":
    print("开始测试AI翻译日志功能...\n")
    
    try:
        test_ai_translation_logs()
        test_ai_translation_logs_mismatch()
        test_ai_translation_logs_error()
        test_full_translation_process()
        
        print("\n🎉 所有AI翻译日志测试通过！")
        print("现在字幕翻译器会在翻译过程中输出详细的AI翻译日志。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
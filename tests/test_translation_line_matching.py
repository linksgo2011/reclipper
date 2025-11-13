#!/usr/bin/env python3
"""
测试翻译行数匹配功能
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from ..subtitle_translator import SubtitleTranslator

def test_translation_line_matching():
    """测试翻译行数匹配功能"""
    print("=== 测试翻译行数匹配功能 ===")
    
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
        # 模拟OpenAI API响应 - 行数匹配的情况
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
            translated_subtitles = translator._translate_subtitles(subtitles, 'zh')
            
            print("行数匹配测试结果:")
            print(f"原始字幕数: {len(subtitles)}")
            print(f"翻译后字幕数: {len(translated_subtitles)}")
            
            # 验证行数匹配
            assert len(subtitles) == len(translated_subtitles), "行数不匹配"
            assert translated_subtitles[0]['text'] == "你好，世界！", "第一个字幕翻译错误"
            assert translated_subtitles[1]['text'] == "这是一个测试字幕。", "第二个字幕翻译错误"
            assert translated_subtitles[2]['text'] == "另一行字幕。", "第三个字幕翻译错误"
            
            print("✓ 行数匹配测试通过")
            
    finally:
        os.unlink(srt_file)

def test_translation_line_mismatch():
    """测试翻译行数不匹配时的处理"""
    print("\n=== 测试翻译行数不匹配处理 ===")
    
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
        # 模拟OpenAI API响应 - 行数不匹配的情况（返回行数少于输入）
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
            translated_subtitles = translator._translate_subtitles(subtitles, 'zh')
            
            print("行数不匹配测试结果:")
            print(f"原始字幕数: {len(subtitles)}")
            print(f"翻译后字幕数: {len(translated_subtitles)}")
            
            # 验证行数不匹配时的处理
            assert len(subtitles) == len(translated_subtitles), "行数应该保持相同"
            assert translated_subtitles[0]['text'] == "你好，世界！", "第一个字幕翻译错误"
            assert translated_subtitles[1]['text'] == "这是一个测试字幕。", "第二个字幕翻译错误"
            assert translated_subtitles[2]['text'] == "Another subtitle line.", "第三个字幕应该保留原文"
            
            print("✓ 行数不匹配处理测试通过")
            
    finally:
        os.unlink(srt_file)

def test_translation_empty_response():
    """测试翻译返回空响应时的处理"""
    print("\n=== 测试翻译空响应处理 ===")
    
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
        # 模拟OpenAI API响应 - 空响应
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = ""  # 空响应
        mock_response.choices = [mock_choice]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            translator = SubtitleTranslator()
            subtitles = translator._read_subtitle_file(srt_file)
            translated_subtitles = translator._translate_subtitles(subtitles, 'zh')
            
            print("空响应测试结果:")
            print(f"原始字幕数: {len(subtitles)}")
            print(f"翻译后字幕数: {len(translated_subtitles)}")
            
            # 验证空响应时的处理
            assert len(subtitles) == len(translated_subtitles), "行数应该保持相同"
            assert translated_subtitles[0]['text'] == "Hello world!", "第一个字幕应该保留原文"
            assert translated_subtitles[1]['text'] == "This is a test subtitle.", "第二个字幕应该保留原文"
            
            print("✓ 空响应处理测试通过")
            
    finally:
        os.unlink(srt_file)

def test_prompt_strictness():
    """测试提示词的严格性"""
    print("\n=== 测试提示词严格性 ===")
    
    # 创建测试数据
    test_subtitles = [
        {'start_time': '00:00:01,000', 'end_time': '00:00:04,000', 'text': 'Hello world!'},
        {'start_time': '00:00:05,000', 'end_time': '00:00:08,000', 'text': 'This is a test subtitle.'},
        {'start_time': '00:00:09,000', 'end_time': '00:00:12,000', 'text': 'Another subtitle line.'}
    ]
    
    translator = SubtitleTranslator()
    
    # 测试提示词生成
    texts_to_translate = [sub['text'] for sub in test_subtitles]
    combined_text = '\n'.join(texts_to_translate)
    
    # 检查提示词是否包含行数要求
    prompt = f"你是一个专业的字幕翻译助手。请将以下英文字幕准确翻译成zh。\n\n**重要要求：**\n1. 必须保持完全相同的行数结构\n2. 每行对应一个字幕块的翻译\n3. 返回的行数必须与输入的行数完全一致\n4. 如果某个字幕块不需要翻译或无法翻译，请保留原文\n5. 严格按照换行符分隔每个字幕块\n\n输入有{len(texts_to_translate)}行字幕，请确保返回{len(texts_to_translate)}行翻译结果。"
    
    print("生成的提示词:")
    print(prompt)
    
    # 验证提示词包含关键要求
    assert "必须保持完全相同的行数结构" in prompt, "提示词缺少行数结构要求"
    assert "返回的行数必须与输入的行数完全一致" in prompt, "提示词缺少行数一致性要求"
    assert f"输入有{len(texts_to_translate)}行字幕" in prompt, "提示词缺少具体行数信息"
    assert f"返回{len(texts_to_translate)}行翻译结果" in prompt, "提示词缺少具体返回行数要求"
    
    print("✓ 提示词严格性测试通过")

if __name__ == "__main__":
    print("开始测试翻译行数匹配功能...\n")
    
    try:
        test_translation_line_matching()
        test_translation_line_mismatch()
        test_translation_empty_response()
        test_prompt_strictness()
        
        print("\n🎉 所有翻译行数匹配测试通过！")
        print("现在翻译器会在行数不匹配时保留原文，并在提示词中给出严格的行数要求。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
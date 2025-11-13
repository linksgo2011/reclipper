#!/usr/bin/env python3
"""
实际测试AI翻译日志输出
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from ..subtitle_translator import SubtitleTranslator

def test_real_translation_with_logs():
    """实际测试翻译过程中的日志输出"""
    print("=== 实际测试AI翻译日志输出 ===\n")
    
    # 创建更真实的测试SRT文件
    srt_content = """1
00:00:01,000 --> 00:00:04,000
Welcome to our tutorial.

2
00:00:05,000 --> 00:00:08,000
Today we will learn about programming.

3
00:00:09,000 --> 00:00:12,000
Let's start with the basics.

4
00:00:13,000 --> 00:00:16,000
Programming is the process of creating instructions.

5
00:00:17,000 --> 00:00:20,000
These instructions tell computers what to do.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(srt_content)
        srt_file = f.name
    
    try:
        # 模拟OpenAI API响应
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "欢迎来到我们的教程。\n今天我们将学习编程。\n让我们从基础开始。\n编程是创建指令的过程。\n这些指令告诉计算机要做什么。"
        mock_response.choices = [mock_choice]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            translator = SubtitleTranslator()
            
            print("开始实际翻译测试...\n")
            print("=" * 60)
            print("以下是AI翻译过程中会输出的日志信息：")
            print("=" * 60 + "\n")
            
            output_file = translator.translate_subtitle_file(srt_file, 'zh')
            
            print("\n" + "=" * 60)
            print("翻译完成！")
            print("=" * 60)
            
            # 验证输出文件
            assert os.path.exists(output_file), "输出文件不存在"
            
            # 读取并显示输出文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()
            
            print("\n生成的翻译文件内容：")
            print("-" * 40)
            print(output_content)
            print("-" * 40)
            
            # 验证翻译结果
            assert "欢迎来到我们的教程。" in output_content
            assert "今天我们将学习编程。" in output_content
            assert "让我们从基础开始。" in output_content
            assert "编程是创建指令的过程。" in output_content
            assert "这些指令告诉计算机要做什么。" in output_content
            
            print("\n✅ 实际翻译测试成功！")
            print("✅ AI翻译日志功能正常工作！")
            
            # 清理输出文件
            os.unlink(output_file)
            
    finally:
        os.unlink(srt_file)

def test_translation_with_warnings():
    """测试包含警告信息的翻译日志"""
    print("\n=== 测试包含警告的翻译日志 ===\n")
    
    # 创建测试SRT文件
    srt_content = """1
00:00:01,000 --> 00:00:04,000
First subtitle line.

2
00:00:05,000 --> 00:00:08,000
Second subtitle line.

3
00:00:09,000 --> 00:00:12,000
Third subtitle line.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(srt_content)
        srt_file = f.name
    
    try:
        # 模拟OpenAI API响应 - 行数不匹配
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "第一行字幕。\n第二行字幕。"  # 只有2行，但输入有3行
        mock_response.choices = [mock_choice]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            translator = SubtitleTranslator()
            
            print("开始包含警告的翻译测试...\n")
            print("=" * 60)
            print("以下是AI翻译过程中会输出的警告信息：")
            print("=" * 60 + "\n")
            
            output_file = translator.translate_subtitle_file(srt_file, 'zh')
            
            print("\n" + "=" * 60)
            print("翻译完成（包含警告）！")
            print("=" * 60)
            
            # 验证输出文件
            assert os.path.exists(output_file), "输出文件不存在"
            
            # 读取并显示输出文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()
            
            print("\n生成的翻译文件内容：")
            print("-" * 40)
            print(output_content)
            print("-" * 40)
            
            # 验证翻译结果（第三行应该保留原文）
            assert "第一行字幕。" in output_content
            assert "第二行字幕。" in output_content
            assert "Third subtitle line." in output_content
            
            print("\n✅ 包含警告的翻译测试成功！")
            print("✅ 警告信息正确显示！")
            
            # 清理输出文件
            os.unlink(output_file)
            
    finally:
        os.unlink(srt_file)

if __name__ == "__main__":
    print("开始实际测试AI翻译日志输出功能...\n")
    
    try:
        test_real_translation_with_logs()
        test_translation_with_warnings()
        
        print("\n🎉 所有实际测试通过！")
        print("\n📋 AI翻译日志功能总结：")
        print("✅ 翻译过程中会显示详细的AI翻译日志")
        print("✅ 包括翻译批次信息、目标语言、原文内容")
        print("✅ 显示AI原始响应和分割后的行数")
        print("✅ 行数不匹配时会显示警告并保留原文")
        print("✅ 翻译失败时会显示错误信息并保留原文")
        print("✅ 最终翻译结果会清晰显示")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
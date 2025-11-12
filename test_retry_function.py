#!/usr/bin/env python3
"""
测试重试功能
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from subtitle_translator import SubtitleTranslator

def test_retry_success():
    """测试重试成功的情况"""
    print("=== 测试重试成功 ===")
    
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
        # 模拟OpenAI API响应 - 第一次行数不匹配，第二次匹配
        mock_response1 = Mock()
        mock_choice1 = Mock()
        mock_choice1.message.content = "你好，世界！"  # 只有1行，但输入有2行
        mock_response1.choices = [mock_choice1]
        
        mock_response2 = Mock()
        mock_choice2 = Mock()
        mock_choice2.message.content = "你好，世界！\n这是一个测试字幕。"  # 2行，匹配
        mock_response2.choices = [mock_choice2]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # 设置第一次返回行数不匹配，第二次返回匹配
            mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]
            
            translator = SubtitleTranslator()
            
            print("开始重试成功测试...")
            output_file = translator.translate_subtitle_file(srt_file, 'zh')
            
            # 验证输出文件存在
            assert os.path.exists(output_file), "输出文件不存在"
            
            # 读取输出文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()
            
            print("生成的翻译文件内容:")
            print(output_content)
            
            # 验证翻译结果
            assert "你好，世界！" in output_content
            assert "这是一个测试字幕。" in output_content
            
            print("✓ 重试成功测试通过")
            
            # 清理输出文件
            os.unlink(output_file)
            
    finally:
        os.unlink(srt_file)

def test_retry_failure():
    """测试重试失败的情况"""
    print("\n=== 测试重试失败 ===")
    
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
        # 模拟OpenAI API响应 - 始终行数不匹配
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "你好，世界！"  # 只有1行，但输入有2行
        mock_response.choices = [mock_choice]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # 设置始终返回行数不匹配
            mock_client.chat.completions.create.return_value = mock_response
            
            translator = SubtitleTranslator()
            
            print("开始重试失败测试...")
            
            try:
                output_file = translator.translate_subtitle_file(srt_file, 'zh')
                # 如果执行到这里，说明没有抛出异常，测试失败
                assert False, "应该抛出异常"
            except Exception as e:
                print(f"成功捕获异常: {e}")
                assert "经过 3 次重试后，行数仍然不匹配" in str(e)
                print("✓ 重试失败测试通过")
            
    finally:
        os.unlink(srt_file)

def test_no_retry_needed():
    """测试不需要重试的情况"""
    print("\n=== 测试不需要重试 ===")
    
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
        # 模拟OpenAI API响应 - 第一次就匹配
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "你好，世界！\n这是一个测试字幕。"  # 2行，匹配
        mock_response.choices = [mock_choice]
        
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response
            
            translator = SubtitleTranslator()
            
            print("开始不需要重试测试...")
            output_file = translator.translate_subtitle_file(srt_file, 'zh')
            
            # 验证输出文件存在
            assert os.path.exists(output_file), "输出文件不存在"
            
            # 读取输出文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()
            
            print("生成的翻译文件内容:")
            print(output_content)
            
            # 验证翻译结果
            assert "你好，世界！" in output_content
            assert "这是一个测试字幕。" in output_content
            
            print("✓ 不需要重试测试通过")
            
            # 清理输出文件
            os.unlink(output_file)
            
    finally:
        os.unlink(srt_file)

def test_api_error():
    """测试API错误的情况"""
    print("\n=== 测试API错误 ===")
    
    # 创建测试SRT文件
    srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello world!
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(srt_content)
        srt_file = f.name
    
    try:
        with patch('subtitle_translator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # 设置API调用异常
            mock_client.chat.completions.create.side_effect = Exception("API调用失败")
            
            translator = SubtitleTranslator()
            
            print("开始API错误测试...")
            
            try:
                output_file = translator.translate_subtitle_file(srt_file, 'zh')
                # 如果执行到这里，说明没有抛出异常，测试失败
                assert False, "应该抛出异常"
            except Exception as e:
                print(f"成功捕获异常: {e}")
                assert "API调用失败" in str(e)
                print("✓ API错误测试通过")
            
    finally:
        os.unlink(srt_file)

if __name__ == "__main__":
    print("开始测试重试功能...\n")
    
    try:
        test_no_retry_needed()
        test_retry_success()
        test_retry_failure()
        test_api_error()
        
        print("\n🎉 所有重试功能测试通过！")
        print("\n📋 重试功能总结：")
        print("✅ 行数匹配时直接返回翻译结果")
        print("✅ 行数不匹配时自动重试（最多3次）")
        print("✅ 重试成功后返回正确的翻译结果")
        print("✅ 重试失败后抛出异常，不保留原文")
        print("✅ API错误时抛出异常，不保留原文")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
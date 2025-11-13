#!/usr/bin/env python3
"""
测试修复后的翻译功能，验证变量引用错误和重试机制
"""

import unittest
from unittest.mock import Mock, patch
import json
from ..subtitle_translator import SubtitleTranslator


class TestFixedTranslation(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        self.translator = SubtitleTranslator()
        self.translator.settings.translation_model = "gpt-4o"
        
        # 模拟字幕数据
        self.subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:03,000', 'text': 'Hello world'},
            {'start_time': '00:00:04,000', 'end_time': '00:00:06,000', 'text': 'How are you?'},
            {'start_time': '00:00:07,000', 'end_time': '00:00:09,000', 'text': 'Good morning'}
        ]
    
    def test_json_parse_error_retry_success(self):
        """测试JSON解析错误时的重试机制"""
        # 模拟第一次返回无效JSON，第二次返回有效JSON
        mock_response1 = Mock()
        mock_choice1 = Mock()
        mock_message1 = Mock()
        mock_message1.content = "invalid json response"
        mock_choice1.message = mock_message1
        mock_response1.choices = [mock_choice1]
        
        mock_response2 = Mock()
        mock_choice2 = Mock()
        mock_message2 = Mock()
        valid_json = {
            "translated_subtitles": [
                {"original": "Hello world", "translated": "你好世界"},
                {"original": "How are you?", "translated": "你好吗？"},
                {"original": "Good morning", "translated": "早上好"}
            ]
        }
        mock_message2.content = json.dumps(valid_json)
        mock_choice2.message = mock_message2
        mock_response2.choices = [mock_choice2]
        
        with patch.object(self.translator.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = [mock_response1, mock_response2]
            
            result = self.translator._translate_batch(self.subtitles, "中文")
            
            # 验证结果
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]['text'], "你好世界")
            self.assertEqual(result[1]['text'], "你好吗？")
            self.assertEqual(result[2]['text'], "早上好")
            
            # 验证API被调用了2次
            self.assertEqual(mock_create.call_count, 2)
    
    def test_line_count_mismatch_retry_success(self):
        """测试行数不匹配时的重试机制"""
        # 模拟第一次返回行数不匹配，第二次返回正确行数
        mock_response1 = Mock()
        mock_choice1 = Mock()
        mock_message1 = Mock()
        invalid_json = {
            "translated_subtitles": [
                {"original": "Hello world", "translated": "你好世界"},
                {"original": "How are you?", "translated": "你好吗？"}
                # 缺少第三行
            ]
        }
        mock_message1.content = json.dumps(invalid_json)
        mock_choice1.message = mock_message1
        mock_response1.choices = [mock_choice1]
        
        mock_response2 = Mock()
        mock_choice2 = Mock()
        mock_message2 = Mock()
        valid_json = {
            "translated_subtitles": [
                {"original": "Hello world", "translated": "你好世界"},
                {"original": "How are you?", "translated": "你好吗？"},
                {"original": "Good morning", "translated": "早上好"}
            ]
        }
        mock_message2.content = json.dumps(valid_json)
        mock_choice2.message = mock_message2
        mock_response2.choices = [mock_choice2]
        
        with patch.object(self.translator.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = [mock_response1, mock_response2]
            
            result = self.translator._translate_batch(self.subtitles, "中文")
            
            # 验证结果
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]['text'], "你好世界")
            self.assertEqual(result[1]['text'], "你好吗？")
            self.assertEqual(result[2]['text'], "早上好")
            
            # 验证API被调用了2次
            self.assertEqual(mock_create.call_count, 2)
    
    def test_max_retries_exceeded(self):
        """测试超过最大重试次数时的异常处理"""
        # 模拟连续返回无效JSON
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "invalid json response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(self.translator.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = mock_response
            
            with self.assertRaises(Exception) as context:
                self.translator._translate_batch(self.subtitles, "中文")
            
            # 验证异常消息
            self.assertIn("经过 3 次重试后，仍然无法解析JSON响应", str(context.exception))
            
            # 验证API被调用了4次（初始1次 + 重试3次）
            self.assertEqual(mock_create.call_count, 4)
    
    def test_missing_fields_handling(self):
        """测试缺少字段时的容错处理"""
        # 模拟返回缺少translated字段的JSON
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        invalid_json = {
            "translated_subtitles": [
                {"original": "Hello world"},  # 缺少translated字段
                {"original": "How are you?", "translated": "你好吗？"},
                {"original": "Good morning", "translated": "早上好"}
            ]
        }
        mock_message.content = json.dumps(invalid_json)
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(self.translator.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = mock_response
            
            result = self.translator._translate_batch(self.subtitles, "中文")
            
            # 验证结果，第一个字幕应该使用原始文本
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]['text'], "Hello world")  # 使用原始文本
            self.assertEqual(result[1]['text'], "你好吗？")
            self.assertEqual(result[2]['text'], "早上好")


def test_actual_translation():
    """实际翻译测试"""
    print("\n=== 实际翻译测试 ===")
    
    translator = SubtitleTranslator()
    
    # 测试数据
    subtitles = [
        {'start_time': '00:00:01,000', 'end_time': '00:00:03,000', 'text': 'Hello world'},
        {'start_time': '00:00:04,000', 'end_time': '00:00:06,000', 'text': 'How are you?'},
        {'start_time': '00:00:07,000', 'end_time': '00:00:09,000', 'text': 'Good morning'}
    ]
    
    try:
        result = translator._translate_batch(subtitles, "中文")
        print(f"翻译成功，得到 {len(result)} 个字幕")
        for i, sub in enumerate(result, 1):
            print(f"  {i}. {sub['text']}")
        return True
    except Exception as e:
        print(f"翻译失败: {e}")
        return False


if __name__ == '__main__':
    # 运行单元测试
    unittest.main(verbosity=2)
    
    # 运行实际翻译测试
    print("\n" + "="*50)
    print("运行实际翻译测试...")
    success = test_actual_translation()
    if success:
        print("实际翻译测试通过！")
    else:
        print("实际翻译测试失败！")
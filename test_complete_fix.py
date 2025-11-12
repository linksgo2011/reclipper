#!/usr/bin/env python3
"""
完整修复验证测试
验证"translated_lines变量未定义"错误修复和重试机制
"""

import json
import unittest
from unittest.mock import Mock, patch
from subtitle_translator import SubtitleTranslator

class TestCompleteFix(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.translator = SubtitleTranslator()
        
        # 创建测试字幕数据
        self.subtitles = [
            {'start_time': 0.0, 'end_time': 2.0, 'text': 'Hello world'},
            {'start_time': 2.0, 'end_time': 4.0, 'text': 'How are you?'},
            {'start_time': 4.0, 'end_time': 6.0, 'text': 'Good morning'}
        ]
    
    def test_variable_scope_fix(self):
        """测试变量作用域修复 - 确保不会出现'translated_lines'未定义错误"""
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
            
            # 这个调用不应该抛出"translated_lines未定义"错误
            result = self.translator._translate_batch(self.subtitles, "中文")
            
            # 验证结果
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]['text'], "你好世界")
            self.assertEqual(result[1]['text'], "你好吗？")
            self.assertEqual(result[2]['text'], "早上好")
            
            # 验证API被调用了2次（第一次失败，第二次成功）
            self.assertEqual(mock_create.call_count, 2)
    
    def test_bilingual_format_working(self):
        """测试中英对照格式正常工作"""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        valid_json = {
            "translated_subtitles": [
                {"original": "Hello world", "translated": "你好世界"},
                {"original": "How are you?", "translated": "你好吗？"},
                {"original": "Good morning", "translated": "早上好"}
            ]
        }
        mock_message.content = json.dumps(valid_json)
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(self.translator.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = mock_response
            
            result = self.translator._translate_batch(self.subtitles, "中文")
            
            # 验证中英对照格式正确处理
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]['text'], "你好世界")
            self.assertEqual(result[1]['text'], "你好吗？")
            self.assertEqual(result[2]['text'], "早上好")
    
    def test_error_handling_robustness(self):
        """测试错误处理的健壮性"""
        # 模拟连续3次返回无效JSON，第4次返回有效JSON
        mock_responses = []
        for i in range(3):
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = f"invalid json response {i}"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_responses.append(mock_response)
        
        # 第4次返回有效JSON
        mock_response4 = Mock()
        mock_choice4 = Mock()
        mock_message4 = Mock()
        valid_json = {
            "translated_subtitles": [
                {"original": "Hello world", "translated": "你好世界"},
                {"original": "How are you?", "translated": "你好吗？"},
                {"original": "Good morning", "translated": "早上好"}
            ]
        }
        mock_message4.content = json.dumps(valid_json)
        mock_choice4.message = mock_message4
        mock_response4.choices = [mock_choice4]
        mock_responses.append(mock_response4)
        
        with patch.object(self.translator.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = mock_responses
            
            result = self.translator._translate_batch(self.subtitles, "中文")
            
            # 验证重试机制正常工作
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]['text'], "你好世界")
            self.assertEqual(result[1]['text'], "你好吗？")
            self.assertEqual(result[2]['text'], "早上好")
            
            # 验证API被调用了4次（3次重试 + 1次成功）
            self.assertEqual(mock_create.call_count, 4)

if __name__ == '__main__':
    unittest.main()
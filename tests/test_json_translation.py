#!/usr/bin/env python3
"""
测试JSON格式字幕翻译功能
"""

import unittest
from unittest.mock import Mock, patch
import json
from ..subtitle_translator import SubtitleTranslator


class TestJSONTranslation(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.translator = SubtitleTranslator()
        
    def test_json_translation_success(self):
        """测试JSON格式翻译成功"""
        # 模拟字幕数据
        subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:03,000', 'text': 'Hello world'},
            {'start_time': '00:00:04,000', 'end_time': '00:00:06,000', 'text': 'How are you?'},
            {'start_time': '00:00:07,000', 'end_time': '00:00:09,000', 'text': 'Good morning'}
        ]
        
        # 模拟AI响应
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "translated_subtitles": ["你好世界", "你好吗？", "早上好"]
        })
        
        with patch.object(self.translator.client.chat.completions, 'create', return_value=mock_response):
            result = self.translator._translate_batch(subtitles, 'zh-CN')
            
            # 验证结果
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]['text'], "你好世界")
            self.assertEqual(result[1]['text'], "你好吗？")
            self.assertEqual(result[2]['text'], "早上好")
            
    def test_json_translation_retry_success(self):
        """测试JSON格式翻译重试成功"""
        subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:03,000', 'text': 'Hello world'},
            {'start_time': '00:00:04,000', 'end_time': '00:00:06,000', 'text': 'How are you?'}
        ]
        
        # 第一次响应行数不匹配
        mock_response1 = Mock()
        mock_response1.choices[0].message.content = json.dumps({
            "translated_subtitles": ["你好世界"]  # 只有1行，应该重试
        })
        
        # 第二次响应正确
        mock_response2 = Mock()
        mock_response2.choices[0].message.content = json.dumps({
            "translated_subtitles": ["你好世界", "你好吗？"]
        })
        
        mock_create = Mock()
        mock_create.side_effect = [mock_response1, mock_response2]
        
        with patch.object(self.translator.client.chat.completions, 'create', mock_create):
            result = self.translator._translate_batch(subtitles, 'zh-CN')
            
            # 验证结果
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['text'], "你好世界")
            self.assertEqual(result[1]['text'], "你好吗？")
            
    def test_json_translation_invalid_format(self):
        """测试JSON格式错误"""
        subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:03,000', 'text': 'Hello world'}
        ]
        
        # 模拟无效JSON响应
        mock_response = Mock()
        mock_response.choices[0].message.content = "这不是有效的JSON"
        
        with patch.object(self.translator.client.chat.completions, 'create', return_value=mock_response):
            with self.assertRaises(Exception) as context:
                self.translator._translate_batch(subtitles, 'zh-CN')
            
            self.assertIn("AI响应格式错误，无法解析JSON", str(context.exception))
            
    def test_json_translation_missing_field(self):
        """测试JSON缺少必要字段"""
        subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:03,000', 'text': 'Hello world'}
        ]
        
        # 模拟缺少translated_subtitles字段的响应
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "other_field": ["一些内容"]
        })
        
        with patch.object(self.translator.client.chat.completions, 'create', return_value=mock_response):
            with self.assertRaises(Exception) as context:
                self.translator._translate_batch(subtitles, 'zh-CN')
            
            self.assertIn("行数仍然不匹配", str(context.exception))


def test_real_json_translation():
    """实际测试JSON格式翻译"""
    print("=== 测试JSON格式翻译功能 ===")
    
    translator = SubtitleTranslator()
    
    # 测试数据
    subtitles = [
        {'start_time': '00:00:01,000', 'end_time': '00:00:03,000', 'text': 'Hello, how are you today?'},
        {'start_time': '00:00:04,000', 'end_time': '00:00:06,000', 'text': 'I am fine, thank you.'},
        {'start_time': '00:00:07,000', 'end_time': '00:00:09,000', 'text': 'What about you?'}
    ]
    
    print(f"输入字幕数量: {len(subtitles)}")
    for i, sub in enumerate(subtitles, 1):
        print(f"  {i}. {sub['text']}")
    
    try:
        result = translator._translate_batch(subtitles, 'zh-CN')
        print(f"翻译成功! 输出字幕数量: {len(result)}")
        for i, sub in enumerate(result, 1):
            print(f"  {i}. {sub['text']}")
        return True
    except Exception as e:
        print(f"翻译失败: {e}")
        return False


if __name__ == '__main__':
    # 运行单元测试
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*50)
    
    # 运行实际测试
    success = test_real_json_translation()
    
    if success:
        print("\n✅ JSON格式翻译功能测试通过!")
    else:
        print("\n❌ JSON格式翻译功能测试失败!")
#!/usr/bin/env python3
"""
字幕翻译模块单元测试
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ..subtitle_translator import SubtitleTranslator, translate_subtitle


class TestSubtitleTranslator(unittest.TestCase):
    """字幕翻译器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.translator = SubtitleTranslator()
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_vtt_file_parsing(self):
        """测试VTT文件解析"""
        # 创建测试VTT文件
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello world!

00:00:05.000 --> 00:00:08.000
This is a test subtitle.
"""
        vtt_file = Path(self.test_dir) / "test.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')
        
        # 解析VTT文件
        subtitles = self.translator._read_subtitle_file(str(vtt_file))
        
        # 验证解析结果
        self.assertEqual(len(subtitles), 2)
        self.assertEqual(subtitles[0]['text'].strip(), 'Hello world!')  # 去除末尾空格
        self.assertEqual(subtitles[0]['start_time'], '00:00:01,000')
        self.assertEqual(subtitles[1]['text'].strip(), 'This is a test subtitle.')
    
    def test_srt_file_parsing(self):
        """测试SRT文件解析"""
        # 创建测试SRT文件
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello world!

2
00:00:05,000 --> 00:00:08,000
This is a test subtitle.
"""
        srt_file = Path(self.test_dir) / "test.srt"
        srt_file.write_text(srt_content, encoding='utf-8')
        
        # 解析SRT文件
        subtitles = self.translator._read_subtitle_file(str(srt_file))
        
        # 验证解析结果
        self.assertEqual(len(subtitles), 2)
        self.assertEqual(subtitles[0]['text'], 'Hello world!')
        self.assertEqual(subtitles[1]['text'], 'This is a test subtitle.')
    
    @patch('subtitle_translator.OpenAI')
    def test_translation_success(self, mock_openai):
        """测试成功翻译"""
        # 模拟OpenAI响应
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "你好，世界！\n这是一个测试字幕。"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 创建测试字幕数据
        test_subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:04,000', 'text': 'Hello world!'},
            {'start_time': '00:00:05,000', 'end_time': '00:00:08,000', 'text': 'This is a test subtitle.'}
        ]
        
        # 执行翻译
        translated = self.translator._translate_subtitles(test_subtitles, 'zh-CN')
        
        # 验证翻译结果
        self.assertEqual(len(translated), 2)
        self.assertEqual(translated[0]['text'], '你好，世界！')
        self.assertEqual(translated[1]['text'], '这是一个测试字幕。')
        
        # 验证API调用
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('subtitle_translator.OpenAI')
    def test_translation_failure(self, mock_openai):
        """测试翻译失败时的回退机制"""
        # 模拟API异常
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        # 创建测试字幕数据
        test_subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:04,000', 'text': 'Hello world!'}
        ]
        
        # 执行翻译（应该回退到原文）
        translated = self.translator._translate_subtitles(test_subtitles, 'zh-CN')
        
        # 验证回退机制
        self.assertEqual(len(translated), 1)
        self.assertEqual(translated[0]['text'], 'Hello world!')  # 保持原文
        
        # 验证API调用确实发生了
        mock_client.chat.completions.create.assert_called_once()
    
    def test_subtitle_file_creation(self):
        """测试字幕文件创建"""
        # 创建测试字幕数据
        test_subtitles = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:04,000', 'text': 'Hello world!'},
            {'start_time': '00:00:05,000', 'end_time': '00:00:08,000', 'text': 'This is a test.'}
        ]
        
        # 创建输出文件
        output_file = Path(self.test_dir) / "output.srt"
        self.translator._write_subtitle_file(output_file, test_subtitles)
        
        # 验证文件内容
        content = output_file.read_text(encoding='utf-8')
        self.assertIn('Hello world!', content)
        self.assertIn('This is a test.', content)
        self.assertIn('00:00:01,000 --> 00:00:04,000', content)
    
    @patch('subtitle_translator.SubtitleTranslator._translate_subtitles')
    def test_full_translation_workflow(self, mock_translate):
        """测试完整翻译流程"""
        # 模拟翻译结果
        mock_translate.return_value = [
            {'start_time': '00:00:01,000', 'end_time': '00:00:04,000', 'text': '你好世界!'}
        ]
        
        # 创建测试VTT文件
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello world!
"""
        input_file = Path(self.test_dir) / "input.vtt"
        input_file.write_text(vtt_content, encoding='utf-8')
        
        # 执行完整翻译
        output_file = self.translator.translate_subtitle_file(str(input_file), 'zh-CN')
        
        # 验证输出文件存在
        self.assertTrue(Path(output_file).exists())
        self.assertTrue(output_file.endswith('.zh-CN.vtt'))
    
    def test_translate_function(self):
        """测试便捷函数"""
        # 创建测试文件
        test_file = Path(self.test_dir) / "test.vtt"
        test_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nTest", encoding='utf-8')
        
        # 测试便捷函数
        with patch.object(SubtitleTranslator, 'translate_subtitle_file') as mock_method:
            mock_method.return_value = str(Path(self.test_dir) / "test.zh-CN.vtt")
            
            result = translate_subtitle(str(test_file))
            
            # 验证函数调用
            mock_method.assert_called_once()
            self.assertTrue(result.endswith('.zh-CN.vtt'))


class TestSubtitleEdgeCases(unittest.TestCase):
    """字幕翻译边界情况测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.translator = SubtitleTranslator()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_empty_vtt_file(self):
        """测试空VTT文件"""
        vtt_file = Path(self.test_dir) / "empty.vtt"
        vtt_file.write_text("", encoding='utf-8')
        
        subtitles = self.translator._read_subtitle_file(str(vtt_file))
        self.assertEqual(len(subtitles), 0)
    
    def test_vtt_with_notes(self):
        """测试包含注释的VTT文件"""
        vtt_content = """WEBVTT
NOTE This is a test note

00:00:01.000 --> 00:00:04.000
Hello world!

NOTE Another note
00:00:05.000 --> 00:00:08.000
Test subtitle
"""
        vtt_file = Path(self.test_dir) / "with_notes.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')
        
        subtitles = self.translator._read_subtitle_file(str(vtt_file))
        self.assertEqual(len(subtitles), 2)
        self.assertEqual(subtitles[0]['text'], 'Hello world!')
        self.assertEqual(subtitles[1]['text'], 'Test subtitle')
    
    def test_malformed_srt_file(self):
        """测试格式错误的SRT文件"""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Line 1

Invalid block
Some random text

2
00:00:05,000 --> 00:00:08,000
Line 2
"""
        srt_file = Path(self.test_dir) / "malformed.srt"
        srt_file.write_text(srt_content, encoding='utf-8')
        
        subtitles = self.translator._read_subtitle_file(str(srt_file))
        # 应该只解析有效的字幕块
        self.assertEqual(len(subtitles), 2)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
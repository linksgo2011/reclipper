import os
import re
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from config import get_settings


class SubtitleTranslator:
    """字幕翻译器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url
        )
    
    def translate_subtitle_file(self, subtitle_file: str, target_language: str = None) -> str:
        """
        翻译字幕文件
        
        Args:
            subtitle_file: 字幕文件路径
            target_language: 目标语言，默认为配置中的语言
            
        Returns:
            翻译后的字幕文件路径
        """
        if target_language is None:
            target_language = self.settings.target_language
        
        # 读取字幕文件
        subtitles = self._read_subtitle_file(subtitle_file)
        
        # 翻译字幕
        translated_subtitles = self._translate_subtitles(subtitles, target_language)
        
        # 生成输出文件路径
        input_path = Path(subtitle_file)
        output_file = input_path.parent / f"{input_path.stem}.{target_language}{input_path.suffix}"
        
        # 写入翻译后的字幕文件
        self._write_subtitle_file(output_file, translated_subtitles)
        
        return str(output_file)
    
    def _read_subtitle_file(self, file_path: str) -> List[Dict[str, Any]]:
        """读取字幕文件并解析为结构化数据"""
        subtitles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析SRT格式
        if file_path.endswith('.srt'):
            subtitles = self._parse_srt_content(content)
        # 解析VTT格式
        elif file_path.endswith('.vtt'):
            subtitles = self._parse_vtt_content(content)
        
        return subtitles
    
    def _parse_srt_content(self, content: str) -> List[Dict[str, Any]]:
        """解析SRT格式字幕"""
        subtitles = []
        
        # 分割字幕块
        blocks = re.split(r'\n\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    # 解析时间轴
                    time_line = lines[1]
                    time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', time_line)
                    
                    if time_match:
                        start_time = time_match.group(1)
                        end_time = time_match.group(2)
                        text = ' '.join(lines[2:])
                        
                        subtitles.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text.strip()
                        })
                except Exception:
                    continue
        
        return subtitles
    
    def _parse_vtt_content(self, content: str) -> List[Dict[str, Any]]:
        """解析VTT格式字幕"""
        subtitles = []
        
        # 移除VTT头部信息
        lines = content.split('\n')
        in_cue = False
        current_cue = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测时间轴行
            time_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})', line)
            if time_match:
                if current_cue:
                    subtitles.append(current_cue)
                current_cue = {
                    'start_time': time_match.group(1).replace('.', ','),
                    'end_time': time_match.group(2).replace('.', ','),
                    'text': ''
                }
                in_cue = True
            elif in_cue and line and not line.startswith('WEBVTT') and not line.startswith('NOTE'):
                current_cue['text'] += line + ' '
        
        if current_cue:
            # 去除文本末尾的空格
            current_cue['text'] = current_cue['text'].strip()
            subtitles.append(current_cue)
        
        return subtitles
    
    def _translate_subtitles(self, subtitles: List[Dict[str, Any]], target_language: str) -> List[Dict[str, Any]]:
        """翻译字幕内容"""
        translated_subtitles = []
        
        # 分批翻译以提高效率
        batch_size = 20
        for i in range(0, len(subtitles), batch_size):
            batch = subtitles[i:i + batch_size]
            translated_batch = self._translate_batch(batch, target_language)
            translated_subtitles.extend(translated_batch)
        
        return translated_subtitles
    
    def _translate_batch(self, subtitles: List[Dict[str, Any]], target_language: str) -> List[Dict[str, Any]]:
        """批量翻译字幕"""
        # 构建JSON格式的翻译文本
        texts_to_translate = [sub['text'] for sub in subtitles]
        json_input = {
            "subtitles": texts_to_translate,
            "count": len(texts_to_translate)
        }
        
        # 打印翻译前的原文
        print(f"\n=== AI翻译日志 ===")
        print(f"翻译批次: {len(subtitles)} 个字幕块")
        print(f"目标语言: {target_language}")
        print(f"原文内容:")
        for i, text in enumerate(texts_to_translate, 1):
            print(f"  {i}. {text}")
        
        try:
            # 调用OpenAI API进行翻译，使用JSON格式
            response = self.client.chat.completions.create(
                model=self.settings.translation_model,
                messages=[
                    {
                                    "role": "system",
                                    "content": f"你是一个专业的字幕翻译助手。请将以下JSON格式的字幕准确翻译成{target_language}。\n\n**重要要求：**\n1. 必须返回JSON格式的响应\n2. 保持完全相同的行数结构\n3. 返回的JSON必须包含'translated_subtitles'字段，该字段是一个数组\n4. 数组中的每个元素必须是一个对象，包含'original'（原文）和'translated'（译文）两个字段\n5. 数组长度必须与输入的字幕数量完全一致\n6. 严格按照输入的顺序进行翻译\n7. 每个字幕块的原文必须与输入完全一致\n8. 译文必须准确翻译原文内容\n\n**返回格式示例：**\n{{\"translated_subtitles\": [\n  {{\"original\": \"Hello world\", \"translated\": \"你好世界\"}},\n  {{\"original\": \"How are you?\", \"translated\": \"你好吗？\"}},\n  {{\"original\": \"Good morning\", \"translated\": \"早上好\"}}\n]}}"
                                },
                    {
                        "role": "user",
                        "content": str(json_input)
                    }
                ],
                temperature=1,
                max_completion_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # 解析JSON格式的响应
            translated_json = response.choices[0].message.content.strip()
            
            # 打印AI返回的翻译结果
            print(f"AI翻译结果:")
            print(f"原始响应: {translated_json}")
            
            # 检查行数是否匹配，如果不匹配则重试
            max_retries = 3
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    # 解析JSON响应
                    import json
                    result = json.loads(translated_json)
                    translated_items = result.get('translated_subtitles', [])
                    
                    print(f"解析后行数: {len(translated_items)} 行")
                    for i, item in enumerate(translated_items, 1):
                        if isinstance(item, dict) and 'original' in item and 'translated' in item:
                            print(f"  {i}. 原文: {item['original']}")
                            print(f"     译文: {item['translated']}")
                        else:
                            print(f"  {i}. {item}")
                    
                    # 检查行数是否匹配
                    if len(translated_items) == len(subtitles):
                        # 行数匹配，重新组合翻译后的字幕
                        translated_subtitles = []
                        for i, sub in enumerate(subtitles):
                            if isinstance(translated_items[i], dict) and 'translated' in translated_items[i]:
                                # 使用译文作为字幕文本
                                translated_text = translated_items[i]['translated']
                            elif isinstance(translated_items[i], dict) and 'original' in translated_items[i]:
                                # 如果只有原文，使用原始文本
                                translated_text = translated_items[i]['original']
                            else:
                                # 如果格式不正确，使用原始文本
                                translated_text = sub['text']
                            
                            translated_subtitles.append({
                                'start_time': sub['start_time'],
                                'end_time': sub['end_time'],
                                'text': translated_text
                            })
                        
                        # 打印最终翻译结果
                        print(f"最终翻译结果:")
                        for i, sub in enumerate(translated_subtitles, 1):
                            print(f"  {i}. {sub['text']}")
                        print(f"=== AI翻译完成 ===\n")
                        
                        return translated_subtitles
                    else:
                        # 行数不匹配，重试
                        retry_count += 1
                        if retry_count <= max_retries:
                            print(f"警告: 行数不匹配 (期望: {len(subtitles)}, 实际: {len(translated_items)})，第 {retry_count} 次重试...")
                            
                            # 重新调用API进行翻译
                            response = self.client.chat.completions.create(
                                model=self.settings.translation_model,
                                messages=[
                                    {
                            "role": "system",
                            "content": f"你是一个专业的字幕翻译助手。请将以下JSON格式的字幕准确翻译成{target_language}。\n\n**重要要求：**\n1. 必须返回JSON格式的响应\n2. 保持完全相同的行数结构\n3. 返回的JSON必须包含'translated_subtitles'字段，该字段是一个数组\n4. 数组中的每个元素必须是一个对象，包含'original'（原文）和'translated'（译文）两个字段\n5. 数组长度必须与输入的字幕数量完全一致\n6. 严格按照输入的顺序进行翻译\n7. 每个字幕块的原文必须与输入完全一致\n8. 译文必须准确翻译原文内容\n\n**返回格式示例：**\n{{\"translated_subtitles\": [\n  {{\"original\": \"Hello world\", \"translated\": \"你好世界\"}},\n  {{\"original\": \"How are you?\", \"translated\": \"你好吗？\"}},\n  {{\"original\": \"Good morning\", \"translated\": \"早上好\"}}\n]}}"
                        },
                                    {
                                        "role": "user",
                                        "content": str(json_input)
                                    }
                                ],
                                temperature=1,
                                max_tokens=4000,
                                response_format={"type": "json_object"}
                            )
                            
                            # 更新翻译结果用于下一次循环
                            translated_json = response.choices[0].message.content.strip()
                            print(f"重试后AI翻译结果:")
                            print(f"原始响应: {translated_json}")
                        else:
                            # 如果重试后仍然不匹配，抛出异常
                            raise Exception(f"翻译失败: 经过 {max_retries} 次重试后，行数仍然不匹配 (期望: {len(subtitles)}, 实际: {len(translated_items)})")
                
                except json.JSONDecodeError as e:
                    # JSON解析失败，重试
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"警告: JSON解析失败，第 {retry_count} 次重试...")
                        print(f"错误信息: {str(e)}")
                        
                        # 重新调用API进行翻译
                        response = self.client.chat.completions.create(
                            model=self.settings.translation_model,
                            messages=[
                                {
                        "role": "system",
                        "content": f"你是一个专业的字幕翻译助手。请将以下JSON格式的字幕准确翻译成{target_language}。\n\n**重要要求：**\n1. 必须返回JSON格式的响应\n2. 保持完全相同的行数结构\n3. 返回的JSON必须包含'translated_subtitles'字段，该字段是一个数组\n4. 数组中的每个元素必须是一个对象，包含'original'（原文）和'translated'（译文）两个字段\n5. 数组长度必须与输入的字幕数量完全一致\n6. 严格按照输入的顺序进行翻译\n7. 每个字幕块的原文必须与输入完全一致\n8. 译文必须准确翻译原文内容\n\n**返回格式示例：**\n{{\"translated_subtitles\": [\n  {{\"original\": \"Hello world\", \"translated\": \"你好世界\"}},\n  {{\"original\": \"How are you?\", \"translated\": \"你好吗？\"}},\n  {{\"original\": \"Good morning\", \"translated\": \"早上好\"}}\n]}}"
                    },
                                {
                                    "role": "user",
                                    "content": str(json_input)
                                }
                            ],
                            temperature=1,
                            max_tokens=4000,
                            response_format={"type": "json_object"}
                        )
                        
                        # 更新翻译结果用于下一次循环
                        translated_json = response.choices[0].message.content.strip()
                        print(f"重试后AI翻译结果:")
                        print(f"原始响应: {translated_json}")
                    else:
                        # 如果重试后仍然无法解析JSON，抛出异常
                        raise Exception(f"翻译失败: 经过 {max_retries} 次重试后，仍然无法解析JSON响应: {str(e)}")
            
        except Exception as e:
            # 如果翻译失败，抛出异常
            print(f"翻译失败: {str(e)}")
            print(f"=== 翻译失败，不保留原文 ===\n")
            raise e
    
    def _write_subtitle_file(self, output_file: Path, subtitles: List[Dict[str, Any]]):
        """写入字幕文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles, 1):
                f.write(f"{i}\n")
                f.write(f"{sub['start_time']} --> {sub['end_time']}\n")
                f.write(f"{sub['text']}\n\n")


def translate_subtitle(subtitle_file: str, target_language: str = None) -> str:
    """翻译字幕文件的便捷函数"""
    translator = SubtitleTranslator()
    return translator.translate_subtitle_file(subtitle_file, target_language)
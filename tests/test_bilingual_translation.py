#!/usr/bin/env python3
"""
测试中英对照字幕翻译功能
"""

import json
from ..subtitle_translator import SubtitleTranslator


def test_bilingual_translation():
    """测试中英对照翻译功能"""
    print("=== 测试中英对照翻译功能 ===")
    
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
        print(f"\n✅ 翻译成功! 输出字幕数量: {len(result)}")
        for i, sub in enumerate(result, 1):
            print(f"  {i}. {sub['text']}")
        return True
    except Exception as e:
        print(f"\n❌ 翻译失败: {e}")
        return False


def test_json_format_validation():
    """测试JSON格式验证"""
    print("\n=== 测试JSON格式验证 ===")
    
    # 测试有效的JSON格式
    valid_json = '''
    {
        "translated_subtitles": [
            {"original": "Hello", "translated": "你好"},
            {"original": "World", "translated": "世界"}
        ]
    }
    '''
    
    try:
        result = json.loads(valid_json)
        translated_items = result.get('translated_subtitles', [])
        print(f"✅ 有效JSON格式解析成功")
        print(f"解析后行数: {len(translated_items)}")
        for i, item in enumerate(translated_items, 1):
            print(f"  {i}. 原文: {item['original']}")
            print(f"     译文: {item['translated']}")
        return True
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
        return False


def test_invalid_json_format():
    """测试无效JSON格式"""
    print("\n=== 测试无效JSON格式 ===")
    
    # 测试无效的JSON格式
    invalid_json = "这不是有效的JSON"
    
    try:
        result = json.loads(invalid_json)
        print(f"❌ 无效JSON格式解析成功（不应该发生）")
        return False
    except json.JSONDecodeError as e:
        print(f"✅ 无效JSON格式正确抛出异常: {e}")
        return True
    except Exception as e:
        print(f"❌ 其他异常: {e}")
        return False


def test_missing_fields():
    """测试缺少必要字段的情况"""
    print("\n=== 测试缺少必要字段 ===")
    
    # 测试缺少translated字段的JSON
    json_with_missing_field = '''
    {
        "translated_subtitles": [
            {"original": "Hello"},
            {"original": "World"}
        ]
    }
    '''
    
    try:
        result = json.loads(json_with_missing_field)
        translated_items = result.get('translated_subtitles', [])
        print(f"✅ JSON解析成功（缺少translated字段）")
        print(f"解析后行数: {len(translated_items)}")
        for i, item in enumerate(translated_items, 1):
            if isinstance(item, dict) and 'original' in item:
                if 'translated' in item:
                    print(f"  {i}. 原文: {item['original']}, 译文: {item['translated']}")
                else:
                    print(f"  {i}. 原文: {item['original']}, 译文: 缺失")
            else:
                print(f"  {i}. {item}")
        return True
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
        return False


if __name__ == '__main__':
    # 运行所有测试
    tests = [
        test_bilingual_translation,
        test_json_format_validation,
        test_invalid_json_format,
        test_missing_fields
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试 {test.__name__} 执行失败: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    print("测试结果汇总:")
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i}. {test.__name__}: {status}")
    
    if all(results):
        print("\n🎉 所有测试通过! 中英对照翻译功能正常工作")
    else:
        print("\n⚠️ 部分测试失败，请检查代码")
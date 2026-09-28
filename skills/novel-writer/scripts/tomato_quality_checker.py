#!/usr/bin/env python3
"""
番茄小说质量检查器
检查标准：
- 省略号 < 30/章（理想<20）
- 平均段落 > 15字
- 对话占比 20-60%
- 字数 2600-3800（目标3200）
- 系统提示 2-3次（MINIMAL原则）
"""

import re
import sys
from typing import Dict, Any


def analyze_chapter(text: str) -> Dict[str, Any]:
    """分析章节质量指标"""
    
    # 计算中文字符 + 标点（番茄标准）
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    punctuation = len(re.findall(r'[，。！？、；：""''（）【】《》…]', text))
    total_words = chinese_chars + punctuation
    
    # 计算对话占比
    dialogue_pattern = r'["""]([^"""]+)["""]'
    dialogues = re.findall(dialogue_pattern, text)
    dialogue_chars = sum(len(re.findall(r'[\u4e00-\u9fff]', d)) for d in dialogues)
    dialogue_percentage = (dialogue_chars / chinese_chars * 100) if chinese_chars > 0 else 0
    
    # 计算省略号数量
    ellipsis_count = text.count('…') + text.count('...')
    
    # 计算段落平均长度
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    avg_paragraph_length = chinese_chars / len(paragraphs) if paragraphs else 0
    
    # 计算系统提示次数
    system_prompts = len(re.findall(r'【系统提示', text))
    
    return {
        "chinese_chars": chinese_chars,
        "punctuation": punctuation,
        "total_words": total_words,
        "dialogue_percentage": dialogue_percentage,
        "ellipsis_count": ellipsis_count,
        "paragraph_count": len(paragraphs),
        "avg_paragraph_length": avg_paragraph_length,
        "system_prompts": system_prompts,
    }


def check_quality(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """检查质量是否达标"""
    
    checks = []
    
    # 字数范围 2600-3800
    checks.append({
        "name": "字数范围(2600-3800)",
        "passed": 2600 <= metrics["total_words"] <= 3800,
        "value": f"{metrics['total_words']}字",
        "target": "2600-3800字"
    })
    
    # 对话占比 20-60%
    checks.append({
        "name": "对话占比(20-60%)",
        "passed": 20 <= metrics["dialogue_percentage"] <= 60,
        "value": f"{metrics['dialogue_percentage']:.1f}%",
        "target": "20-60%"
    })
    
    # 省略号 < 30
    checks.append({
        "name": "省略号<30",
        "passed": metrics["ellipsis_count"] < 30,
        "value": f"{metrics['ellipsis_count']}次",
        "target": "<30次"
    })
    
    # 平均段落 > 15字
    checks.append({
        "name": "平均段落>15字",
        "passed": metrics["avg_paragraph_length"] > 15,
        "value": f"{metrics['avg_paragraph_length']:.1f}字",
        "target": ">15字"
    })
    
    # 系统提示 2-3次
    checks.append({
        "name": "系统提示2-3次",
        "passed": 2 <= metrics["system_prompts"] <= 3,
        "value": f"{metrics['system_prompts']}次",
        "target": "2-3次"
    })
    
    passed = sum(1 for c in checks if c["passed"])
    
    return {
        "passed": passed == len(checks),
        "passed_count": passed,
        "total_count": len(checks),
        "checks": checks
    }


def print_report(metrics: Dict[str, Any], quality: Dict[str, Any]):
    """打印质量报告"""
    print("=" * 50)
    print("番茄小说质量检查报告")
    print("=" * 50)
    print(f"中文字符数: {metrics['chinese_chars']}")
    print(f"标点符号数: {metrics['punctuation']}")
    print(f"总字数（中文+标点）: {metrics['total_words']}")
    print(f"段落数: {metrics['paragraph_count']}")
    print(f"平均段落长度: {metrics['avg_paragraph_length']:.1f}字")
    print(f"对话占比: {metrics['dialogue_percentage']:.1f}%")
    print(f"省略号数量: {metrics['ellipsis_count']}次")
    print(f"系统提示次数: {metrics['system_prompts']}次")
    print("=" * 50)
    print("质量检查:")
    for check in quality["checks"]:
        status = "✓ 通过" if check["passed"] else "✗ 未通过"
        print(f"  {check['name']}: {status}")
        print(f"    实际值: {check['value']}, 目标: {check['target']}")
    print("=" * 50)
    print(f"总计: {quality['passed_count']}/{quality['total_count']} 项通过")
    if quality["passed"]:
        print("✓ 所有质量检查通过！")
    else:
        print("✗ 存在未通过项，需要修正")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python tomato_quality_checker.py <章节文件路径>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    
    metrics = analyze_chapter(text)
    quality = check_quality(metrics)
    print_report(metrics, quality)
    
    sys.exit(0 if quality["passed"] else 1)

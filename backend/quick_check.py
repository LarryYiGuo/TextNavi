#!/usr/bin/env python3
"""
快速检查缺失的锚点
"""

import json
import sys
from collections import defaultdict

def quick_check():
    """快速检查缺失的锚点"""
    print("🔍 快速检查缺失的锚点")
    print("=" * 50)
    
    # 读取结构文件
    try:
        with open("data/Sense_A_Finetuned.fixed.jsonl", "r") as f:
            first_line = f.readline().strip()
            struct = json.loads(first_line)
            struct_ids = {n["id"].strip() for n in struct["input"]["topology"]["nodes"]}
        print(f"📊 Structure文件中的节点: {sorted(struct_ids)}")
    except Exception as e:
        print(f"❌ 读取Structure文件失败: {e}")
        return
    
    # 读取Detail文件
    detail_ids = set()
    try:
        with open("data/Sense_A_MS.jsonl", "r") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    # 检查是否有input.anchor字段
                    if "input" in d and "anchor" in d["input"]:
                        anchor = d["input"]["anchor"].strip()
                        detail_ids.add(anchor)
                    # 兼容旧的node_hint字段
                    elif "node_hint" in d:
                        node_hint = d["node_hint"].strip()
                        detail_ids.add(node_hint)
                except json.JSONDecodeError:
                    print(f"⚠️ Line {line_num}: JSON decode error")
                    continue
        
        print(f"📊 Detail文件中的锚点: {sorted(detail_ids)}")
    except Exception as e:
        print(f"❌ 读取Detail文件失败: {e}")
        return
    
    # 检查缺失和多余的锚点
    missing = sorted(struct_ids - detail_ids)
    extra = sorted(detail_ids - struct_ids)
    
    print(f"\n🔍 锚点对齐检查:")
    print(f"   Structure节点数量: {len(struct_ids)}")
    print(f"   Detail锚点数量: {len(detail_ids)}")
    print(f"   缺失在Detail中: {missing}")
    print(f"   多余的Detail锚点: {extra}")
    
    if not missing and not extra:
        print("✅ 所有锚点完全对齐！")
    else:
        if missing:
            print(f"⚠️ 发现{len(missing)}个节点在Detail文件中缺失")
        if extra:
            print(f"⚠️ 发现{len(extra)}个多余的Detail锚点")

if __name__ == "__main__":
    quick_check()
    print("\n✅ 检查完成!")

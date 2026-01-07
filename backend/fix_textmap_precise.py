#!/usr/bin/env python3
"""
精确修复Sense_B_Finetuned.fixed.jsonl文件
"""

import json
import re
import os

def fix_textmap_precise():
    """精确修复textmap文件"""
    file_path = os.path.join(os.path.dirname(__file__), "data", "Sense_B_Finetuned.fixed.jsonl")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式找到重复的拓扑结构
    # 查找最后一个完整的拓扑结构结束位置
    pattern = r'}, "topology": \{"nodes": \[\]\}, "instruction_templates".*$'
    match = re.search(pattern, content)
    
    if match:
        # 找到匹配位置
        start_pos = match.start()
        # 截取到完整拓扑结构结束
        fixed_content = content[:start_pos] + '}'
        
        # 验证JSON格式
        try:
            fixed_data = json.loads(fixed_content)
            
            # 检查节点数量
            nodes_count = len(fixed_data.get("topology", {}).get("nodes", []))
            print(f"✅ 修复完成，节点数量: {nodes_count}")
            
            # 保存修复后的文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 文件已修复并保存: {file_path}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误: {e}")
            return False
    else:
        print("❌ 未找到重复的拓扑结构模式")
        return False

if __name__ == "__main__":
    print("🔧 开始精确修复textmap文件...")
    success = fix_textmap_precise()
    if success:
        print("🎉 修复完成！")
    else:
        print("❌ 修复失败！")

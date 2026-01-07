#!/usr/bin/env python3
"""
最终修复Sense_B_Finetuned.fixed.jsonl文件
"""

import json
import re
import os

def fix_textmap_final():
    """最终修复textmap文件"""
    file_path = os.path.join(os.path.dirname(__file__), "data", "Sense_B_Finetuned.fixed.jsonl")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找最后一个完整的拓扑结构结束位置
    # 查找最后一个完整的拓扑结构，在"regions"之后
    pattern = r'("regions": \[.*?\], "indoorGML": \{.*?\}, "retrieval": \{.*?\}, "navigation_policy": \{.*?\}, "uncertainty_policy": \{.*?\}, "accessibility": \{.*?\}, "schema_version": ".*?", "defaults": \{.*?\}, "evaluation_matrix": \{.*?\}\}, "output": ".*?")\s*,\s*"topology":\s*\{.*$'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # 找到匹配位置
        end_pos = match.end(1)
        # 截取到完整拓扑结构结束
        fixed_content = content[:end_pos] + '}'
        
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
        # 尝试简单的截取
        try:
            # 查找最后一个完整的JSON结构
            last_complete = content.rfind('}, "output": "')
            if last_complete > 0:
                # 找到output字段的结束位置
                output_end = content.find('"', last_complete + 15)
                if output_end > 0:
                    fixed_content = content[:output_end + 1] + '}'
                    
                    # 验证JSON格式
                    fixed_data = json.loads(fixed_content)
                    nodes_count = len(fixed_data.get("topology", {}).get("nodes", []))
                    print(f"✅ 简单修复完成，节点数量: {nodes_count}")
                    
                    # 保存修复后的文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ 文件已修复并保存: {file_path}")
                    return True
        except Exception as e:
            print(f"❌ 简单修复也失败: {e}")
            return False
        
        return False

if __name__ == "__main__":
    print("🔧 开始最终修复textmap文件...")
    success = fix_textmap_final()
    if success:
        print("🎉 修复完成！")
    else:
        print("❌ 修复失败！")

#!/usr/bin/env python3
"""
修复Sense_B_Finetuned.fixed.jsonl文件中的重复拓扑结构问题
"""

import json
import os

def fix_textmap_file():
    """修复textmap文件"""
    file_path = os.path.join(os.path.dirname(__file__), "data", "Sense_B_Finetuned.fixed.jsonl")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到重复的拓扑结构位置
    # 查找最后一个完整的拓扑结构结束位置
    last_complete_topology = content.rfind('"regions": [{"id": "gdi_studio", "name": "Studio"}, {"id": "gdi_workspace", "name": "Workspace (inside Sense B)"}]')
    
    if last_complete_topology > 0:
        # 找到完整拓扑结构的结束位置
        end_pos = content.find('}, "topology": {"nodes": []}', last_complete_topology)
        if end_pos > 0:
            # 截取到完整拓扑结构结束，然后添加output字段
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
            print("❌ 无法找到重复拓扑结构位置")
            return False
    else:
        print("❌ 无法找到完整拓扑结构")
        return False

if __name__ == "__main__":
    print("🔧 开始修复textmap文件...")
    success = fix_textmap_file()
    if success:
        print("🎉 修复完成！")
    else:
        print("❌ 修复失败！")

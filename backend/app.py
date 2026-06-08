import os, io, time, json, tempfile, subprocess, numpy as np, csv, uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# Local BLIP model imports
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

# Note: dropped unused top-level imports (`requests`, top-level `math`, duplicate `io`)
# during the 2026-06-04 cleanup. `math` is still re-imported locally inside
# `_enhanced_fusion`'s topo helpers where needed.

# ✅ New: DG Optimization Modules
# from user_needs_validator import UserNeedsValidator, UserNeed, DesignGoal
try:
    from accessibility_checker import AccessibilityChecker
except Exception as _e:
    AccessibilityChecker = None
    print(f"⚠️ AccessibilityChecker import failed: {_e}")
try:
    from indoor_gml_generator import IndoorGMLGenerator
except Exception as _e:
    IndoorGMLGenerator = None
    print(f"⚠️ IndoorGMLGenerator import failed: {_e}")
# from enhanced_metrics_collector import EnhancedMetricsCollector, MetricType, DataPriority, CollectionConfig

# Not wired yet — kept as None (not a no-op function) so /health/enhanced reports it
# honestly as "disabled" and the `if enhanced_metrics_collector:` guards short-circuit.
# The `.collect_real_time_data(...)` call sites are already wrapped in try/except.
enhanced_metrics_collector = None

# MetricType / DataPriority / UserNeed are normally exported from the matching DG
# modules. Provide None placeholders so static name lookup doesn't fail in the
# (currently dead) call sites; `if enhanced_metrics_collector:` / `if user_needs_validator:`
# guards prevent these from being touched at runtime when those modules are disabled.
try:
    from enhanced_metrics_collector import MetricType, DataPriority  # type: ignore
except Exception:
    MetricType = None
    DataPriority = None
try:
    from user_needs_validator import UserNeed  # type: ignore
except Exception:
    UserNeed = None

def get_location_description(node_id, detail_items=None):
    """获取位置描述，避免参数错误"""
    try:
        # 避免 takes from 1 to 2 positional arguments 错误
        base = f"Current location: {node_id.replace('_',' ')}."
        if detail_items:
            captions = []
            for item in detail_items[:2]:  # 最多取前2个
                caption = item.get("caption", "") or item.get("nl_text", "")
                if caption:
                    captions.append(caption)
            if captions:
                return base + " " + " ".join(captions)
        return base
    except Exception as e:
        return f"Current location: {node_id}."

def get_next_action(node_id=None, site_id=None, lang="en", *args, **kwargs):
    """Next-action prompt. Previously a fixed yellow-line phrase emitted for every
    photo regardless of node/scene — replaced with an empty string so the response
    field stays for FE compatibility but no longer broadcasts a misleading instruction.
    The real per-node turn+step direction is already in `navigation_instruction`.
    """
    return {"say": ""}

# 添加到全局命名空间
globals()['get_location_description'] = get_location_description
globals()['get_next_action'] = get_next_action
try:
    from dg_evaluation_enhancement import DGEvaluationManager
except Exception as _e:
    DGEvaluationManager = None
    print(f"⚠️ DGEvaluationManager import failed: {_e}")

# Note: If you encounter Hugging Face authentication issues, you can:
# 1. Set HF_TOKEN environment variable in your .env file
# 2. Run: huggingface-cli login
# 3. Or use a different model that doesn't require authentication

# ---------- Config ----------
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
# HF_TOKEN  = os.getenv("HF_TOKEN", "")  # No longer needed for local BLIP
# HF_MODEL  = os.getenv("HF_MODEL", "Salesforce/blip-image-captioning-large")  # No longer needed
LLM_KEY   = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMP  = float(os.getenv("LLM_TEMPERATURE", "0"))
STEP_LEN  = float(os.getenv("STEP_LEN_M", "0.7"))

# Local BLIP model configuration
BLIP_MODEL_PATH = os.getenv("BLIP_MODEL_PATH", "Salesforce/blip-image-captioning-large")
BLIP_DEVICE = os.getenv("BLIP_DEVICE", "cpu")

DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

# ✅ New: DG Optimization Configuration
METRICS_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "metrics_data")
ENABLE_DG_EVALUATION = os.getenv("ENABLE_DG_EVALUATION", "true").lower() == "true"
ENABLE_ACCESSIBILITY_CHECKING = os.getenv("ENABLE_ACCESSIBILITY_CHECKING", "true").lower() == "true"
ENABLE_INDOOR_GML = os.getenv("ENABLE_INDOOR_GML", "true").lower() == "true"

# ✅ New: Preset output mapping based on provider + site_id
PRESET_OUTPUTS = {
    "ft_SCENE_A_MS": "Sense_A_Finetuned.fixed.jsonl",
    "ft_SCENE_B_STUDIO": "Sense_B_Finetuned.fixed.jsonl", 
    "base_SCENE_A_MS": "Sence_A_4o.fixed.jsonl",
    "base_SCENE_B_STUDIO": "Sense_B_4o.fixed.jsonl"
}

def get_preset_output(provider: str, site_id: str) -> str:
    """Get preset output based on provider and site_id combination"""
    key = f"{provider.lower()}_{site_id}"
    filename = PRESET_OUTPUTS.get(key)
    print(f"🔍 Looking for preset output: key={key}, filename={filename}")
    
    if not filename:
        print(f"⚠️ No filename found for key: {key}")
        return "Welcome! Please take a photo to start exploring."
    
    filepath = os.path.join(DATA_DIR, filename)
    print(f"📁 Full filepath: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first line (JSONL format)
            first_line = f.readline().strip()
            print(f"📖 First line: {first_line[:100]}...")
            
            if first_line:
                data = json.loads(first_line)
                output = data.get("output", "Welcome! Please take a photo to start exploring.")
                print(f"✅ Found output: {output[:100]}...")
                return output
            else:
                print("⚠️ Empty first line")
                return "Welcome! Please take a photo to start exploring."
    except Exception as e:
        print(f"⚠️ Failed to load preset output from {filename}: {e}")
        return "Welcome! Please take a photo to start exploring."

def get_matching_data(provider: str, site_id: str) -> dict:
    """Get matching data for BLIP text matching based on provider and site_id"""
    key = f"{provider.lower()}_{site_id}"
    filename = PRESET_OUTPUTS.get(key)
    if not filename:
        return {}
    
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first line (JSONL format)
            first_line = f.readline().strip()
            if first_line:
                data = json.loads(first_line)
                return data
            else:
                return {}
    except Exception as e:
        print(f"⚠️ Failed to load matching data from {filename}: {e}")
        return {}

def get_detailed_matching_data(site_id: str) -> list:
    """Get detailed matching data from Detail files for layered fusion conversation enhancement"""
    # Map site_id to corresponding Detail file
    detail_file_mapping = {
        "SCENE_A_MS": "Sense_A_MS.jsonl",
        "SCENE_B_STUDIO": "Sense_B_Studio.jsonl"
    }
    
    filename = detail_file_mapping.get(site_id)
    if not filename:
        print(f"⚠️ No Detail file mapping found for site_id: {site_id}")
        return []
    
    filepath = os.path.join(DATA_DIR, filename)
    try:
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        print(f"✅ Loaded {len(data)} detailed descriptions from {filepath} for {site_id}")
        return data
    except Exception as e:
        print(f"⚠️ Failed to load detailed descriptions from {filename}: {e}")
        return []


def track_orientation(session_id: str, caption: str, predicted_location: str) -> dict:
    """Track user orientation changes"""
    caption_lower = caption.lower()
    
    # Extract orientation information from description
    orientation = "unknown"
    if "left" in caption_lower:
        orientation = "left"
    elif "right" in caption_lower:
        orientation = "right"
    elif "ahead" in caption_lower or "front" in caption_lower:
        orientation = "ahead"
    elif "behind" in caption_lower or "back" in caption_lower:
        orientation = "behind"
    
    # Get session state
    session = SESSIONS.get(session_id, {})
    orientation_history = session.get("orientation_history", [])
    
    # Check orientation consistency
    orientation_consistent = True
    if orientation_history and orientation != "unknown":
        last_orientation = orientation_history[-1].get("orientation", "unknown")
        if last_orientation != "unknown" and last_orientation != orientation:
            # Orientation has changed, check if it's reasonable
            orientation_consistent = False
    
    return {
        "orientation": orientation,
        "consistent": orientation_consistent,
        "confidence": 0.8 if orientation != "unknown" else 0.5
    }

def update_session_location(session_id: str, new_location: str, confidence: float, orientation_info: dict):
    """Update location information in session"""
    if session_id not in SESSIONS:
        return
    
    session = SESSIONS[session_id]

    # Update current location
    session["current_location"] = new_location
    session["last_update_time"] = datetime.utcnow().isoformat()

    # Add to history records (continuity_* fields removed — validate_location_continuity
    # used a generic-name adjacency table that never matched real node IDs; its output
    # was recorded but never read. The real continuity boost lives in the retriever pipeline.)
    location_record = {
        "location": new_location,
        "confidence": confidence,
        "timestamp": datetime.utcnow().isoformat(),
    }

    session["location_history"].append(location_record)
    session["orientation_history"].append(orientation_info)
    session["confidence_history"].append(confidence)

    # Keep history records within reasonable range
    if len(session["location_history"]) > 10:
        session["location_history"] = session["location_history"][-10:]
        session["orientation_history"] = session["orientation_history"][-10:]
        session["confidence_history"] = session["confidence_history"][-10:]

    print(f"📍 Session {session_id} location updated: {new_location} (confidence: {confidence:.3f})")


def generate_location_context_prompt(session_id: str, user_question: str, site_id: str, lang: str = "en") -> str:
    """Generate context prompt with location secondary judgment"""
    if session_id not in SESSIONS:
        return ""
    
    session = SESSIONS[session_id]
    current_location = session.get("current_location")
    orientation_history = session.get("orientation_history", [])
    location_history = session.get("location_history", [])
    
    # 获取当前朝向
    current_orientation = "unknown"
    if orientation_history:
        current_orientation = orientation_history[-1].get("orientation", "unknown")
    
    # Analyze location stability
    location_stability = "stable"
    if len(location_history) >= 2:
        recent_locations = [h["location"] for h in location_history[-3:]]
        if len(set(recent_locations)) == 1:
            location_stability = "very stable"
        elif len(set(recent_locations)) <= 2:
            location_stability = "stable"
        else:
            location_stability = "changing"
    
    # 检测用户询问的目的地类型（抽象化）
    destination_types = {
        "SCENE_A_MS": {
            "exit": ["出口", "exit", "出去", "离开", "门", "door"],
            "central_area": ["中间", "中央", "中心", "central", "middle", "center"],
            "work_area": ["工作", "工作台", "工作区", "work", "workbench", "workspace"],
            "storage": ["存储", "储物", "架子", "storage", "shelf", "cabinet"],
            "seating": ["坐", "椅子", "休息", "seating", "chair", "rest"]
        },
        "SCENE_B_STUDIO": {
            "exit": ["出口", "exit", "出去", "离开", "门", "door"],
            "window_area": ["窗户", "窗", "window", "光线", "light"],
            "seating": ["坐", "沙发", "椅子", "休息", "seating", "sofa", "chair"],
            "work_surface": ["桌子", "工作台", "桌面", "desk", "table", "surface"]
        }
    }
    
    # 分析用户问题中的目的地类型
    detected_destinations = []
    question_lower = user_question.lower()
    site_destinations = destination_types.get(site_id, {})
    
    for dest_type, keywords in site_destinations.items():
        if any(keyword in question_lower for keyword in keywords):
            detected_destinations.append(dest_type)
    
    # 生成抽象但有用的位置上下文
    if lang == "zh":
        location_context = f"""当前位置分析：
- 预测位置：{current_location or '未知'}
- 用户朝向：{current_orientation or '未知'}
- 位置稳定性：{location_stability}
- 位置历史：{len(location_history)} 次记录

"""
        
        if detected_destinations and current_location:
            # 使用抽象的目的地类型而不是具体地点
            dest_type = detected_destinations[0]
            location_context += f"""导航目标分析：
- 目标类型：{dest_type}
- 当前位置：{current_location}
- 建议：基于当前位置和朝向，提供到达目标类型的导航指导

"""
        
        location_context += f"""用户问题：{user_question}

请基于以上位置信息，为用户提供：
1. 基于当前位置的抽象导航指导
2. 考虑用户当前朝向的转向建议
3. 如果位置信息不明确，建议重新拍照确认
4. 提供通用的移动指导，而不是具体地点名称"""
        
    else:
        location_context = f"""Current Location Analysis:
- Predicted Location: {current_location or 'Unknown'}
- User Orientation: {current_orientation or 'Unknown'}
- Location Stability: {location_stability}
- Location History: {len(location_history)} records

"""
        
        if detected_destinations and current_location:
            dest_type = detected_destinations[0]
            location_context += f"""Navigation Target Analysis:
- Target Type: {dest_type}
- Current Location: {current_location}
- Suggestion: Provide navigation guidance based on current location and orientation

"""
        
        location_context += f"""User Question: {user_question}

Please provide:
1. Abstract navigation guidance based on current location
2. Turn-by-turn guidance considering user's current orientation
3. Suggestion to retake photo if location is unclear
4. General movement guidance rather than specific location names"""
    
    return location_context

def normalize_candidate(c):
    """统一候选返回格式为 (node_id, fused_score, has_detail)"""
    if isinstance(c, (list, tuple)):
        if len(c) == 3: 
            return c[0], float(c[1]), bool(c[2])
        if len(c) == 2: 
            return c[0], float(c[1]), False
    # 兜底：非法输入
    return str(c), 0.0, False

def enhanced_ft_retrieval(caption: str, retriever, site_id: str, detailed_data: list,
                          session_id: Optional[str] = None) -> list:
    """增强：改进的FT检索，使用增强的双通道融合策略。
    session_id 透传到 retriever.retrieve()，让 DG2 区分度打点能落到正确会话。"""
    print(f"🏗️ Enhanced Dual-Channel Fusion retrieval for {site_id}")

    try:
        # 使用增强的双通道检索器
        try:
            # 获取融合后的候选列表
            candidates = retriever.retrieve(caption, top_k=10, scene_filter=site_id, session_id=session_id)
            
            if not candidates:
                print("❌ 无法获取候选列表")
                return []
                
            print(f"✅ 成功获取候选列表: {len(candidates)} 个候选")
            
            # 🔧 NEW: 标准化候选格式，确保三元组一致性
            if candidates and isinstance(candidates[0], (list, tuple)):
                print(f"🔧 标准化候选格式: 从{len(candidates[0])}元组到三元组")
                normalized_candidates = []
                for c in candidates:
                    node_id, score, has_detail = normalize_candidate(c)
                    # 转换为字典格式以保持兼容性
                    normalized_candidates.append({
                        "id": node_id,
                        "score": score,
                        "has_detail": has_detail
                    })
                candidates = normalized_candidates
                print(f"🔧 标准化完成: {len(candidates)} 个候选")
                
        except Exception as e:
            print(f"❌ 增强双通道检索失败: {e}")
            return []
        
        print(f"📊 Enhanced dual-channel fusion returned {len(candidates)} candidates")
        
        # 修复：正确查找detail数据，确保has_detail与detail_entries一致
        for candidate in candidates:
            node_id = candidate["id"]
            
            # 🔧 NEW: 应用实体别名映射，将结构数据ID转换为细节数据ID
            mapped_detail_id = node_id  # 默认使用原ID
            entity_aliases = {
                "poi01_entrance_glass_door": "dp_ms_entrance",
                "poi02_green_trash_bin": "yline_start",
                "poi03_black_drawer_cabinet": "yline_bend_mid",
                "poi04_wall_3d_printers": "atrium_edge",
                "poi05_desk_3d_printer": "tv_zone",
                "poi06_small_open_3d_printer": "storage_corner",
                "poi07_cardboard_boxes": "orange_sofa_corner",
                "poi08_to_atrium": "desks_cluster",
                "poi09_qr_bookshelf": "chair_on_yline",
                "poi10_metal_display_cabinet": "small_table_mid"
            }
            
            if node_id in entity_aliases:
                mapped_detail_id = entity_aliases[node_id]
                print(f"🔍 实体别名映射: {node_id} → {mapped_detail_id}")
            
            # 使用retriever中的detail_index（优先使用映射后的ID）
            if hasattr(retriever, 'detail_index') and retriever.detail_index:
                detail_items = retriever.detail_index.get(mapped_detail_id, [])
                print(f"🔧 使用retriever.detail_index查找 {mapped_detail_id}: {len(detail_items)} 项")
            else:
                # 回退到原始方法（使用映射后的ID）
                detail_items = find_node_details_by_hint(mapped_detail_id, detailed_data)
                print(f"🔧 使用find_node_details_by_hint查找 {mapped_detail_id}: {len(detail_items)} 项")
            
            candidate["detail_metadata"] = detail_items
            candidate["detail_items"] = len(detail_items)
            
            # 修复：确保has_detail与detail_entries统计一致
            has_detail = len(detail_items) > 0
            candidate["has_detail"] = has_detail  # 绑定到候选节点上
            
            print(f"🔍 Found {len(detail_items)} detail entries for node {node_id}")
            
            if has_detail:
                print(f"🔍 Node {node_id}: structure={candidate.get('structure_score', 0):.3f}, detail_available")
            else:
                print(f"🔍 Node {node_id}: structure={candidate.get('structure_score', 0):.3f}, no_detail_available")
        
        print(f"📊 Enhanced Dual-Channel Fusion completed: {len(candidates)} candidates (fused scoring)")
        return candidates
        
    except Exception as e:
        print(f"❌ Enhanced FT retrieval failed: {e}")
        return []


def find_node_details_by_hint(node_id: str, detailed_data: list) -> list:
    """Find detail descriptions from Sense_A_MS.jsonl using node_hint field with alias resolution"""
    print(f"🔍 find_node_details_by_hint调用: node_id={node_id}, detailed_data长度={len(detailed_data) if detailed_data else 0}")
    
    if not detailed_data:
        print(f"⚠️ detailed_data为空！")
        return []
    
    # 🔧 NEW: 统一的别名解析器
    POI_TO_CANON = {
        "poi01_entrance_glass_door": "dp_ms_entrance",
        "poi02_green_trash_bin": "yline_start",
        "poi03_black_drawer_cabinet": "yline_bend_mid",
        "poi04_wall_3d_printers": "atrium_edge",
        "poi05_desk_3d_printer": "tv_zone",
        "poi06_small_open_3d_printer": "storage_corner",
        "poi07_cardboard_boxes": "orange_sofa_corner",
        "poi08_to_atrium": "desks_cluster",
        "poi09_qr_bookshelf": "chair_on_yline",
        "poi10_metal_display_cabinet": "small_table_mid",
    }
    
    def resolve_alias(node_id: str) -> str:
        """解析节点ID别名"""
        return POI_TO_CANON.get(node_id, node_id)
    
    # 应用别名解析
    anchor = resolve_alias(node_id)
    if anchor != node_id:
        print(f"🔍 别名解析: {node_id} → {anchor}")
    
    node_details = []
    for item in detailed_data:
        # Use node_hint field to match with structure nodes (使用解析后的别名)
        if item.get("node_hint") == anchor:
            node_details.append(item)
    
    # 🔧 NEW: 关键词兜底（避免0命中）
    if not node_details:
        k = anchor.lower()
        if "entrance" in k or "door" in k: 
            fallback_items = [item for item in detailed_data if item.get("node_hint") == "dp_ms_entrance"]
            if fallback_items:
                print(f"🔍 关键词兜底: {anchor} → dp_ms_entrance (找到 {len(fallback_items)} 项)")
                node_details = fallback_items
        elif "atrium" in k:
            fallback_items = [item for item in detailed_data if item.get("node_hint") == "atrium_edge"]
            if fallback_items:
                print(f"🔍 关键词兜底: {anchor} → atrium_edge (找到 {len(fallback_items)} 项)")
                node_details = fallback_items
        elif "printer" in k:
            fallback_items = [item for item in detailed_data if item.get("node_hint") in ["tv_zone", "desks_cluster"]]
            if fallback_items:
                print(f"🔍 关键词兜底: {anchor} → tv_zone/desks_cluster (找到 {len(fallback_items)} 项)")
                node_details = fallback_items
        elif "box" in k:
            fallback_items = [item for item in detailed_data if item.get("node_hint") in ["storage_corner", "orange_sofa_corner"]]
            if fallback_items:
                print(f"🔍 关键词兜底: {anchor} → storage_corner/orange_sofa_corner (找到 {len(fallback_items)} 项)")
                node_details = fallback_items
        elif "bookshelf" in k or "qr" in k:
            fallback_items = [item for item in detailed_data if item.get("node_hint") == "chair_on_yline"]
            if fallback_items:
                print(f"🔍 关键词兜底: {anchor} → chair_on_yline (找到 {len(fallback_items)} 项)")
                node_details = fallback_items
        elif "trash" in k or "bin" in k:
            fallback_items = [item for item in detailed_data if item.get("node_hint") == "small_table_mid"]
            if fallback_items:
                print(f"🔍 关键词兜底: {anchor} → small_table_mid (找到 {len(fallback_items)} 项)")
                node_details = fallback_items
    
    print(f"🔍 Found {len(node_details)} detail entries for node {node_id} (解析后: {anchor})")
    return node_details

def find_node_details(node_id: str, detailed_data: list) -> list:
    """Find detail descriptions associated with a specific node (legacy function)"""
    if not detailed_data:
        return []
    
    node_details = []
    for item in detailed_data:
        if item.get("id") == node_id:
            node_details.append(item)
    
    return node_details

def calculate_enhanced_detail_score(caption: str, node_details: list, structure_score: float) -> float:
    """Calculate enhanced detail score with proper weighting and structure score consideration"""
    if not node_details:
        return 0.0
    
    caption_lower = caption.lower()
    best_detail_score = 0.0
    
    for detail in node_details:
        detail_score = 0.0
        
        # 1. Natural language text enhancement (primary)
        nl_text = detail.get("nl_text", "").lower()
        if nl_text:
            # Enhanced semantic similarity calculation
            try:
                if EMB and nl_text and caption:
                    embeddings = EMB.encode([nl_text, caption])
                    similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
                    
                    # Scale similarity based on structure score quality
                    if structure_score > 0.7:
                        semantic_score = max(0, similarity) * 0.25  # High structure score = conservative detail boost
                    elif structure_score > 0.5:
                        semantic_score = max(0, similarity) * 0.35  # Medium structure score = moderate detail boost
                    else:
                        semantic_score = max(0, similarity) * 0.45  # Low structure score = aggressive detail boost
                    
                    detail_score += semantic_score
                    print(f"  📊 Semantic similarity: {similarity:.3f} -> {semantic_score:.3f}")
            except Exception as e:
                print(f"⚠️ Semantic similarity calculation failed: {e}")
        
        # 2. Structured text enhancement (secondary)
        struct_text = detail.get("struct_text", "").lower()
        if struct_text:
            struct_score_detail = parse_structured_text(caption_lower, struct_text)
            detail_score += struct_score_detail * 0.2  # Reduced weight for structured text
        
        # 3. Spatial relations enhancement (tertiary)
        spatial_relations = detail.get("spatial_relations", {})
        if spatial_relations:
            spatial_score = calculate_spatial_enhancement(caption_lower, spatial_relations)
            detail_score += spatial_score * 0.15  # Spatial relations bonus
        
        # 4. Unique features enhancement (quaternary)
        unique_features = detail.get("unique_features", [])
        if unique_features:
            feature_score = calculate_feature_enhancement(caption_lower, unique_features)
            detail_score += feature_score * 0.1  # Unique features bonus
        
        best_detail_score = max(best_detail_score, detail_score)
    
    # Normalize detail score based on structure score quality
    if structure_score > 0.8:
        normalized_score = best_detail_score * 0.8  # High confidence = conservative detail
    elif structure_score > 0.6:
        normalized_score = best_detail_score * 0.9  # Medium confidence = moderate detail
    else:
        normalized_score = best_detail_score * 1.0  # Low confidence = full detail potential
    
    print(f"  🔍 Detail score: raw={best_detail_score:.3f}, normalized={normalized_score:.3f}")
    return min(normalized_score, 0.4)  # Cap detail contribution at 0.4

def calculate_spatial_enhancement(caption: str, spatial_relations: dict) -> float:
    """Calculate spatial relations enhancement score"""
    if not spatial_relations:
        return 0.0
    
    spatial_score = 0.0
    caption_lower = caption.lower()
    
    # Check for spatial relation matches
    for direction, landmarks in spatial_relations.items():
        if isinstance(landmarks, list):
            for landmark in landmarks:
                if landmark.lower() in caption_lower:
                    spatial_score += 0.05  # Small bonus for each spatial match
        elif isinstance(landmarks, str) and landmarks.lower() in caption_lower:
            spatial_score += 0.05
    
    return min(spatial_score, 0.2)  # Cap spatial bonus at 0.2

def calculate_feature_enhancement(caption: str, unique_features: list) -> float:
    """Calculate unique features enhancement score"""
    if not unique_features:
        return 0.0
    
    feature_score = 0.0
    caption_lower = caption.lower()
    
    # Check for unique feature matches
    for feature in unique_features:
        if feature and feature.lower() in caption_lower:
            feature_score += 0.08  # Bonus for each unique feature match
    
    return min(feature_score, 0.3)  # Cap feature bonus at 0.3


def extract_keywords(text: str) -> list:
    """Extract meaningful keywords from text"""
    # Remove common words and extract key terms
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"}
    
    words = text.lower().split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords

def parse_structured_text(caption: str, struct_text: str) -> float:
    """Parse structured text and calculate match score"""
    score = 0.0
    
    # Parse structured text format: key=value; key=value
    try:
        parts = struct_text.split(";")
        for part in parts:
            if "=" in part:
                key, value = part.strip().split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Check if caption contains this value
                if value in caption:
                    score += 0.2  # Increased from 0.1 to 0.2
                    
                    # Enhanced bonus for important features
                    if key in ["objects", "location", "furniture"]:
                        score += 0.15  # Increased from 0.05 to 0.15
                    elif key in ["colors", "materials"]:
                        score += 0.1   # Increased from 0.03 to 0.1
                    
                    # Additional bonus for exact phrase matches
                    if len(value.split()) > 1 and value in caption:
                        score += 0.1  # Bonus for multi-word matches
    except:
        pass
    
    return score


# Session-level logging switch: key = (session_id, provider) -> {"enabled":bool, "run_id":str}
LOG_SWITCH = defaultdict(lambda: {"enabled": False, "run_id": ""})

# Enhanced session management with location tracking
SESSIONS: Dict[str, Dict[str, Any]] = {}

# ✅ DG Optimization Module Instances
if ENABLE_DG_EVALUATION and DGEvaluationManager is not None:
    try:
        dg_evaluator = DGEvaluationManager()
        print("✅ DG Evaluation Manager initialized")
    except Exception as _e:
        dg_evaluator = None
        print(f"⚠️ DG Evaluation Manager init failed: {_e}")
else:
    dg_evaluator = None
    print("⚠️ DG Evaluation Manager disabled")

if ENABLE_ACCESSIBILITY_CHECKING and AccessibilityChecker is not None:
    try:
        accessibility_checker = AccessibilityChecker()
        print("✅ Accessibility Checker initialized")
    except Exception as _e:
        accessibility_checker = None
        print(f"⚠️ Accessibility Checker init failed: {_e}")
else:
    accessibility_checker = None
    print("⚠️ Accessibility Checker disabled")

if ENABLE_INDOOR_GML and IndoorGMLGenerator is not None:
    try:
        indoor_gml_generator = IndoorGMLGenerator()
        print("✅ IndoorGML Generator initialized")
    except Exception as _e:
        indoor_gml_generator = None
        print(f"⚠️ IndoorGML Generator init failed: {_e}")
else:
    indoor_gml_generator = None
    print("⚠️ IndoorGML Generator disabled")

# Not wired yet — kept as None so /health/enhanced and `if user_needs_validator:` guards don't NameError
user_needs_validator = None

# # Initialize enhanced metrics collector
# metrics_collector_config = CollectionConfig(
#     storage_path=METRICS_STORAGE_PATH,
#     auto_save_interval=60,
#     max_buffer_size=1000,
#     enable_real_time_processing=True,
#     enable_database_storage=True,
#     enable_file_storage=True
# )
# enhanced_metrics_collector = EnhancedMetricsCollector(metrics_collector_config)
# print("✅ Enhanced Metrics Collector initialized")

# # Initialize user needs validator
# user_needs_validator = UserNeedsValidator()
# print("✅ User Needs Validator initialized")

# Logging configuration
BASE_LOG_DIR = os.getenv("LOG_DIR", "logs")

    # Create subdirectories by provider: logs/ft/* and logs/base/*
def _log_paths(provider: str):
    sub = "ft" if str(provider).lower() == "ft" else "base"
    d = os.path.join(BASE_LOG_DIR, sub)
    os.makedirs(d, exist_ok=True)
    return {
        "locate":    os.path.join(d, "locate_log.csv"),
        "clar":      os.path.join(d, "clarification_log.csv"),
        "recovery":  os.path.join(d, "recovery_log.csv"),
        "latency":   os.path.join(d, "latency_log.csv"),
    }

HEADERS = {
    # ✅ First column: site_id; Second column: run_id; Third column: phase
    "locate":   ["site_id","run_id","ts_iso","req_id","session_id","provider",
                 "phase",  # 👈 新增：warmup|trial
                 "caption",
                 "top1_id","top1_score",
                 "top2_id","top2_score",
                 "margin",
                 "gt_node_id",
                 "hit_top1","hit_top2","hit_hop1",
                 "low_conf","low_conf_rule",
                 "client_start_ms","server_recv_ms","server_resp_ms"],
    "clar":     ["site_id","run_id","ts_iso","clar_id","session_id","provider",
                 "phase",  # 👈 新增：warmup|trial
                 "req_id","round_idx","event",  # event: trigger/step/success/fail
                 "user_text","system_text",
                 "resolved_node_id","gt_node_id","success"],
    "recovery": ["site_id","run_id","ts_iso","session_id","provider",
                 "phase",  # 👈 新增：warmup|trial
                 "req_id","recovery_ms","from_node","to_node"],
    "latency":  ["site_id","run_id","ts_iso","req_id","session_id","provider",
                 "phase",  # 👈 新增：warmup|trial
                 "client_start_ms","client_tts_start_ms","e2e_latency_ms"]
}

def _ensure_headers(paths: dict):
    for kind, p in paths.items():
        if not os.path.exists(p):
            with open(p, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(HEADERS[kind])

def _is_logging(session_id: str, provider: str):
    st = LOG_SWITCH[(session_id, (provider or "base").lower())]
    return bool(st.get("enabled")), st.get("run_id") or ""

def _now_ms(): 
    """Get current time in milliseconds"""
    return int(time.time() * 1000)

# 🔧 FIX: 调整低置信度阈值，让60%+的confidence不再显示警告
# 低置信度阈值配置 - 双通道模式，优化阈值
LOWCONF_SCORE_TH = float(os.getenv("LOWCONF_SCORE_TH", "0.50"))  # 🔧 FIX P1-5: 跟论文 §3.4 对齐（confidence < 0.50 → 请求新照片）
LOWCONF_MARGIN_TH = float(os.getenv("LOWCONF_MARGIN_TH", "0.10"))  # 🔧 FIX P1-5: 跟论文 §3.4 对齐（margin < 0.10 → 请求新照片）

ENABLE_CONTINUITY_BOOST = os.getenv("ENABLE_CONTINUITY_BOOST", "true").lower() == "true"

# 🆕 SigLIP retriever (Plan B): replaces BLIP-caption + dual-channel fusion with
# a single SigLIP-so400m image→text-template matching call. On the labeled
# 37-photo benchmark this reaches useful-top1 = 73.0% (paper Table 4 metric),
# matching the paper's fine-tuned baseline. Falls back to legacy when off.
ENABLE_SIGLIP = os.getenv("ENABLE_SIGLIP", "true").lower() == "true"
siglip_retriever = None
if ENABLE_SIGLIP:
    try:
        from siglip_retriever import get_retriever as _get_siglip
        siglip_retriever = _get_siglip()
    except Exception as _e:
        print(f"⚠️ SigLIP retriever init failed: {_e}")
        siglip_retriever = None

# 🆕 Topology prior: boost SigLIP candidates that are topology-neighbours of the
# user's previous location (sequential-movement assumption). Loaded lazily; if
# topology_eval import fails, prior is skipped silently.
TOPOLOGY_PRIOR_SAME_BOOST     = float(os.getenv("TOPOLOGY_PRIOR_SAME_BOOST",     "0.05"))  # cosine units
TOPOLOGY_PRIOR_NEIGHBOR_BOOST = float(os.getenv("TOPOLOGY_PRIOR_NEIGHBOR_BOOST", "0.025"))
try:
    from topology_eval import STRUCT_TO_TOPOLOGY as _STRUCT_TO_TOPO, _ADJ as _TOPO_ADJ
    print(f"🔧 Topology prior enabled: same_boost={TOPOLOGY_PRIOR_SAME_BOOST}, neighbor_boost={TOPOLOGY_PRIOR_NEIGHBOR_BOOST}")
except Exception as _e:
    print(f"⚠️ Topology prior disabled ({_e})")
    _STRUCT_TO_TOPO, _TOPO_ADJ = {}, {}

# 🔧 Fusion hyperparameters — env-tunable so an outer driver can sweep them.
# All defaults are the existing hardcoded values; changing nothing keeps current
# behavior. See backend/tools/sweep_fusion.py for the search driver.
FUSION_GAMMA        = float(os.getenv("FUSION_GAMMA",        "0.15"))   # continuity-boost coef
FUSION_NEG_PENALTY  = float(os.getenv("FUSION_NEG_PENALTY",  "0.15"))   # apply_negatives() per-hit penalty
FUSION_STRUCT_TAU   = float(os.getenv("FUSION_STRUCT_TAU",   "0.15"))   # structure channel softmax temperature
FUSION_DETAIL_TAU   = float(os.getenv("FUSION_DETAIL_TAU",   "0.20"))   # detail channel softmax temperature
FUSION_CONFLICT_GAP = float(os.getenv("FUSION_CONFLICT_GAP", "0.50"))   # |struct_logit - detail_logit| trigger for conflict gating
FUSION_ALPHA_FB     = float(os.getenv("FUSION_ALPHA_FB",     "0.65"))   # α fallback when both channel clarities are zero
FUSION_BETA_FB      = float(os.getenv("FUSION_BETA_FB",      "0.35"))   # β fallback (paired with FUSION_ALPHA_FB)
# Force-override (-1 = use adaptive). Useful for diagnostics: α=1/β=0 = struct-only,
# α=0/β=1 = detail-only. Set both to non-negative values to bypass _adaptive_weights.
FUSION_ALPHA_FORCE  = float(os.getenv("FUSION_ALPHA_FORCE",  "-1"))
FUSION_BETA_FORCE   = float(os.getenv("FUSION_BETA_FORCE",   "-1"))

print(f"🔧 Low-confidence thresholds: score<{LOWCONF_SCORE_TH}, margin<{LOWCONF_MARGIN_TH}")
print(f"🔧 Continuity boost: enabled={ENABLE_CONTINUITY_BOOST}")
print(f"🔧 Fusion hyperparams: γ={FUSION_GAMMA}, neg_penalty={FUSION_NEG_PENALTY}, "
      f"τ_struct={FUSION_STRUCT_TAU}, τ_detail={FUSION_DETAIL_TAU}, "
      f"conflict_gap={FUSION_CONFLICT_GAP}, αβ_fb=({FUSION_ALPHA_FB}, {FUSION_BETA_FB})")
# Note: an `apply_softmax_calibration` helper and SOFTMAX_TEMPERATURE / ENABLE_SOFTMAX_CALIBRATION
# constants used to live here. `ENABLE_SOFTMAX_CALIBRATION` was hardcoded to False and the helper
# had no callers — removed. The live softmax now lives in the retriever's per-channel calibration
# and the final fusion softmax (env `FUSION_TEMPERATURE`, default 0.25).


def calibrate_confidence(margin, has_detail, struct_top1, detail_top1, same_as_last):
    """温和的置信度标定，避免"先拉满再腰斩" """
    import numpy as np
    
    # margin→sigmoid
    conf_m = 1/(1 + np.exp(-12*(margin - 0.15)))   # 0.15 作为"可分"分界
    if not has_detail:
        conf_m *= 0.92

    # 一致性：没有 top1 的时候不要给 1.15。
    # 之前还有一个 `elif are_neighbors(struct_top1, detail_top1): cons = 1.05` 分支，
    # 但 are_neighbors 永远 return False（模块作用域看不到 retriever 的 _are_neighbors），
    # 所以该 1.05 路径死了——直接拿掉，简化为 same/diff/missing 三态。
    if struct_top1 and detail_top1:
        cons = 1.15 if struct_top1 == detail_top1 else 0.92
    else:
        cons = 0.95

    cont = 1.10 if same_as_last else 1.00

    # 之前还有 `* max(0.75, float(content_match or 1.0))`，但两处 caller 都硬编码 content_match=1.0，
    # 这一项实际恒为 1.0——删掉参数 + 这一项的乘法，让 calibrate_confidence 的签名诚实反映用了什么。
    conf = conf_m * cons * cont
    
    # 🔧 FIX: 移除硬编码的0.98上限，使用动态上限
    # 基于margin动态调整上限：高margin时允许更高confidence
    if margin > 0.5:
        max_conf = 0.95  # 高margin时允许95%
    elif margin > 0.2:
        max_conf = 0.90  # 中等margin时允许90%
    else:
        max_conf = 0.80  # 低margin时限制在80%
    
    conf = float(np.clip(conf, 0.20, max_conf))

    # 低置信度不更新会话，避免"定位抖动"
    if conf < 0.35:
        return conf, False   # False=不要 update_session
    return conf, True


def calculate_calibrated_confidence_and_margin(
    candidates: List[Dict],
    top_k: int = 5,
    session_id: Optional[str] = None,
    site_id: Optional[str] = None,
) -> tuple:
    """统一置信度计算：margin → sigmoid → consistency × continuity

    🔧 FIX P0-1: 原实现把 struct_top1/detail_top1 写死成 None，导致
       calibrate_confidence 里 consistency 永远走 else 分支返回 0.92（-8% 惩罚）。
       现在从 candidates[0] 上读 retriever 挂上的 _struct_top1_id / _detail_top1_id。
    🔧 FIX P0-2: 原实现 same_as_last 永远为 True（current_node_id == None 永真），
       现在从 SESSIONS[session_id]["current_location"] 读真实上一帧位置比较。

    Args:
        candidates: 融合后的候选列表（retriever.retrieve 输出）
        top_k: 取前 k 个候选（仅用于潜在扩展，当前只用 top1/top2）
        session_id: 当前会话 id，用于读取上一帧位置（不传则 same_as_last=False）
        site_id: 当前场景 id（保留供未来扩展，目前未使用）

    Returns:
        (confidence, margin, top1_raw_score, top2_raw_score)
    """
    if not candidates:
        return 0.0, 0.0, 0.0, 0.0

    top_scores = [float(c["score"]) for c in candidates[:top_k]]
    if len(top_scores) < 2:
        # 只有一个候选时，margin=0，置信度走标定函数
        top1_score = top_scores[0]
        top1 = candidates[0]
        confidence, _ = calibrate_confidence(
            margin=0.0,
            has_detail=top1.get("has_detail", False),
            struct_top1=top1.get("_struct_top1_id"),
            detail_top1=top1.get("_detail_top1_id"),
            same_as_last=False,
        )
        return confidence, 0.0, top1_score, 0.0

    top1_score = top_scores[0]
    top2_score = top_scores[1]
    margin = max(0.0, top1_score - top2_score)

    top1 = candidates[0]
    top1_id = top1.get("id")
    has_detail = top1.get("has_detail", False)
    struct_top1 = top1.get("_struct_top1_id")
    detail_top1 = top1.get("_detail_top1_id")

    # 从 session 读上一帧位置（用于 same_as_last 判定）
    previous_node_id = None
    if session_id and session_id in SESSIONS:
        previous_node_id = SESSIONS[session_id].get("current_location")
    same_as_last = bool(previous_node_id and top1_id == previous_node_id)

    confidence, _should_update = calibrate_confidence(
        margin=margin,
        has_detail=has_detail,
        struct_top1=struct_top1,
        detail_top1=detail_top1,
        same_as_last=same_as_last,
    )

    print(f"🔧 置信度标定: margin={margin:.3f}, has_detail={has_detail}, "
          f"struct_top1={struct_top1}, detail_top1={detail_top1}, "
          f"same_as_last={same_as_last} → confidence={confidence:.3f}")

    return confidence, margin, top1_score, top2_score

def apply_continuity_boost(top1_score: float, session_id: str, site_id: str, 
                          current_node_id: str, orientation_info: Dict = None) -> tuple:
    """修复：改进的连续性boost，避免过度惩罚
    
    Returns:
        tuple: (boost, reason)
    """
    # 注：原来这里有 TH_UP=0.60 / TH_DOWN=0.35 两个"粘性阈值"局部常量，但
    # 整个函数体内从未引用，纯死常量——拿掉。
    boost = 0.0
    reason = "none"
    
    try:
        # 🔧 FIX P0-3 配套：原代码用 f"{session_id}_{site_id}" 作 key 找不到 session
        # （update_session_location 实际用 session_id 作 key），且字段名是 "location" 不是 "node_id"
        session = SESSIONS.get(session_id, {})
        location_history = session.get("location_history", [])

        if len(location_history) > 0:
            last_location = location_history[-1].get("location")

            if last_location == current_node_id:
                # 位置一致：给予正向boost
                boost = 0.05
                reason = "location_consistency"
                print(f"🔧 位置一致性boost: +{boost:.3f}")
            elif last_location != current_node_id:
                # 位置变化：使用粘性阈值判断
                boost = 0.0  # 保持中性
                reason = "location_change_neutral"
                print(f"🔧 位置变化，保持中性: {boost:.3f}")
                
        # 方向一致性检查
        if orientation_info and "confidence" in orientation_info:
            orientation_conf = orientation_info["confidence"]
            if orientation_conf > 0.7:
                boost += 0.03
                reason += "_orientation_boost"
                print(f"🔧 方向一致性boost: +0.03")
                
    except Exception as e:
        print(f"⚠️ 连续性boost计算失败: {e}")
        boost = 0.0
        reason = "error"
    
    # 限制boost范围
    boost = max(-0.05, min(0.10, boost))
    
    return boost, reason

# 加载拓扑
try:
    with open(os.path.join(os.path.dirname(__file__), "topology.json"), "r", encoding="utf-8") as f:
        TOPO = json.load(f)
    print("✅ Topology loaded successfully")
except Exception as e:
    print(f"⚠️  Failed to load topology: {e}")
    TOPO = {}

def is_hop1(site_id: str, a: str, b: str) -> bool:
    """Check if two nodes are within 1 hop (directly connected)"""
    if not a or not b: return False
    if a == b: return True
    g = TOPO.get(site_id, {})
    return b in (g.get(a) or [])

# ✅ 新增：RQ3 数据记录函数
def record_misbelief(req_id: str, session_id: str, site_id: str, 
                     predicted_node: str, gt_node_id: str, 
                     clarification_triggered: bool, confidence: float):
    """记录误信率数据"""
    if not gt_node_id:
        return
    
    misbelief = 1 if (predicted_node != gt_node_id and not clarification_triggered) else 0
    
    # 更新 locate_log.csv 中的 misbelief 字段
    # 注意：这里需要找到对应的行并更新，或者在前端调用时直接传入
    return misbelief

def start_clarification_session(session_id: str, site_id: str, req_id: str, 
                              predicted_node: str, gt_node_id: str, provider: str) -> str:
    """Start clarification dialogue session, return clarification_id"""
    clarification_id = str(uuid.uuid4())
    
    # Get log paths and ensure headers
    paths = _log_paths(provider)
    _ensure_headers(paths)
    
    # ✅ Only write when logging is enabled
    enabled, run_id = _is_logging(session_id, provider)
    if enabled:
        with open(paths["clar"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                site_id, run_id, datetime.utcnow().isoformat(), clarification_id, session_id, provider,
                req_id, 1, "trigger",  # event: trigger
                "Low confidence triggered", "Clarification started",
                predicted_node, gt_node_id or "", False
            ])
    
    print(f"🔍 Clarification session started: {clarification_id}")
    return clarification_id

def record_clarification_round(clarification_id: str, session_id: str, site_id: str,
                              round_count: int, user_question: str, system_answer: str,
                              predicted_node: str, gt_node_id: str, provider: str):
    """Record each round of clarification dialogue"""
    paths = _log_paths(provider)
    _ensure_headers(paths)
    
    # ✅ Only write when logging is enabled
    enabled, run_id = _is_logging(session_id, provider)
    if enabled:
        with open(paths["clar"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                site_id, run_id, datetime.utcnow().isoformat(), clarification_id, session_id, provider,
                "trial",  # phase: trial phase
                "", round_count, "step",  # event: step
                user_question, system_answer, predicted_node, gt_node_id or "", False
            ])

def end_clarification_session(clarification_id: str, session_id: str, site_id: str,
                            total_rounds: int, final_predicted_node: str, gt_node_id: str, provider: str):
    """End clarification dialogue session, record success rate"""
    clarification_success = final_predicted_node == gt_node_id
    
    # Get log paths and ensure headers
    paths = _log_paths(provider)
    _ensure_headers(paths)
    
    # ✅ Only write when logging is enabled
    enabled, run_id = _is_logging(session_id, provider)
    if enabled:
        with open(paths["clar"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                site_id, run_id, datetime.utcnow().isoformat(), clarification_id, session_id, provider,
                "trial",  # phase: trial phase
                "", total_rounds, "success" if clarification_success else "fail",  # event: success/fail
                f"Session ended", f"Final prediction: {final_predicted_node}", 
                final_predicted_node, gt_node_id or "", clarification_success
            ])
    
    print(f"🔍 Clarification session ended: {clarification_id}, success: {clarification_success}")

def start_error_recovery(session_id: str, site_id: str, error_node: str, 
                        correct_node: str, provider: str) -> str:
    """Start error recovery timing, return recovery_id"""
    recovery_id = str(uuid.uuid4())
    error_start_time = _now_ms()
    
    # Get log paths and ensure headers
    paths = _log_paths(provider)
    _ensure_headers(paths)
    
    # ✅ Only write when logging is enabled
    enabled, run_id = _is_logging(session_id, provider)
    if enabled:
        with open(paths["recovery"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                site_id, run_id, datetime.utcnow().isoformat(), session_id, provider,
                "trial",  # phase: trial phase
                "", error_start_time, error_node, correct_node
            ])
    
    print(f"⚠️  Error recovery started: {recovery_id}, from {error_node} to {correct_node}")
    return recovery_id

def end_error_recovery(recovery_id: str, session_id: str, site_id: str,
                      correct_node: str, recovery_path: str = "", provider: str = ""):
    """End error recovery timing, calculate recovery duration"""
    if not provider:
        print("⚠️  Provider not specified for error recovery end")
        return 0
    
    # Get log paths and ensure headers
    paths = _log_paths(provider)
    _ensure_headers(paths)
    
    # ✅ Only write when logging is enabled
    enabled, run_id = _is_logging(session_id, provider)
    if enabled:
        # Calculate recovery duration (simplified version, direct recording)
        recovery_duration = _now_ms()  # This can be optimized for actual recovery duration calculation
        
        with open(paths["recovery"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                site_id, run_id, datetime.utcnow().isoformat(), session_id, provider,
                "trial",  # phase: trial phase
                "", recovery_duration, "", correct_node
            ])
        
        print(f"✅ Error recovery completed: {recovery_id}, duration: {recovery_duration}ms")
        return recovery_duration
    
    return 0

# ---------- Opening outputs (Independent variables only take effect here) ----------
HARD_OUTPUTS_EN = {
    "SCENE_A_MS": {
        "base": "You are just inside the Maker Space entrance, facing inward. Walk straight about six steps. Around step five there is a stack of boxes—slow down and pass on one side. Beyond the boxes you enter the open atrium. Landmarks: QR-code bookshelf behind you; black drawer wall to your right.",
        "ft":   "Face forward and walk six steps. Slow at step five to bypass boxes. Continue straight to enter the open atrium. Landmarks: QR-code bookshelf behind; drawer wall on your right."
    },
    "SCENE_B_STUDIO": {
        "base": "You are at the studio entry facing the large window. Walk forward five steps to the window. Then turn left and walk about five steps to the chair next to the orange sofa. Watch your step—around step three there may be a floor cable.",
        "ft":   "Face forward. Walk five steps to the large window and stop. Turn left and walk five steps to the chair beside the orange sofa. Slow down near step three for a floor cable."
    }
}
HARD_OUTPUTS_ZH = {
    "SCENE_A_MS": {
        "base": "你在 Maker Space 入口内侧。直行约六步。第五步有纸箱，减速从一侧绕过。越过后进入开阔的中庭。确认点：身后二维码书架；右侧黑色抽屉墙。",
        "ft":   "面向前方直行六步。第五步绕过纸箱，继续前行进入中庭。确认点：身后二维码书架；右侧抽屉墙。"
    },
    "SCENE_B_STUDIO": {
        "base": "你在工作室入口，正对大窗。向前五步到窗前，再左转五步到橙色沙发旁的椅子。注意第三步可能有地面电缆。",
        "ft":   "面向前方走五步至大窗停。再向左走五步到橙色沙发旁的椅子。第三步附近可能有电缆，请放慢。"
    }
}

# ---------- Embedding & Index ----------
from sentence_transformers import SentenceTransformer
EMB = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Import dual-channel retrieval
try:
    import sys
    import os
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    import dual_channel_retrieval  # load-check only — the actual retriever class
    # lives in app.py; this import just confirms the module is importable.
    _ = dual_channel_retrieval
    DUAL_CHANNEL_AVAILABLE = True
    print("✅ Dual channel retrieval module imported successfully")
except ImportError as e:
    print(f"⚠️  Dual channel retrieval module not available: {e}")
    print("⚠️  Using legacy system")
    DUAL_CHANNEL_AVAILABLE = False

import pathlib

try:
    import faiss  # type: ignore
    USE_FAISS = True
except Exception:
    from sklearn.neighbors import NearestNeighbors
    USE_FAISS = False

# Initialize unified dual-channel retriever
MODEL_DIR_PATH = pathlib.Path(MODEL_DIR)
UNIFIED_RETRIEVER = None

def get_unified_retriever():
    """Get or create enhanced dual-channel retriever with improved fusion strategy"""
    print("🔧 Initializing enhanced dual-channel retriever...")
    
    global UNIFIED_RETRIEVER
    if UNIFIED_RETRIEVER is None:
        try:
            print("🔧 Creating enhanced dual-channel retriever with improved fusion...")
            
            # 🔧 ENHANCED: Create an enhanced dual-channel retriever with improved fusion strategy
            class EnhancedDualChannelRetriever:
                def __init__(self):
                    # env-tunable (FUSION_STRUCT_TAU / FUSION_DETAIL_TAU)
                    self.structure_tau = FUSION_STRUCT_TAU
                    self.detail_tau = FUSION_DETAIL_TAU
                    self.alpha = 0.35          # 结构通道权重（进一步降低，减少宽泛索引词影响）
                    self.beta = 0.65           # 细节通道权重（进一步提高，增强内容匹配）
                    self.gamma = FUSION_GAMMA  # env-tunable (FUSION_GAMMA)
                    
                    # 🔧 FIX: 延迟加载数据，等待场景信息
                    self.structure_data = None
                    self.detail_data = None
                    self.topology_graph = {}
                    self.topology_empty = False
                    self.current_scene_filter = None
                    
                    print(f"✅ Enhanced dual-channel retriever initialized (Margin Boost Mode)")
                    print(f"   Structure tau: {self.structure_tau} (sharper distribution)")
                    print(f"   Detail tau: {self.detail_tau} (sharper distribution)")
                    print(f"   Enhanced fusion: α={self.alpha}, β={self.beta}, γ={self.gamma}")
                    print(f"   Margin boost: exponential amplification + continuity boost")
                    print(f"   Structure bias: enhanced with 1.5x clarity multiplier")
                
                def _build_topology_graph(self):
                    """构建拓扑图用于连续性检查"""
                    try:
                        # 从结构数据中提取拓扑信息
                        if hasattr(self, 'structure_data') and self.structure_data:
                            topology = self.structure_data.get('input', {}).get('topology', {})
                            nodes = topology.get('nodes', [])
                            edges = topology.get('edges', [])
                            
                            # 🔧 NEW: Fail-fast检查
                            if not nodes:
                                print("❌ 空拓扑图！中止融合，使用预设/上一帧状态")
                                self.topology_graph = {}
                                return False
                            
                            print(f"🔧 开始构建拓扑图: {len(nodes)} 个节点, {len(edges)} 条边")
                            
                            for node in nodes:
                                node_id = node['id']
                                self.topology_graph[node_id] = []
                                
                                # 从edges中提取邻居信息
                                for edge in edges:
                                    if edge['from'] == node_id:
                                        self.topology_graph[node_id].append(edge['to'])
                                    elif edge['to'] == node_id:
                                        self.topology_graph[node_id].append(edge['from'])
                        
                        print(f"🔧 拓扑图构建完成: {len(self.topology_graph)} 个节点")
                        
                        # 🔧 NEW: 验证拓扑图完整性
                        if len(self.topology_graph) == 0:
                            print("❌ 拓扑图为空！中止融合，使用预设/上一帧状态")
                            self.topology_graph = {}
                            return False  # 返回False表示构建失败
                        else:
                            print(f"🔧 拓扑图验证: 每个节点的邻居数量")
                            for node_id, neighbors in self.topology_graph.items():
                                print(f"   {node_id}: {len(neighbors)} 个邻居")
                            return True  # 返回True表示构建成功
                                
                    except Exception as e:
                        print(f"⚠️ 拓扑图构建失败: {e}")
                        self.topology_graph = {}
                        return False  # 返回False表示构建失败
                
                def _get_node_neighbors(self, node_id):
                    """获取节点的邻居列表"""
                    return self.topology_graph.get(node_id, [])
                
                def _are_neighbors(self, node1, node2):
                    """检查两个节点是否为邻居"""
                    if not node1 or not node2:
                        return False
                    if node1 == node2:
                        return True
                    return node2 in self.topology_graph.get(node1, [])
                
                def _get_previous_location(self):
                    """获取上一帧位置（从当前 session 读）

                    🔧 FIX P0-3: 原实现写死 return None，导致 topology continuity prior
                    永远不会触发（+0.25 / +0.10 boost 失效）。
                    retrieve() 调用时通过 _session_id 属性传入，这里从 SESSIONS 读取。
                    """
                    sid = getattr(self, '_session_id', None)
                    if not sid or sid not in SESSIONS:
                        return None
                    return SESSIONS[sid].get("current_location")
                
                def _load_structure_data(self):
                    """加载结构数据（根据场景动态选择）"""
                    try:
                        # 🔧 FIX: 动态选择正确的结构文件
                        import os
                        
                        # 获取当前场景ID（从实例属性或默认值）
                        current_scene = getattr(self, 'current_scene_filter', 'SCENE_A_MS')
                        print(f"🔧 当前场景: {current_scene}")
                        
                        # 根据场景选择正确的结构文件
                        if current_scene == "SCENE_B_STUDIO":
                            structure_file = os.path.join(DATA_DIR, "Sense_B_Finetuned.fixed.jsonl")
                            print(f"🔧 选择Sense_B结构文件: {structure_file}")
                        else:
                            # 默认使用Sense_A
                            structure_file = os.path.join(DATA_DIR, "Sense_A_Finetuned.fixed.jsonl")
                            print(f"🔧 选择Sense_A结构文件: {structure_file}")
                        
                        if os.path.exists(structure_file):
                            with open(structure_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                print(f"🔧 成功加载结构数据: {structure_file}")
                                return data
                        else:
                            # 🔧 FIX P0-7: 文件不存在直接报空，不再返回 mock fake data
                            # (mock data 会让系统静默用 3 个假节点跑，掩盖配置错误)
                            print(f"❌ 结构数据文件不存在: {structure_file}")
                            return {}
                    except Exception as e:
                        print(f"❌ Failed to load structure data: {e}")
                        return {}
                
                def _ensure_structure_data_loaded(self):
                    """确保结构数据已加载（延迟加载）"""
                    if self.structure_data is None:
                        print("🔧 延迟加载结构数据...")
                        self.structure_data = self._load_structure_data()
                        # 构建拓扑图
                        topology_built = self._build_topology_graph()
                        if not topology_built:
                            self.topology_empty = True
                            print("⚠️ 拓扑图为空，融合时将使用预设状态")
                        else:
                            self.topology_empty = False
                
                def _ensure_detail_data_loaded(self):
                    """确保细节数据已加载（延迟加载）"""
                    if self.detail_data is None:
                        print("🔧 延迟加载细节数据...")
                        self.detail_data = self._load_detail_data()
                
                def _load_detail_data(self):
                    """加载细节数据（Sense_A_MS.jsonl等）— 委托给 _load_detail_once 真实加载

                    🔧 FIX P0-7: 原实现返回 3 个 mock 节点会让 self.detail_data 静默挂上假数据，
                    现在统一从 _load_detail_once 走真实加载路径。
                    """
                    scene_id = getattr(self, 'current_scene_filter', None) or 'SCENE_A_MS'
                    return self._load_detail_once(scene_id)
                
                def _channel_calibration(self, scores, tau):
                    """步骤A：通道内校准 - 温度化softmax（增强版）"""
                    if not scores:
                        return []
                    
                    # 温度缩放
                    scaled_scores = [score / tau for score in scores]
                    
                    # Softmax
                    max_score = max(scaled_scores)
                    exp_scores = [np.exp(score - max_score) for score in scaled_scores]
                    sum_exp = sum(exp_scores)
                    
                    probabilities = [exp_score / sum_exp for exp_score in exp_scores]
                    
                    # 温和的概率调整：避免过度放大
                    if probabilities:
                        # 找到最大概率的索引
                        max_prob_idx = probabilities.index(max(probabilities))
                        
                        # 温和调整：只在概率过低时适当提升
                        top1_prob = probabilities[max_prob_idx]
                        if top1_prob < 0.3:  # 只在top1概率过低时调整
                            # 温和提升top1概率
                            adjustment_factor = 1.1  # 从1.2降低到1.1
                            probabilities[max_prob_idx] = min(0.8, top1_prob * adjustment_factor)
                            
                            # 重新归一化其他概率
                            remaining_prob = 1.0 - probabilities[max_prob_idx]
                            other_probs = [p for i, p in enumerate(probabilities) if i != max_prob_idx]
                            if other_probs and sum(other_probs) > 0:
                                for i in range(len(probabilities)):
                                    if i != max_prob_idx:
                                        probabilities[i] = (probabilities[i] / sum(other_probs)) * remaining_prob
                    
                    return probabilities
                
                def _conflict_gate(self, alpha, beta, struct_logit, detail_logit, gap=0.5):
                    """冲突门控：两通道 top1 logit 差距大时，偏向结构通道（permanence-aware backbone）

                    🔧 FIX P1-2: 原实现 alpha*=0.7, beta*=1.1 — 冲突时反而更信细节通道，
                    跟论文 §3.2 "structural backbone for localisation" 叙事完全相反。
                    现在改成 alpha*=1.1, beta*=0.7：冲突时结构通道（建筑骨架）压制噪声大的细节通道。
                    """
                    if abs(struct_logit - detail_logit) > gap:
                        return alpha * 1.1, beta * 0.7
                    return alpha, beta
                
                def _safe_sharpen(self, probs, tau=0.10):
                    """🔧 FIX: 修复过度极端的二次锐化"""
                    try:
                        import numpy as np
                        
                        def softmax(x):
                            x = np.asarray(x, dtype=np.float64)
                            x = x - np.max(x)
                            e = np.exp(x)
                            s = e.sum()
                            return e / (s if s > 0 else 1.0)
                        
                        def sharpen(probs, tau=0.10):
                            p = np.asarray(probs, dtype=np.float64)
                            eps = 1e-12
                            p = np.clip(p, eps, 1.0 - eps)
                            logits = np.log(p) - np.log(1.0 - p)
                            return softmax(logits / max(tau, 1e-6))
                        
                        # 🔧 FIX: 动态调整温度，避免过度极端
                        # 检查原始分数的分布
                        probs_array = np.array(probs)
                        max_prob = np.max(probs_array)
                        min_prob = np.min(probs_array)
                        prob_range = max_prob - min_prob
                        
                        # 如果分数差异已经很大，使用更高温度
                        if prob_range > 0.5:
                            adjusted_tau = max(0.3, tau)  # 至少0.3
                            print(f"🔧 检测到高差异({prob_range:.3f})，调整温度: {tau:.2f} → {adjusted_tau:.2f}")
                            tau = adjusted_tau
                        
                        # 应用安全的二次锐化
                        fused = probs  # 先得到融合后的概率
                        sharpened = sharpen(fused, tau=tau)
                        
                        # 🔧 FIX: 限制锐化后的分数范围，避免过度极端
                        sharpened_array = np.array(sharpened)
                        max_score = 0.8  # 限制最高分数
                        min_score = 0.05  # 限制最低分数
                        
                        # 应用范围限制
                        sharpened_array = np.clip(sharpened_array, min_score, max_score)
                        
                        # 重新归一化
                        total = np.sum(sharpened_array)
                        if total > 0:
                            sharpened_array = sharpened_array / total
                        
                        return sharpened_array.tolist()  # 转换回Python列表
                        
                    except Exception as e:
                        print(f"⚠️ 二次锐化失败，使用原始概率: {e}")
                        return probs  # 失败时返回原始概率
                
                def _calculate_channel_entropy(self, probabilities):
                    """计算归一化通道熵 H ∈ [0,1]（0=高确定度，1=均匀分布）

                    Per paper Eq.(4): H_c = -1/log(k) Σ p_i log p_i
                    """
                    if not probabilities or len(probabilities) < 2:
                        return 1.0

                    entropy = 0.0
                    for p in probabilities:
                        if p > 0:
                            entropy -= p * np.log(p)

                    # 归一化到 [0,1]：除以 log(k)（最大熵）
                    return float(entropy / np.log(len(probabilities)))
                
                def _adaptive_weights(self, struct_entropy, detail_entropy):
                    """根据通道熵自适应调整权重（标准公式实现）"""
                    # Diagnostic force-override path (env: FUSION_ALPHA_FORCE / FUSION_BETA_FORCE).
                    # Both -1 → use adaptive (default); both ≥ 0 → bypass adaptive entirely.
                    if FUSION_ALPHA_FORCE >= 0 and FUSION_BETA_FORCE >= 0:
                        print(f"🔧 FORCE α/β override: α={FUSION_ALPHA_FORCE}, β={FUSION_BETA_FORCE}")
                        return FUSION_ALPHA_FORCE, FUSION_BETA_FORCE
                    # 按照标准公式：α = (1-H_struct) / ((1-H_struct) + (1-H_detail))
                    # 熵越低，权重越高（分布越尖锐，越可信）

                    # 计算清晰度（1 - 熵）
                    struct_clarity = 1.0 - struct_entropy
                    detail_clarity = 1.0 - detail_entropy
                    
                    # 防止除零错误
                    total_clarity = struct_clarity + detail_clarity
                    
                    if total_clarity > 0:
                        # 标准公式实现
                        alpha = struct_clarity / total_clarity
                        beta = detail_clarity / total_clarity
                        
                        # 限制权重范围，避免极端值
                        alpha = max(0.1, min(0.9, alpha))
                        beta = max(0.1, min(0.9, beta))
                        
                        # 重新归一化
                        total_weight = alpha + beta
                        alpha = alpha / total_weight
                        beta = beta / total_weight
                        
                    else:
                        # 如果两个通道都很平（高熵），使用默认权重
                        alpha, beta = FUSION_ALPHA_FB, FUSION_BETA_FB
                    
                    print(f"🔧 Dynamic weight calculation:")
                    print(f"   Structure entropy: {struct_entropy:.3f} → clarity: {struct_clarity:.3f} → weight: {alpha:.3f}")
                    print(f"   Detail entropy: {detail_entropy:.3f} → clarity: {detail_clarity:.3f} → weight: {beta:.3f}")
                    print(f"   Total clarity: {total_clarity:.3f}")
                    
                    return alpha, beta
                
                def _enhanced_fusion(self, struct_candidates, detail_candidates, caption, scene_filter):
                    """步骤B：增强的通道间融合（对数几率相加）+ 反证惩罚机制"""
                    if not struct_candidates:
                        return []
                    
                    try:
                        # 🔧 NEW: 反证惩罚机制
                        def apply_negatives(score, node_meta, query_text, penalty=FUSION_NEG_PENALTY):
                            """应用反证惩罚：如果查询文本命中节点的negative提示，则降低分数。
                            返回 (新分数, 命中数)，命中数供 DG2 区分度打点使用。"""
                            neg = set(node_meta.get("retrieval", {}).get("negative", []))
                            hit = sum(1 for n in neg if n in query_text.lower())
                            if hit > 0:
                                print(f"🔍 反证惩罚: {node_meta.get('id', 'unknown')} 命中 {hit} 个negative提示，惩罚: {hit * penalty:.3f}")
                            return score - hit * penalty, hit
                        
                        # 🔧 NEW: 结构通道稳态词过滤（不污染原始文本）
                        MOVABLE = {"suitcase", "bag", "backpack", "person", "cup", "bottle", "laptop", "phone", "book"}
                        LOW_TRUST = {"box": 0.5, "bins": 0.6, "item": 0.7, "stuff": 0.6, "thing": 0.5, "object": 0.5}
                        
                        def term_weight(token):
                            """获取词的权重，不修改原始文本"""
                            return LOW_TRUST.get(token.lower(), 1.0)
                        
                        def stable_query(text: str):
                            """结构通道专用：过滤可移动物体，保留固定地标（不污染文本）"""
                            t = text.lower()
                            # 完全移除可移动物体（包括复数形式）
                            for w in MOVABLE:
                                # 移除单数形式
                                t = t.replace(f" {w} ", " ")
                                t = t.replace(f"{w} ", " ")
                                t = t.replace(f" {w}", " ")
                                # 移除复数形式
                                t = t.replace(f" {w}s ", " ")
                                t = t.replace(f"{w}s ", " ")
                                t = t.replace(f" {w}s", " ")
                            
                            # 清理多余空格和标点
                            cleaned = " ".join(t.split())
                            cleaned = cleaned.rstrip(" .")
                            if cleaned != text.lower():
                                print(f"🔍 结构通道稳态过滤: '{text}' → '{cleaned}'")
                            return cleaned
                        
                        # 对结构通道分数应用反证惩罚 + 稳态过滤
                        caption_lower = caption.lower()
                        stable_caption = stable_query(caption)  # 结构通道用稳态版本
                        stable_query_applied = (stable_caption != caption_lower)

                        for i, struct_cand in enumerate(struct_candidates):
                            original_score = struct_cand['score']
                            # 先应用稳态过滤（在反证惩罚之前）
                            penalized_score, neg_hits = apply_negatives(original_score, struct_cand, stable_caption)
                            struct_cand['_neg_hits'] = neg_hits
                            if penalized_score != original_score:
                                print(f"🔍 结构通道反证惩罚: {struct_cand['id']} {original_score:.3f} → {penalized_score:.3f}")
                                struct_cand['score'] = penalized_score
                        
                        # 提取分数（已应用反证惩罚）
                        struct_scores = [c['score'] for c in struct_candidates]
                        detail_scores = [c['score'] for c in detail_candidates] if detail_candidates else [0.0] * len(struct_candidates)
                        
                        # 步骤A：通道内校准 - 温度化softmax
                        struct_probs = self._channel_calibration(struct_scores, self.structure_tau)
                        detail_probs = self._channel_calibration(detail_scores, self.detail_tau)
                        
                        print(f"🔧 Channel calibration completed:")
                        print(f"   Structure probs: {[f'{p:.3f}' for p in struct_probs[:3]]}")
                        print(f"   Detail probs: {[f'{p:.3f}' for p in detail_probs[:3]]}")
                        
                        # 新增：显示空间概念匹配调试信息
                        print(f"🔍 Space concept matching debug:")
                        print(f"   Caption: {caption}")
                        space_concepts = ["large open space", "open space", "open area", "atrium"]
                        for concept in space_concepts:
                            if concept in caption.lower():
                                print(f"   ✅ Detected space concept: '{concept}'")
                                break
                        
                        # 计算通道熵和自适应权重
                        struct_entropy = self._calculate_channel_entropy(struct_probs)
                        detail_entropy = self._calculate_channel_entropy(detail_probs)
                        
                        alpha, beta = self._adaptive_weights(struct_entropy, detail_entropy)
                        
                        print(f"🔧 Adaptive weights:")
                        print(f"   Structure entropy: {struct_entropy:.3f}, weight: {alpha:.3f}")
                        print(f"   Detail entropy: {detail_entropy:.3f}, weight: {beta:.3f}")
                        
                        # 冲突门控检查：检查两个通道的top1是否不同且差异很大
                        conflict_detected = False
                        conflict_threshold = FUSION_CONFLICT_GAP  # env-tunable
                        alpha_final = alpha
                        beta_final = beta

                        # 🔧 FIX P0-1/P0-2 配套：记录两个通道的 top1 id，
                        # 后续 calculate_calibrated_confidence_and_margin 读取以计算 consistency
                        struct_top1_id = struct_candidates[0]['id'] if struct_candidates else None
                        detail_top1_id = detail_candidates[0]['id'] if detail_candidates else None

                        # 概率转对数几率 - 安全版本
                        def prob_to_logit(p, eps=1e-6):
                            p = min(max(p, eps), 1 - eps)
                            import math
                            return math.log(p/(1-p))

                        if len(struct_candidates) > 0 and len(detail_candidates) > 0:
                            
                            if struct_top1_id != detail_top1_id:
                                # 计算两个通道top1的logit差异
                                struct_top1_logit = prob_to_logit(struct_probs[0])
                                detail_top1_logit = prob_to_logit(detail_probs[0])
                                logit_diff = abs(struct_top1_logit - detail_top1_logit)
                                
                                if logit_diff > conflict_threshold:
                                    conflict_detected = True
                                    print(f"⚠️ Channel conflict detected:")
                                    print(f"   Structure top1: {struct_top1_id} (logit: {struct_top1_logit:.3f})")
                                    print(f"   Detail top1: {detail_top1_id} (logit: {detail_top1_logit:.3f})")
                                    print(f"   Logit difference: {logit_diff:.3f} > {conflict_threshold}")
                                    print(f"   Using conflict gating strategy")
                                    
                                    # 🔧 NEW: 冲突门控改为局部返回值，只执行一次
                                    alpha_final, beta_final = self._conflict_gate(alpha, beta, struct_top1_logit, detail_top1_logit, gap=FUSION_CONFLICT_GAP)
                                    print(f"🔧 冲突门控: α={alpha:.3f}→{alpha_final:.3f}, β={beta:.3f}→{beta_final:.3f}")
                        
                        # 融合对数几率（带冲突门控）
                        fused_candidates = []
                        fused_logits = []  # 收集所有融合后的logits用于二次锐化
                        
                        for i, struct_cand in enumerate(struct_candidates):
                            struct_logit = prob_to_logit(struct_probs[i])
                            detail_logit = prob_to_logit(detail_probs[i]) if i < len(detail_probs) else 0.0
                            
                            # 使用最终权重进行融合（无论是否有冲突）
                            fused_logit = alpha_final * struct_logit + beta_final * detail_logit
                            
                            # 连续性boost（γ*boost）
                            boost_value = self._calculate_continuity_boost(struct_cand, caption, scene_filter)
                            fused_logit += self.gamma * boost_value
                            
                            # 🔧 NEW: 拓扑连续性prior
                            def topo_prior(prev_node, current_node):
                                """拓扑连续性prior：上一帧的邻居 +0.25，二阶邻居 +0.10，其它 0"""
                                if prev_node is None:
                                    return 0.0
                                
                                # 获取上一帧节点的邻居
                                prev_neighbors = self._get_node_neighbors(prev_node)
                                if current_node in prev_neighbors:
                                    return 0.25  # 直接邻居
                                
                                # 检查二阶邻居
                                for neighbor in prev_neighbors:
                                    neighbor_neighbors = self._get_node_neighbors(neighbor)
                                    if current_node in neighbor_neighbors:
                                        return 0.10  # 二阶邻居
                                
                                return 0.0
                            
                            # 应用拓扑连续性prior
                            prev_node = self._get_previous_location()
                            topo_boost = topo_prior(prev_node, struct_cand['id'])
                            if topo_boost > 0:
                                print(f"🔍 拓扑连续性prior: {struct_cand['id']} +{topo_boost:.3f}")
                            
                            fused_logit += topo_boost

                            # 🔧 FIX P1-6: 删除 per-candidate sigmoid (fused_prob = 1/(1+exp(-l)))
                            # 那种做法把每个候选当独立二分类处理，所有候选的 sigmoid 输出加起来不等于 1，
                            # 后续 _safe_sharpen 再当概率分布 softmax 在数学上不自洽。
                            # 改成：循环里只收集 fused_logits，循环外对所有 logits 做一次 softmax(温度 T)。
                            fused_logits.append(fused_logit)

                            # 创建融合后的候选（score 先占位 0.0，循环外 softmax 覆盖）
                            fused_cand = struct_cand.copy()
                            fused_cand["score"] = 0.0
                            fused_cand["structure_score"] = struct_cand["score"]
                            fused_cand["detail_score"] = detail_candidates[i]["score"] if i < len(detail_candidates) else 0.0
                            fused_cand["fusion_weights"] = {"alpha": alpha, "beta": beta, "gamma": self.gamma}
                            fused_cand["boost_value"] = boost_value
                            fused_cand["conflict_strategy"] = "conflict_gated" if conflict_detected else "normal"
                            # DG2 区分度打点用：把 neg_hits + stable_query_applied 带到下游
                            fused_cand["_neg_hits"] = struct_cand.get("_neg_hits", 0)
                            fused_cand["_stable_query_applied"] = stable_query_applied

                            fused_candidates.append(fused_cand)

                        # 🔧 FIX P0-1/P0-2 配套：把两个通道的 top1 id 挂在融合候选上，
                        # 供下游 calculate_calibrated_confidence_and_margin 计算 consistency
                        for fc in fused_candidates:
                            fc["_struct_top1_id"] = struct_top1_id
                            fc["_detail_top1_id"] = detail_top1_id

                        # 🔧 FIX P1-6: 对所有 fused_logits 做一次温度 softmax，得到合法概率分布（和为 1）
                        # 论文 §3.4 Eq.(3): p_final_i = exp(logit_i / T) / Σ exp(logit_j / T)
                        # 删除原 _safe_sharpen + clip[0.05, 0.8] 路径：那是为了修上一处 sigmoid 的副作用，
                        # 现在源头修正了，二次锐化不再需要。
                        if fused_logits:
                            T = float(os.getenv("FUSION_TEMPERATURE", "0.25"))  # 论文 Eq.(3) 的 T
                            logits_arr = np.asarray(fused_logits, dtype=np.float64)
                            logits_arr = logits_arr - np.max(logits_arr)  # 数值稳定
                            exp_logits = np.exp(logits_arr / max(T, 1e-6))
                            denom = exp_logits.sum()
                            probs = exp_logits / denom if denom > 0 else np.full_like(exp_logits, 1.0 / len(exp_logits))
                            for cand, p in zip(fused_candidates, probs):
                                cand["score"] = float(p)
                            print(f"🔧 Fusion softmax: T={T}, top1_prob={probs.max():.4f}")

                        print(f"🔧 Enhanced fusion completed: {len(fused_candidates)} candidates")
                        return fused_candidates
                        
                    except Exception as e:
                        print(f"⚠️ Enhanced fusion failed: {e}")
                        return struct_candidates  # 回退到结构通道
                
                def _build_detail_index(self):
                    """统一一次初始化detail数据，避免重复加载冲突"""
                    scene_id = getattr(self, 'current_scene_filter', 'SCENE_A_MS')
                    return self._load_detail_once(scene_id)
                
                def _load_detail_once(self, scene_id):
                    """统一一次初始化detail数据缓存"""
                    # 检查缓存 - 修复：使用实例变量而不是方法属性
                    if hasattr(self, '_detail_cache') and self._detail_cache.get("scene") == scene_id:
                        return self._detail_cache["data"]
                    
                    # 定义detail文件路径
                    DETAIL_PATHS = {
                        'SCENE_A_MS': os.path.join(DATA_DIR, 'Sense_A_MS.jsonl'),
                        'SCENE_B_STUDIO': os.path.join(DATA_DIR, 'Sense_B_Studio.jsonl')
                    }
                    
                    detail_index = {}
                    path = DETAIL_PATHS.get(scene_id)
                    
                    if not path or not os.path.exists(path):
                        print(f"⚠️ 未找到detail文件: scene={scene_id}")
                        data = {}
                    else:
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                for line in f:
                                    line = line.strip()
                                    if not line:
                                        continue
                                    try:
                                        item = json.loads(line)
                                        node_hint = item.get('node_hint', '')
                                        if node_hint:
                                            if node_hint not in detail_index:
                                                detail_index[node_hint] = []
                                            detail_index[node_hint].append(item)
                                    except json.JSONDecodeError:
                                        continue
                            
                            print(f"✅ Detail数据已加载: scene={scene_id}, {len(detail_index)} 个节点有detail数据")
                            for node_id, items in list(detail_index.items())[:3]:  # 只显示前3个
                                print(f"   {node_id}: {len(items)} 项")
                            if len(detail_index) > 3:
                                print(f"   ...等共 {len(detail_index)} 个节点")
                            data = detail_index
                        except Exception as e:
                            print(f"⚠️ Detail数据加载失败: {e}")
                            data = {}
                    
                    # 缓存结果 - 修复：使用实例变量
                    self._detail_cache = {"scene": scene_id, "data": data}
                    return data
                
                def _calculate_continuity_boost(self, candidate, caption, scene_filter):
                    """计算连续性boost值（γ*boost）- 增强版"""
                    try:
                        boost_value = 0.0
                        
                        # 1. 方向一致性boost
                        # 🔧 FIX P0-5: candidate 是 dict，不能用 hasattr (永远 False)
                        bearing = candidate.get('bearing_hint', '')
                        if bearing and any(word in caption.lower() for word in bearing.split()):
                            boost_value += 0.2

                        # 2. 拓扑合法性boost
                        # 🔧 FIX P0-5: candidate 是 dict，不能用 hasattr
                        if candidate.get('topology_valid', False):
                            boost_value += 0.15
                        
                        # 3. 空间关系一致性boost（增强）
                        spatial_relations = candidate.get('spatial_relations', {})
                        for relation, landmark in spatial_relations.items():
                            if landmark and any(word in caption.lower() for word in str(landmark).split()):
                                boost_value += 0.1  # 从0.05增加到0.1
                        
                        # 4. 关键词匹配boost（新增）
                        caption_lower = caption.lower()
                        candidate_text = candidate.get('text', '').lower()
                        if candidate_text:
                            # 计算关键词匹配度
                            caption_words = set(caption_lower.split())
                            text_words = set(candidate_text.split())
                            overlap = len(caption_words & text_words)
                            if overlap > 0:
                                boost_value += overlap * 0.05  # 每个匹配词+0.05
                        
                        # 5. 历史连续性boost（如果有session信息）
                        # 这里可以添加基于session历史的boost逻辑
                        
                        return min(0.5, boost_value)  # 从0.3增加到0.5，让boost有更大影响
                        
                    except Exception as e:
                        print(f"⚠️ Continuity boost calculation failed: {e}")
                        return 0.0

                def _pack_result(self, node_id, score, used_detail=None):
                    """统一返回值格式，确保永远返回三元组"""
                    return node_id, float(score), bool(used_detail) if used_detail is not None else False
                
                def _has_detail_data(self, scene_filter):
                    """检查是否有可用的detail数据"""
                    try:
                        if scene_filter == "SCENE_A_MS":
                            detail_file = os.path.join(DATA_DIR, "Sense_A_MS.jsonl")
                        elif scene_filter == "SCENE_B_STUDIO":
                            detail_file = os.path.join(DATA_DIR, "Sense_B_Studio.jsonl")
                        else:
                            return False
                        
                        return os.path.exists(detail_file) and os.path.getsize(detail_file) > 0
                    except Exception:
                        return False
                
                def _get_detail_for_node(self, node_id, scene_filter):
                    """获取特定节点的detail数据"""
                    try:
                        if scene_filter == "SCENE_A_MS":
                            detail_file = os.path.join(DATA_DIR, "Sense_A_MS.jsonl")
                        elif scene_filter == "SCENE_B_STUDIO":
                            detail_file = os.path.join(DATA_DIR, "Sense_B_Studio.jsonl")
                        else:
                            return []
                        
                        if not os.path.exists(detail_file):
                            return []
                        
                        detail_items = []
                        with open(detail_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip():
                                    try:
                                        detail_item = json.loads(line)
                                        if detail_item.get("node_hint") == node_id:
                                            detail_items.append(detail_item)
                                    except json.JSONDecodeError:
                                        continue
                        
                        return detail_items
                    except Exception:
                        return []

                def retrieve(self, caption, top_k=10, scene_filter=None, session_id=None):
                    """增强双通道检索：使用改进的融合策略，返回候选列表

                    🔧 FIX P0-3: 新增 session_id 参数，用于 _get_previous_location 拿上一帧位置。
                    不传时拓扑连续性 prior 不生效（保持向后兼容）。
                    """
                    # 设置当前场景过滤器与会话 id，用于 detail 加载和拓扑 prior
                    self.current_scene_filter = scene_filter
                    self._session_id = session_id

                    print(f"🔧 Enhanced dual-channel retrieval for: {caption[:50]}...")
                    
                    try:
                        # 🔧 FIX: 确保数据已加载
                        self._ensure_structure_data_loaded()
                        self._ensure_detail_data_loaded()
                        
                        # 步骤A：通道内校准 - 获取两个通道的候选
                        struct_candidates = self._retrieve_from_structure_map(caption, scene_filter, top_k)
                        detail_candidates = self._retrieve_from_detail_map(caption, scene_filter, top_k)
                        
                        # 检查detail数据可用性
                        has_detail_data = self._has_detail_data(scene_filter) and len(detail_candidates) > 0
                        print(f"🔧 Detail data availability: {has_detail_data} (found {len(detail_candidates)} detail candidates)")
                        
                        # 修复：为每个candidate添加has_detail标记
                        for candidate in struct_candidates:
                            candidate["has_detail"] = has_detail_data
                        
                        if not struct_candidates:
                            print("⚠️ No candidates found from structure map")
                            return []
                        
                        # 步骤B：通道间融合（对数几率相加）
                        fused_candidates = self._enhanced_fusion(
                            struct_candidates, detail_candidates, caption, scene_filter
                        )
                        
                        if not fused_candidates:
                            print("⚠️ Fusion failed")
                            return struct_candidates  # 回退到结构通道

                        # 🔧 FIX P1-3: 删除"连续 >3 次识别同一 POI 就 ×0.7" 反多样性补丁。
                        # 用户站在同一位置应该被稳定识别，不该被算法主动打分降级。
                        # （配合内部 _calculate_node_score 里的 0.8 倍补丁也一起删，见 P1-3 第二处）

                        # 按融合分数排序
                        fused_candidates.sort(key=lambda x: x["score"], reverse=True)

                        # 🆕 DG2 区分度打点：记录每次融合的 top1/top2/margin/通道一致性等
                        if dg_evaluator is not None and fused_candidates:
                            try:
                                top1 = fused_candidates[0]
                                top2 = fused_candidates[1] if len(fused_candidates) > 1 else None
                                dg_evaluator.dg2_evaluator.record_discrimination_event(
                                    session_id=(getattr(self, "_session_id", None) or "anonymous"),
                                    query=caption,
                                    top1_id=top1.get("id"),
                                    top1_score=top1.get("score", 0.0),
                                    top2_id=(top2.get("id") if top2 else None),
                                    top2_score=(top2.get("score", 0.0) if top2 else 0.0),
                                    struct_top1_id=top1.get("_struct_top1_id"),
                                    detail_top1_id=top1.get("_detail_top1_id"),
                                    struct_score=top1.get("structure_score", 0.0),
                                    detail_score=top1.get("detail_score", 0.0),
                                    neg_hits=int(top1.get("_neg_hits", 0)),
                                    stable_query_applied=bool(top1.get("_stable_query_applied", False)),
                                    scene_filter=scene_filter,
                                )
                            except Exception as _e:
                                print(f"⚠️ discrimination event record failed: {_e}")

                        # 🔧 FIX P1-1: 删除 retriever 内部冗余的 confidence/margin 计算
                        # （原代码 30 行：分段动态公式 + 指数放大 + clip，本来就被外部
                        # calculate_calibrated_confidence_and_margin 完全覆盖，是 dead path）。
                        # retriever 只负责返回排序好的候选 + score；置信度由统一的 calibrator 算。
                        for candidate in fused_candidates:
                            candidate["retrieval_method"] = "enhanced_dual_channel_fusion"
                            candidate["has_detail"] = has_detail_data

                        if fused_candidates:
                            top1_score = fused_candidates[0]['score']
                            top2_score = fused_candidates[1]['score'] if len(fused_candidates) > 1 else 0.0
                            print(f"✅ Enhanced dual-channel retrieval completed: "
                                  f"top1={fused_candidates[0]['id']} (score={top1_score:.4f}), "
                                  f"top2_score={top2_score:.4f}, raw_margin={top1_score - top2_score:.4f}")
                        print(f"🔧 Final candidates prepared: {len(fused_candidates)} with has_detail={has_detail_data}")

                        return fused_candidates
                        
                    except Exception as e:
                        print(f"⚠️ Enhanced dual-channel retrieval failed: {e}")
                        return []
                
                def _retrieve_from_structure_map(self, caption, scene_filter, top_k):
                    """从structure map文件中检索（结构通道）"""
                    try:
                        # 根据场景选择文件
                        if scene_filter == "SCENE_A_MS":
                            textmap_file = os.path.join(DATA_DIR, "Sense_A_Finetuned.fixed.jsonl")
                        elif scene_filter == "SCENE_B_STUDIO":
                            textmap_file = os.path.join(DATA_DIR, "Sense_B_Finetuned.fixed.jsonl")
                        else:
                            print(f"⚠️ Unknown scene: {scene_filter}")
                            return []
                        
                        print(f"🔍 Reading structure map from: {textmap_file}")
                        
                        # 读取textmap文件
                        # 🔧 FIX P1-4: 原 fallback "只读第一行" 是个 latent bug
                        # （如果未来文件变成真正的多行 JSONL，会静默丢失 99% 数据）。
                        # 现在结构文件就是单行 JSON，json.load 走得通；
                        # 如果格式坏了直接报错让人修文件，不再静默读半个。
                        textmap_data = None
                        try:
                            with open(textmap_file, 'r', encoding='utf-8') as f:
                                textmap_data = json.load(f)
                                print(f"🔍 成功读取结构文件: {textmap_file}")
                        except json.JSONDecodeError as e:
                            print(f"❌ 结构文件 JSON 解析失败: {textmap_file}: {e}")
                            print(f"   提示：本函数期望文件是单个 JSON object（含 input.topology.nodes/edges）")
                            return []
                        except Exception as e:
                            print(f"❌ 无法读取结构文件: {e}")
                            return []
                        
                        if not textmap_data:
                            print(f"⚠️ No data found in {textmap_file}")
                            return []
                        
                        # 🔧 FIX: 正确处理Sense_B的节点格式
                        # 提取节点信息 - 检查input.topology和顶级topology
                        nodes = []
                        if "input" in textmap_data and "topology" in textmap_data["input"]:
                            nodes = textmap_data["input"]["topology"].get("nodes", [])
                            print(f"🔍 从input.topology中读取节点")
                        elif "topology" in textmap_data:
                            nodes = textmap_data["topology"].get("nodes", [])
                            print(f"🔍 从顶级topology中读取节点")
                        
                        if not nodes:
                            print(f"⚠️ No nodes found in {textmap_file}")
                            return []
                        
                        print(f"🔍 Found {len(nodes)} nodes in structure map (structure channel)")
                        
                        # 🔧 FIX: 处理不同的节点格式
                        # Sense_A: [{"id": "poi01", "name": "..."}, ...]
                        # Sense_B: ["poi11", "poi12", ...]
                        processed_nodes = []
                        if nodes and isinstance(nodes[0], str):
                            # Sense_B格式：字符串数组，需要转换为对象格式
                            print(f"🔧 检测到Sense_B格式，转换节点为对象格式")
                            for node_id in nodes:
                                # 从pois中获取节点信息
                                pois = textmap_data.get("input", {}).get("pois", {})
                                if node_id in pois:
                                    node_info = pois[node_id]
                                    processed_nodes.append({
                                        "id": node_id,
                                        "name": node_info.get("name", ""),
                                        "retrieval": textmap_data.get("input", {}).get("retrieval", {}),
                                        "landmarks": [],
                                        "categories": []
                                    })
                                else:
                                    # 如果没有pois信息，创建基本节点
                                    processed_nodes.append({
                                        "id": node_id,
                                        "name": node_id,
                                        "retrieval": textmap_data.get("input", {}).get("retrieval", {}),
                                        "landmarks": [],
                                        "categories": []
                                    })
                        else:
                            # Sense_A格式：已经是对象数组
                            processed_nodes = nodes
                        
                        # 计算每个节点的相似度分数
                        candidates = []
                        caption_lower = caption.lower()
                        
                        for node in processed_nodes:
                            node_id = node.get("id", "")
                            if not node_id:
                                continue
                            
                            # 计算检索分数
                            score = self._calculate_node_score(node, caption_lower)
                            
                            candidates.append({
                                "id": node_id,
                                "score": score,
                                "text": node.get("name", ""),
                                "score_nl": score,
                                "score_struct": score,
                                "provider": "ft",
                                "bonus_keywords": 0.0,
                                "bonus_bearing": 0.0,
                                "alpha_used": 0.8,
                                "retrieval_method": "structure_channel"
                            })
                        
                        # 语义去重：合并语义相似的节点
                        deduplicated_candidates = self._semantic_deduplication(candidates, caption_lower)
                        
                        # 返回top_k个候选
                        deduplicated_candidates.sort(key=lambda x: x["score"], reverse=True)
                        return deduplicated_candidates[:top_k]
                        
                    except Exception as e:
                        print(f"⚠️ Failed to read structure map: {e}")
                        return []
                
                def _retrieve_from_detail_map(self, caption, scene_filter, top_k):
                    """从detail map文件中检索（细节通道）"""
                    try:
                        # 根据场景选择文件
                        if scene_filter == "SCENE_A_MS":
                            detail_file = os.path.join(DATA_DIR, "Sense_A_MS.jsonl")
                        elif scene_filter == "SCENE_B_STUDIO":
                            detail_file = os.path.join(DATA_DIR, "Sense_B_Studio.jsonl")
                        else:
                            print(f"⚠️ Unknown scene: {scene_filter}")
                            return []
                        
                        # 读取detail文件
                        if not os.path.exists(detail_file):
                            print(f"⚠️ Detail file not found: {detail_file}")
                            return []
                        
                        print(f"🔍 Reading detail data from: {detail_file}")
                        
                        # 解析JSONL格式
                        detail_candidates = []
                        caption_lower = caption.lower()
                        
                        with open(detail_file, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                if line.strip():
                                    try:
                                        detail_item = json.loads(line)
                                        node_id = detail_item.get("node_hint", "")
                                        
                                        if not node_id:
                                            print(f"⚠️ Line {line_num}: Missing node_hint")
                                            continue
                                        
                                        # 计算detail分数
                                        score = self._calculate_detail_score(detail_item, caption_lower)
                                        
                                        detail_candidates.append({
                                            "id": node_id,
                                            "score": score,
                                            "text": detail_item.get("nl_text", ""),
                                            "score_nl": score,
                                            "score_detail": score,
                                            "provider": "ft",
                                            "retrieval_method": "detail_channel"
                                        })
                                        
                                    except json.JSONDecodeError as e:
                                        print(f"⚠️ Line {line_num}: JSON decode error: {e}")
                                        continue
                        
                        print(f"🔍 Successfully loaded {len(detail_candidates)} detail candidates")
                        
                        # 按分数排序并返回top_k
                        detail_candidates.sort(key=lambda x: x["score"], reverse=True)
                        return detail_candidates[:top_k]
                        
                    except Exception as e:
                        print(f"⚠️ Failed to read detail map: {e}")
                        return []
                
                # 🔧 Removed an earlier (dead) copy of `_calculate_detail_score`
                # defined here. Python kept the later override at the bottom of this
                # class as the live one — see definition further below.

                def _calculate_node_score(self, node, caption_lower):
                    """计算节点的检索分数（结构通道）- 增强版"""
                    score = 0.0
                    
                    # 🔧 FIX: 改进语义匹配，避免过于宽泛的匹配
                    # 1. 基于检索词的分数（更严格的匹配）
                    retrieval = node.get("retrieval", {})
                    index_terms = retrieval.get("index_terms", [])
                    tags = retrieval.get("tags", [])
                    
                    # 关键词匹配（更严格的权重分配）
                    for term in index_terms + tags:
                        term_lower = term.lower()
                        if term_lower in caption_lower:
                            # 空间概念给予更高权重
                            if any(space_word in term_lower for space_word in ["open", "space", "area", "large", "atrium"]):
                                score += 0.4  # 空间概念权重
                            elif "box" in term_lower or "boxes" in term_lower:
                                # 🔧 FIX: 降低box相关词的权重，避免过度匹配
                                score += 0.15  # 从0.3降低到0.15
                            else:
                                score += 0.3
                        elif any(word in caption_lower for word in term_lower.split()):
                            if any(space_word in term_lower for space_word in ["open", "space", "area", "large", "atrium"]):
                                score += 0.2
                            elif "box" in term_lower or "boxes" in term_lower:
                                # 🔧 FIX: 降低box相关词的部分匹配权重
                                score += 0.08  # 从0.15降低到0.08
                            else:
                                score += 0.15
                    
                    # 2. 基于节点名称的分数（更精确的匹配）
                    node_name = node.get("name", "").lower()
                    if node_name:
                        # 检查空间概念关键词
                        space_keywords = ["open", "space", "area", "large", "atrium", "cluster"]
                        space_match = any(space_word in node_name for space_word in space_keywords)
                        
                        if space_match and any(word in caption_lower for word in ["open", "space", "large"]):
                            score += 0.3  # 空间概念匹配给予更高权重
                        elif any(word in caption_lower for word in node_name.split()):
                            # 🔧 FIX: 降低box相关节点的名称匹配权重
                            if "box" in node_name or "boxes" in node_name:
                                score += 0.1  # 从0.2降低到0.1
                            else:
                                score += 0.2
                    
                    # 3. 基于地标的分数
                    landmarks = node.get("landmarks", [])
                    for landmark in landmarks:
                        if isinstance(landmark, dict):
                            landmark_term = landmark.get("term", "").lower()
                            if landmark_term and any(word in caption_lower for word in landmark_term.split()):
                                score += 0.1
                        elif isinstance(landmark, str) and landmark.startswith("lm_"):
                            # 地标ID匹配
                            landmark_id = landmark.lower()
                            if any(word in caption_lower for word in landmark_id.split("_")):
                                score += 0.1
                    
                    # 4. 基于类别的分数
                    categories = node.get("categories", [])
                    for category in categories:
                        if category.lower() in caption_lower:
                            score += 0.1
                    
                    # 5. 新增：空间概念语义匹配（解决"large open space"问题）
                    # 检查caption中的空间概念是否与节点匹配
                    space_concepts = {
                        "large open space": ["open", "space", "large", "area", "atrium", "cluster"],
                        "open space": ["open", "space", "area", "atrium"],
                        "open area": ["open", "area", "space", "atrium"],
                        "atrium": ["atrium", "open", "space", "area"]
                    }
                    
                    for caption_concept, keywords in space_concepts.items():
                        if caption_concept in caption_lower:
                            # 检查节点是否包含相关空间概念
                            node_text = f"{node.get('name', '')} {' '.join(index_terms)} {' '.join(tags)}"
                            node_text_lower = node_text.lower()
                            
                            if any(keyword in node_text_lower for keyword in keywords):
                                score += 0.25  # 空间概念语义匹配给予额外权重
                                break
                    
                    # 🔧 FIX P1-3: 删除"上一次 top1 自动 ×0.8" 多样性惩罚补丁。
                    # 跟外层 ×0.7 补丁叠加会让稳定正确的预测被压到 0.56，反而触发 low_conf。
                    # 🔧 FIX P1-7: 去掉 min(1.0, score) 硬上限。让 raw score 累积反映真实匹配强度，
                    # 多个高分候选不再被压成 1.0 ties（之前会导致 margin=0 触发误判低置信）。
                    return score
                
                def _semantic_deduplication(self, candidates, caption_lower):
                    """语义去重：合并语义相似的节点，避免返回重复的TV screen等"""
                    if not candidates:
                        return candidates
                    
                    # 定义语义相似组 - 增强版，更精确的区分
                    semantic_groups = {
                        "tv_screen_group": [
                            "tv screen", "large tv screen", "large tv screen near entry",
                            "tv", "television", "display", "screen", "monitor"
                        ],
                        "window_group": [
                            "glass window", "window wall", "windows", "glass", "window"
                        ],
                        "sofa_group": [
                            "orange sofa", "sofa", "couch", "seating"
                        ],
                        "chair_group": [
                            "chair", "chair_on", "yline", "seating", "stool"
                        ],
                        "space_group": [
                            "open space", "large open space", "open area", "atrium", "space"
                        ],
                        "boxes_group": [
                            "boxes", "box", "cardboard", "stacked", "floor", "on floor"
                        ],
                        "desk_group": [
                            "desk", "desks", "workbench", "workstation", "computer"
                        ],
                        "table_group": [
                            "table", "surface", "counter", "small_table"
                        ],
                        "storage_group": [
                            "storage", "shelf", "cabinet", "drawer", "container"
                        ],
                        "wall_group": [
                            "wall", "drawer_wall", "component_wall", "partition"
                        ]
                    }
                    
                    # 新增：实体别名映射，识别同一实体的不同表示（修复节点ID不匹配）
                    entity_aliases = {
                        "poi01_entrance_glass_door": ["dp_ms_entrance", "entrance", "glass door"],
                        "poi02_green_trash_bin": ["yline_start", "trash bin", "green bin"],
                        "poi03_black_drawer_cabinet": ["yline_bend_mid", "drawer cabinet", "black cabinet"],
                        "poi04_wall_3d_printers": ["atrium_edge", "3d printers", "wall printers"],
                        "poi05_desk_3d_printer": ["tv_zone", "desk printer", "3d printer"],
                        "poi06_small_open_3d_printer": ["storage_corner", "small printer", "open printer"],
                        "poi07_cardboard_boxes": ["orange_sofa_corner", "cardboard boxes", "boxes"],
                        "poi08_to_atrium": ["desks_cluster", "atrium", "to atrium"],
                        "poi09_qr_bookshelf": ["chair_on_yline", "qr bookshelf", "bookshelf"],
                        "poi10_metal_display_cabinet": ["small_table_mid", "metal cabinet", "display cabinet"]
                    }
                    
                    # 按语义组分组候选
                    grouped_candidates = {}
                    for candidate in candidates:
                        candidate_id = candidate["id"].lower()
                        candidate_text = candidate.get("text", "").lower()
                        candidate_name = candidate.get("name", "").lower()
                        
                        # 新增：检查实体别名，识别同一实体（修复映射逻辑）
                        entity_group = None
                        for canonical_name, aliases in entity_aliases.items():
                            # 检查候选ID是否匹配规范名称
                            if candidate_id.lower() == canonical_name.lower():
                                # 找到匹配，返回对应的细节数据ID
                                entity_group = aliases[0]  # 使用第一个别名作为细节数据ID
                                print(f"🔍 Entity alias detected: {candidate_id} → {entity_group}")
                                break
                        
                        # 检查属于哪个语义组
                        assigned_group = None
                        best_match_score = 0
                        
                        for group_name, keywords in semantic_groups.items():
                            match_score = 0
                            for keyword in keywords:
                                # 检查候选的各个字段
                                if keyword in candidate_id:
                                    match_score += 2  # ID匹配给予最高权重
                                if keyword in candidate_text:
                                    match_score += 1.5  # 文本匹配给予高权重
                                if keyword in candidate_name:
                                    match_score += 1.0  # 名称匹配给予中等权重
                            
                            # 选择匹配度最高的组
                            if match_score > best_match_score:
                                best_match_score = match_score
                                assigned_group = group_name
                        
                        # 如果匹配度太低，则不分组
                        if best_match_score < 1.0:
                            assigned_group = None
                        
                        # 优先使用实体别名分组，如果没有则使用语义分组
                        final_group = entity_group if entity_group else assigned_group
                        
                        if final_group:
                            if final_group not in grouped_candidates:
                                grouped_candidates[final_group] = []
                            grouped_candidates[final_group].append(candidate)
                        else:
                            # 不属于任何组的候选，单独处理
                            if "other" not in grouped_candidates:
                                grouped_candidates["other"] = []
                            grouped_candidates["other"].append(candidate)
                    
                    # 对每个语义组，选择最高分的候选
                    deduplicated = []
                    for group_name, group_candidates in grouped_candidates.items():
                        if group_name == "other":
                            # 其他候选直接添加
                            deduplicated.extend(group_candidates)
                        else:
                            # 语义组选择最高分的
                            if len(group_candidates) > 1:
                                print(f"🔍 Semantic deduplication: {group_name} has {len(group_candidates)} candidates")
                                for i, cand in enumerate(group_candidates):
                                    print(f"   {i+1}. {cand['id']} (score: {cand['score']:.3f})")
                            
                            # 选择最高分的候选
                            best_candidate = max(group_candidates, key=lambda x: x["score"])
                            best_candidate["semantic_group"] = group_name
                            best_candidate["merged_candidates"] = len(group_candidates)
                            deduplicated.append(best_candidate)
                    
                    print(f"🔍 Semantic deduplication: {len(candidates)} → {len(deduplicated)} candidates")
                    return deduplicated
                
                def _calculate_detail_score(self, detail_item, caption_lower):
                    """计算detail分数（细节通道）- 增强版"""
                    score = 0.0
                    
                    # 1. 基于自然语言描述的分数（增强空间概念权重）
                    nl_text = detail_item.get("nl_text", "").lower()
                    if nl_text:
                        # 关键词匹配
                        keywords = nl_text.split()
                        for keyword in keywords:
                            if keyword in caption_lower:
                                # 空间概念给予更高权重
                                if any(space_word in keyword for space_word in ["open", "space", "area", "large", "atrium", "cluster"]):
                                    score += 0.3  # 空间概念权重从0.2提升到0.3
                                else:
                                    score += 0.2
                            elif len(keyword) > 3 and any(word in caption_lower for word in keyword.split()):
                                if any(space_word in keyword for space_word in ["open", "space", "area", "large", "atrium", "cluster"]):
                                    score += 0.15  # 空间概念权重从0.1提升到0.15
                                else:
                                    score += 0.1
                    
                    # 2. 基于结构化文本的分数
                    struct_text = detail_item.get("struct_text", "").lower()
                    if struct_text:
                        # 解析结构化特征
                        struct_features = struct_text.split(";")
                        for feature in struct_features:
                            if feature.strip() and any(word in caption_lower for word in feature.split()):
                                score += 0.15
                    
                    # 3. 基于空间关系的分数
                    spatial_info = detail_item.get("spatial_info", {})
                    for relation, landmark in spatial_info.items():
                        if landmark and any(word in caption_lower for word in str(landmark).split()):
                            score += 0.1
                    
                    # 4. 新增：空间概念语义匹配（与结构通道保持一致）
                    space_concepts = {
                        "large open space": ["open", "space", "large", "area", "atrium", "cluster"],
                        "open space": ["open", "space", "area", "atrium"],
                        "open area": ["open", "area", "space", "atrium"],
                        "atrium": ["atrium", "open", "space", "area"]
                    }
                    
                    for caption_concept, keywords in space_concepts.items():
                        if caption_concept in caption_lower:
                            # 检查detail文本是否包含相关空间概念
                            detail_text = f"{nl_text} {struct_text}"
                            if any(keyword in detail_text for keyword in keywords):
                                score += 0.2  # 空间概念语义匹配给予额外权重
                                break

                    # 🔧 FIX P1-7: 去掉 min(1.0, score) 上限
                    # ⚠️ NOTE: 本函数与 2429 行的 _calculate_detail_score 重复定义，
                    # Python 会以本（后定义）版本为准。重构去重留给 Stage 3。
                    return score
            
            UNIFIED_RETRIEVER = EnhancedDualChannelRetriever()
            
            # 修复：确保detail_index已构建
            if not hasattr(UNIFIED_RETRIEVER, 'detail_index'):
                print("🔧 构建detail_index...")
                UNIFIED_RETRIEVER.detail_index = UNIFIED_RETRIEVER._build_detail_index()
            
            print("✅ Calibrated dual-channel retriever initialized successfully")
            return UNIFIED_RETRIEVER
            
        except Exception as e:
            print(f"⚠️  Failed to load unified retriever: {e}")
            print("⚠️  Falling back to legacy retrieval")
            return None
    return UNIFIED_RETRIEVER

# Legacy scene loading (fallback)
def load_scene_index(scene_id: str):
    """Legacy function - kept for backward compatibility"""
    npz = np.load(os.path.join(MODEL_DIR, f"{scene_id}.npz"), allow_pickle=True)
    X = npz["X"].astype(np.float32)
    texts = npz["texts"].tolist()
    ids = json.loads(open(os.path.join(MODEL_DIR, f"{scene_id}.ids.json"), "r", encoding="utf-8").read())
    if USE_FAISS:
        index = faiss.read_index(os.path.join(MODEL_DIR, f"{scene_id}.faiss"))
        return {"index": index, "X": X, "texts": texts, "ids": ids}
    else:
        nn = NearestNeighbors(n_neighbors=5, metric="cosine").fit(X)
        return {"index": nn, "X": X, "texts": texts, "ids": ids}

# Legacy scene loading (fallback)
SCENE = {
    "SCENE_A_MS": load_scene_index("SCENE_A_MS"),
    "SCENE_B_STUDIO": load_scene_index("SCENE_B_STUDIO"),
}

# ---------- BLIP caption (Local Model) ----------
# Initialize local BLIP model
try:
    processor = BlipProcessor.from_pretrained(BLIP_MODEL_PATH)
    model = BlipForConditionalGeneration.from_pretrained(BLIP_MODEL_PATH)
    print(f"✓ Loaded local BLIP model successfully: {BLIP_MODEL_PATH}")
    print(f"✓ Using device: {BLIP_DEVICE}")
except Exception as e:
    print(f"⚠ Failed to load local BLIP model: {e}")
    print("⚠ Image captioning will be disabled")
    processor = None
    model = None

def hf_caption(image_bytes: bytes) -> str:
    if processor is None or model is None:
        return "an indoor workspace with desks and shelves"
    
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        print(f"⚠ Error in local BLIP captioning: {e}")
        return "an indoor workspace with desks and shelves"


# ---------- ASR (faster-whisper) ----------
from faster_whisper import WhisperModel

# Set environment variables to handle Hugging Face Hub issues
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_OFFLINE"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Avoid deadlock warnings

# Initialize ASR model with proper error handling
ASR = None
try:
    # Try to load from local cache first
    ASR = WhisperModel("small", device="cpu", compute_type="int8", local_files_only=True)
    print("✓ Loaded faster-whisper model from local cache")
except Exception as e:
    print(f"⚠ Local cache not found: {e}")
    try:
        # Try to download with explicit settings
        print("Attempting to download faster-whisper model...")
        ASR = WhisperModel("small", device="cpu", compute_type="int8")
        print("✓ Successfully downloaded and loaded faster-whisper model")
    except Exception as download_error:
        print(f"Failed to download 'small' model: {download_error}")
        try:
            # Try a different model that might be more accessible
            print("Trying alternative model 'tiny'...")
            ASR = WhisperModel("tiny", device="cpu", compute_type="int8")
            print("✓ Successfully loaded 'tiny' model as fallback")
        except Exception as alt_error:
            print(f"Failed to download alternative model: {alt_error}")
            print("ASR functionality will be disabled. Please check your internet connection or Hugging Face credentials.")
            print("Alternative: Try using a different model or check if you have Hugging Face credentials set up.")
            # Create a dummy ASR object to prevent crashes
            class DummyASR:
                def transcribe(self, *args, **kwargs):
                    raise Exception("ASR model not available - download failed")
            ASR = DummyASR()

def webm_to_wav_16k_mono(data: bytes) -> bytes:
    """Convert WebM audio to WAV format with better error handling"""
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as fin, tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fout:
            fin.write(data)
            fin.flush()
            
            # Use more robust ffmpeg command with better error handling
            cmd = [
                "ffmpeg",
                "-loglevel", "warning",  # Show warnings for debugging
                "-y",  # Overwrite output file
                "-i", fin.name,
                "-ac", "1",  # Mono
                "-ar", "16000",  # 16kHz sample rate
                "-f", "wav",  # Force WAV format
                fout.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                print(f"FFmpeg stdout: {result.stdout}")
                raise Exception(f"FFmpeg failed with return code {result.returncode}")
            
            # Read the converted file
            with open(fout.name, 'rb') as f:
                wav_data = f.read()
            
            # Clean up temporary files
            os.unlink(fin.name)
            os.unlink(fout.name)
            
            return wav_data
            
    except Exception as e:
        print(f"Audio conversion error: {e}")
        # Clean up any remaining temp files
        try:
            if 'fin' in locals(): os.unlink(fin.name)
            if 'fout' in locals(): os.unlink(fout.name)
        except:
            pass
        raise e

def asr_bytes_to_text(data: bytes) -> str:
    """Convert audio bytes to text with improved error handling"""
    if not data or len(data) == 0:
        print("Empty audio data received")
        return ""
    
    print(f"Processing audio: {len(data)} bytes")
    
    # Check if it's already WAV format
    buf = data
    if not (len(buf) > 12 and buf[:4] == b"RIFF" and b"WAVE" in buf[:12]):
        print("Converting WebM to WAV...")
        try:
            buf = webm_to_wav_16k_mono(data)
            print(f"Conversion successful: {len(buf)} bytes WAV")
        except Exception as e:
            print(f"WebM to WAV conversion failed: {e}")
            # Try to use original data as fallback
            buf = data
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(buf)
            f.flush()
            
            print(f"Transcribing audio file: {f.name}")
            segments, info = ASR.transcribe(f.name, beam_size=1, vad_filter=True)
            text = "".join([s.text for s in segments]).strip()
            
            # Clean up temp file
            os.unlink(f.name)
            
            print(f"Transcription result: '{text}'")
            return text
            
    except Exception as e:
        print(f"ASR transcription error: {e}")
        # Clean up temp file
        try:
            if 'f' in locals(): os.unlink(f.name)
        except:
            pass
        raise e

# ---------- OpenAI client (used by /api/qa) ----------
from openai import OpenAI
OAI = OpenAI(api_key=LLM_KEY)

# ---------- FastAPI ----------
app = FastAPI(title="VLN4VI Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "asr_model": "loaded" if ASR else "not_loaded",
            "blip_model": "loaded" if processor else "not_loaded",
            "enhanced_dual_channel_retriever": "available" if get_unified_retriever() else "not_available"
        }
    }

# TTS start endpoint for end-to-end latency tracking
class TTSMark(BaseModel):
    req_id: str
    session_id: str
    site_id: str
    provider: str  # ✅ 新增 provider 字段
    client_start_ms: int
    client_tts_start_ms: int

@app.post("/api/metrics/tts_start")
def api_tts_start(mark: TTSMark):
    """Record TTS start for end-to-end latency calculation"""
    paths = _log_paths(mark.provider)
    _ensure_headers(paths)
    
    e2e = int(mark.client_tts_start_ms) - int(mark.client_start_ms)
    
    # ✅ Only write when logging is enabled
    enabled, run_id = _is_logging(mark.session_id, mark.provider)
    if enabled:
        with open(paths["latency"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                mark.site_id, run_id, datetime.utcnow().isoformat(),
                mark.req_id, mark.session_id, mark.provider,
                "trial",  # phase: trial phase for subsequent photos
                mark.client_start_ms, mark.client_tts_start_ms, e2e
            ])
    
    print(f"📊 TTS start recorded: req_id={mark.req_id}, e2e={e2e}ms, logging={enabled}")
    return {"ok": True, "e2e_latency_ms": e2e}

# ✅ New: Logging control API endpoints
class LogSwitchIn(BaseModel):
    session_id: str
    provider: str = "ft"
    enabled: bool
    run_id: str = ""     # Optional, keep previous if not provided

@app.post("/api/logging/set")
def api_logging_set(body: LogSwitchIn):
    """Set logging record switch"""
    key = (body.session_id, body.provider.lower())
    cur = LOG_SWITCH[key]
    cur["enabled"] = bool(body.enabled)
    if body.run_id:
        cur["run_id"] = body.run_id
    
    status = "ON" if cur["enabled"] else "OFF"
    run_id_info = f" (run_id: {cur['run_id']})" if cur["run_id"] else ""
    print(f"🔧 Logging {status} for session={body.session_id}, provider={body.provider}{run_id_info}")
    
    return {"ok": True, "state": cur, "key": {"session_id": body.session_id, "provider": body.provider.lower()}}

@app.get("/api/logging/status")
def api_logging_status(session_id: str, provider: str = "ft"):
    """Query logging record status"""
    st = LOG_SWITCH[(session_id, provider.lower())]
    return {"ok": True, "state": st}

# ✅ 新增：RQ3 澄清对话管理端点
class ClarificationRound(BaseModel):
    clarification_id: str
    session_id: str
    site_id: str
    round_count: int
    user_question: str
    system_answer: str
    predicted_node: str
    gt_node_id: str = None

@app.post("/api/metrics/clarification_round")
def api_clarification_round(round_data: ClarificationRound):
    """Record a clarification dialogue round"""
    record_clarification_round(
        round_data.clarification_id,
        round_data.session_id,
        round_data.site_id,
        round_data.round_count,
        round_data.user_question,
        round_data.system_answer,
        round_data.predicted_node,
        round_data.gt_node_id
    )
    
    print(f"🔍 Clarification round recorded: {round_data.clarification_id}, round {round_data.round_count}")
    return {"ok": True, "round_recorded": round_data.round_count}

class ClarificationEnd(BaseModel):
    clarification_id: str
    session_id: str
    site_id: str
    total_rounds: int
    final_predicted_node: str
    gt_node_id: str

@app.post("/api/metrics/clarification_end")
def api_clarification_end(end_data: ClarificationEnd):
    """End a clarification session and record success rate"""
    end_clarification_session(
        end_data.clarification_id,
        end_data.session_id,
        end_data.site_id,
        end_data.total_rounds,
        end_data.final_predicted_node,
        end_data.gt_node_id
    )
    
    return {"ok": True, "session_ended": end_data.clarification_id}

# ✅ 新增：RQ3 错误恢复管理端点
class ErrorRecoveryStart(BaseModel):
    session_id: str
    site_id: str
    error_node: str
    correct_node: str

@app.post("/api/metrics/error_recovery_start")
def api_error_recovery_start(recovery_data: ErrorRecoveryStart):
    """Start error recovery timing"""
    recovery_id = start_error_recovery(
        recovery_data.session_id,
        recovery_data.site_id,
        recovery_data.error_node,
        recovery_data.correct_node
    )
    
    return {"ok": True, "recovery_id": recovery_id}

class ErrorRecoveryEnd(BaseModel):
    recovery_id: str
    session_id: str
    site_id: str
    correct_node: str
    recovery_path: str = ""

@app.post("/api/metrics/error_recovery_end")
def api_error_recovery_end(recovery_data: ErrorRecoveryEnd):
    """End error recovery timing and calculate duration"""
    duration = end_error_recovery(
        recovery_data.recovery_id,
        recovery_data.session_id,
        recovery_data.site_id,
        recovery_data.correct_node,
        recovery_data.recovery_path
    )
    
    return {"ok": True, "recovery_duration_ms": duration}

class StartIn(BaseModel):
    session_id: str
    site_id: str               # SCENE_A_MS / SCENE_B_STUDIO
    opening_provider: str      # base / ft
    lang: str = "en"           # en / zh

@app.post("/api/start")
def api_start(body: StartIn):
    # ✅ New: Enhanced session initialization with location tracking
    SESSIONS[body.session_id] = {
        "site_id": body.site_id, 
        "opening_provider": body.opening_provider, 
        "lang": body.lang,
        "current_location": None,           # 当前预测位置
        "location_history": [],             # 位置历史记录
        "orientation_history": [],          # 朝向历史记录
        "confidence_history": [],           # 置信度历史记录
        "last_update_time": datetime.utcnow().isoformat(),  # 最后更新时间
        "photo_count": 0                   # 拍照计数
    }
    
    # Initialize photo count tracking
    session_key = f"{body.session_id}_{body.opening_provider}_{body.site_id}"
    if "_photo_count" not in SESSIONS:
        SESSIONS["_photo_count"] = {}
    SESSIONS["_photo_count"][session_key] = 0
    
    table = HARD_OUTPUTS_EN if body.lang=="en" else HARD_OUTPUTS_ZH
    say = table[body.site_id][body.opening_provider]
    return {"mode":"orient","say":[say],"site_id":body.site_id,"opening_provider":body.opening_provider,"lang":body.lang}

@app.post("/api/locate")
async def api_locate(
    site_id: str = Form(...),
    image: UploadFile = File(...),
    session_id: str = Form("T1"),      # Allow session_id, default T1
    provider: str = Form("ft"),        # Frontend can pass (or get from session)
    gt_node_id: str = Form(None),      # ✅ New: ground truth label (optional)
    client_start_ms: int = Form(None), # ✅ New: client start timestamp
    req_id: str = Form(None),          # ✅ New: request ID for tracking
    first_photo: bool = Form(False)    # ✅ New: whether this is the first photo
):
    # Generate request ID if not provided
    req_id = req_id or str(uuid.uuid4())
    server_recv_ms = _now_ms()
    
    print(f"🔍 API locate called: site_id={site_id}, provider={provider}, first_photo={first_photo}, session_id={session_id}")
    
    # 🔧 FIX: 把原来重复的两段 70 行 warmup 分支合并成一条。
    # 触发条件 = 客户端显式 first_photo=True，或者会话对该 provider+site 还未拍过任何照片。
    # 之前第二个分支在 CSV 行里多写了 2 个空列，导致 low_conf_rule 之后的 timing 列错位 — 一并修掉。
    session_key = f"{session_id}_{provider}_{site_id}"
    if "_photo_count" not in SESSIONS:
        SESSIONS["_photo_count"] = {}
    SESSIONS["_photo_count"].setdefault(session_key, 0)

    is_warmup = first_photo or SESSIONS["_photo_count"][session_key] == 0
    if is_warmup:
        reason = "first_photo flag" if first_photo else f"photo_count==0 for {session_key}"
        print(f"📸 Warmup path ({reason})")
        SESSIONS["_photo_count"][session_key] = 1

        # BLIP caption only for logging — the response uses the preset output.
        try:
            img = await image.read()
            cap = hf_caption(img)
            print(f"📸 BLIP caption for first photo (logging only): {cap[:100]}...")
            preset_output = get_preset_output(provider, site_id)
            print(f"📚 First photo preset output for {provider}_{site_id}: {preset_output[:100]}...")
        except Exception as e:
            print(f"⚠️ Failed to get preset output, using fallback: {e}")
            preset_output = f"Welcome to {site_id}! Please take a photo to start exploring."
            print(f"📚 Fallback preset output: {preset_output}")

        # Always log warmup row (regardless of /api/logging/set switch).
        paths = _log_paths(provider)
        _ensure_headers(paths)
        with open(paths["locate"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                site_id, "WARMUP", datetime.utcnow().isoformat(), req_id, session_id, provider,
                "warmup",  # phase
                "First photo - preset output",  # caption
                "", "", "", "", "",  # top1, top2, margin
                "", "", "", "",  # gt_node_id, hit_top1, hit_top2, hit_hop1
                "", "",  # low_conf, low_conf_rule
                client_start_ms or "", server_recv_ms, _now_ms()  # timing
            ])
        print(f"📝 Warmup phase logged for {provider}_{site_id}")

        # DG metrics for the warmup event (no-ops when collector/evaluator are disabled).
        try:
            if enhanced_metrics_collector:
                enhanced_metrics_collector.collect_real_time_data(
                    MetricType.USER_BEHAVIOR,
                    session_id,
                    {
                        "action": "first_photo",
                        "site_id": site_id,
                        "provider": provider,
                        "preset_output_used": True,
                        "photo_count": 1,
                    },
                    priority=DataPriority.HIGH,
                    tags=["navigation", "first_photo", "preset_output"],
                )
            if dg_evaluator:
                dg_evaluator.dg1_evaluator.record_setup_process(
                    session_id=session_id,
                    steps=["photo_capture", "preset_output_display"],
                    time_taken=0,
                    success=True,
                )
        except Exception as e:
            print(f"⚠️ Failed to collect DG metrics for first photo: {e}")

        return {
            "req_id": req_id,
            "caption": cap if 'cap' in locals() else "First photo - preset output",
            "node_id": None,
            "confidence": 1.0,
            "low_conf": False,
            "preset_output": preset_output,
            "is_first_photo": True,
            "retrieval_method": "preset_output",
        }
    
    # 1) Get image → BLIP generate caption (for subsequent photos)
    try:
        img = await image.read()
        cap = hf_caption(img)
    except Exception as e:
        # Log failure
        # paths is already initialized above
        
        # ✅ Only write when logging is enabled
        enabled, run_id = _is_logging(session_id, provider)
        if enabled:
            with open(paths["locate"], "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    site_id, run_id, datetime.utcnow().isoformat(), req_id, session_id, provider,
                    f"BLIP_FAILED:{e}", "", "", "", "", "", gt_node_id or "", "", "", "",
                    True, f"BLIP_failed:{e}", client_start_ms or "", server_recv_ms, _now_ms()
                ])
        raise HTTPException(status_code=400, detail=f"BLIP failed: {e}")
    
    # 🔧 Increment photo count for this session. Keep a local `photo_count` for
    # downstream metrics/DG-evaluator calls (deleting the duplicate warmup branch
    # in the previous cleanup dropped the local-variable assignment downstream
    # references relied on — pyflakes flagged it).
    SESSIONS["_photo_count"][session_key] += 1
    photo_count = SESSIONS["_photo_count"][session_key]
    print(f"📸 Photo #{photo_count} for session {session_key}")

    # Initialize paths early (used by both SigLIP and legacy paths for CSV logging)
    paths = _log_paths(provider)
    _ensure_headers(paths)

    # 🆕 SigLIP short-circuit (ENABLE_SIGLIP=true and retriever loaded).
    # Single forward pass: image→cosine vs clean-textmap embeddings.
    # 73.0% useful-top1 on the labeled benchmark vs ~50% for the legacy
    # BLIP+fusion pipeline. See backend/siglip_retriever.py.
    if siglip_retriever is not None:
        try:
            print(f"🆕 SigLIP retrieval path for {site_id}")
            siglip_results = siglip_retriever.predict(img, top_k=5, site_id=site_id)

            # 🆕 Topology prior: if we have a previous location for this session,
            # boost candidates that are in the same topology cell (+SAME) or a
            # 1-hop neighbour (+NEIGHBOR). Re-rank by boosted cosine, recompute
            # confidence/margin. No-op when there's no prev location or the
            # mapping is unavailable.
            prev_loc = SESSIONS.get(session_id, {}).get("current_location")
            prior_used = False
            if prev_loc and _STRUCT_TO_TOPO:
                prev_topo = _STRUCT_TO_TOPO.get(prev_loc)
                if prev_topo:
                    prev_neighbors = _TOPO_ADJ.get(prev_topo, set())
                    import math as _math
                    for c in siglip_results:
                        c_topo = _STRUCT_TO_TOPO.get(c["node_id"])
                        boost = 0.0
                        if c_topo == prev_topo:
                            boost = TOPOLOGY_PRIOR_SAME_BOOST
                        elif c_topo and c_topo in prev_neighbors:
                            boost = TOPOLOGY_PRIOR_NEIGHBOR_BOOST
                        c["score_raw"] = c["score"]
                        c["score"] = c["score"] + boost
                        c["topo_boost"] = boost
                        # Recompute confidence using the boosted cosine via the
                        # same sigmoid mapping siglip_retriever uses
                        c["confidence"] = max(0.0, min(1.0,
                            1.0 / (1.0 + _math.exp(-12.0 * (c["score"] - 0.15)))))
                    # Re-sort by boosted score; rank field reflects new order
                    siglip_results.sort(key=lambda x: -x["score"])
                    for r, c in enumerate(siglip_results):
                        c["rank"] = r
                    prior_used = True
                    print(f"🔧 Topology prior: prev={prev_loc} (cell {prev_topo}) → "
                          f"re-ranked. new top1={siglip_results[0]['node_id']}")

            top1 = siglip_results[0]
            top2 = siglip_results[1] if len(siglip_results) > 1 else {"confidence": 0.0, "score": 0.0}
            top1_id = top1["node_id"]
            confidence = top1["confidence"]
            margin = max(0.0, top1["confidence"] - top2["confidence"])
            low_conf = (confidence < LOWCONF_SCORE_TH) or (margin < LOWCONF_MARGIN_TH)

            # Bearing — best-effort from BLIP caption (kept for FE compatibility)
            t = cap.lower()
            bearing = ""
            if "left" in t:
                bearing = "left"
            elif "right" in t:
                bearing = "right"
            elif "behind" in t or "back" in t:
                bearing = "behind"

            # Language + navigation instruction (reuse existing helpers)
            detected_lang = detect_language_from_caption(cap, provider)
            matching_data = get_matching_data(provider, site_id) or {}
            navigation_response = generate_dynamic_navigation_response(
                site_id, top1_id, confidence, low_conf, matching_data, detected_lang, top1
            )

            # Session location update
            orientation_info = track_orientation(session_id, cap, top1_id)
            update_session_location(session_id, top1_id, confidence, orientation_info)

            # Log to CSV (warmup-style row plus the locate fields the rest of the
            # pipeline writes; we keep the schema consistent with the legacy path)
            enabled, run_id = _is_logging(session_id, provider)
            top2_id = top2.get("node_id", "")
            hit_top1 = "" if not gt_node_id else ("True" if top1_id == gt_node_id else "False")
            hit_top2 = "" if not gt_node_id else ("True" if top2_id == gt_node_id else "False")
            with open(paths["locate"], "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    site_id, run_id if enabled else "SIGLIP",
                    datetime.utcnow().isoformat(), req_id, session_id, provider,
                    "siglip", cap[:200],
                    top1_id, f"{confidence:.4f}", top2_id, f"{top2.get('confidence', 0.0):.4f}",
                    f"{margin:.4f}",
                    gt_node_id or "", hit_top1, hit_top2, "",
                    str(low_conf).lower(), "siglip_default",
                    client_start_ms or "", server_recv_ms, _now_ms()
                ])

            response = {
                "req_id": req_id,
                "caption": cap,
                "node_id": top1_id,
                "confidence": confidence,
                "low_conf": low_conf,
                "bearing": bearing,
                "margin": margin,
                "navigation_instruction": navigation_response,
                "current_location": get_location_description(top1_id, []),
                "next_action": get_next_action(top1_id, site_id, detected_lang),
                "candidates": [
                    {
                        "id": c["node_id"],
                        "score": c["score"],
                        "confidence": c["confidence"],
                        "rank": c["rank"],
                    }
                    for c in siglip_results
                ],
                "retrieval_method": "siglip_so400m_v1",
                "siglip_score_top1": top1["score"],
            }
            print(f"✅ SigLIP top1={top1_id} conf={confidence:.3f} margin={margin:.3f} low_conf={low_conf}")
            return response
        except Exception as _e:
            print(f"⚠️ SigLIP path failed: {_e} — falling through to legacy retrieval")

    # 2) Try unified dual-channel retrieval first (legacy fallback)
    
    retriever = get_unified_retriever()
    if retriever:
        try:
            # ✅ Layered Fusion: Structure for localization + Detail for conversation enhancement
            if provider.lower() == "ft":
                print(f"🏗️ FT mode detected for {site_id} - using Enhanced Dual-Channel Fusion mode")
                
                # Phase 1: Structure-only localization (Sense_A_Finetuned.fixed.jsonl or Sense_B_Finetuned.fixed.jsonl)
                matching_data = get_matching_data(provider, site_id)
                print(f"🔍 Using Structure data from {PRESET_OUTPUTS.get(f'{provider.lower()}_{site_id}')}")
                
                # Phase 2: Load Detail data for post-localization conversation enhancement
                # Detail files (Sense_A_MS.jsonl, Sense_B_Studio.jsonl) are NOT used for scoring
                detailed_data = get_detailed_matching_data(site_id)
                print(f"🔍 Detail数据加载结果: {len(detailed_data) if detailed_data else 0} 条记录")
                if detailed_data:
                    print(f"🔍 Loaded Detail data from Detail file for conversation enhancement")
                    # 验证前几个节点的detail数据
                    if site_id == "SCENE_A_MS":
                        test_nodes = ["chair_on_yline", "desks_cluster", "dp_ms_entrance"]
                    elif site_id == "SCENE_B_STUDIO":
                        test_nodes = ["dp_studio_entrance", "workstation_zone", "glass_cage_room"]
                    else:
                        test_nodes = []
                    
                    for node_id in test_nodes:
                        node_details = [item for item in detailed_data if item.get("node_hint") == node_id]
                        print(f"   {node_id}: {len(node_details)} 项detail数据")
                else:
                    print(f"⚠️ Detail数据加载失败！")
                
                # Use layered fusion retrieval: Structure-only scoring + Detail metadata attachment
                candidates = enhanced_ft_retrieval(cap, retriever, site_id, detailed_data, session_id=session_id)
            else:
                # Standard retrieval for other modes (base/4o)
                matching_data = get_matching_data(provider, site_id)
                if matching_data:
                    print(f"🔍 Using matching data from {PRESET_OUTPUTS.get(f'{provider.lower()}_{site_id}')}")
                
                # Use enhanced dual-channel retrieval with scene filtering
                try:
                    # 获取融合后的候选列表
                    # 🔧 FIX P0-3: 传入 session_id 使 retriever 能拿到上一帧位置（topology prior）
                    candidates = retriever.retrieve(cap, top_k=10, scene_filter=site_id, session_id=session_id)
                    
                    if not candidates:
                        print("❌ 无法获取候选列表")
                        candidates = None
                    else:
                        print(f"✅ 成功获取候选列表: {len(candidates)} 个候选")
                        
                except Exception as e:
                    print(f"⚠️ Enhanced dual-channel retrieval failed: {e}")
                    # 不回退，不改位置；只沿用上一帧（或置为低置信待澄清）
                    candidates = None
            
            if candidates:
                # 🔧 NEW: Apply softmax calibration and continuity boost for enhanced dual-channel confidence scoring
                print(f"🔧 Applying enhanced confidence calculation for {len(candidates)} candidates")
                
                # Phase 1: Softmax calibration
                # 🔧 FIX P0-1/P0-2: 传入 session_id/site_id，让函数能读真实上一帧位置和通道 top1 id
                calibrated_confidence, calibrated_margin, raw_top1_score, raw_top2_score = calculate_calibrated_confidence_and_margin(
                    candidates, top_k=5, session_id=session_id, site_id=site_id
                )
                
                # Phase 2: Extract basic candidate info
                top1 = candidates[0]
                top1_id = top1["id"]
                top1_score = float(top1["score"])
                
                # 修复：添加断言式日志，确保状态一致
                has_detail = top1.get("has_detail", False)
                print(f"🔧 [ASSERT] top1={top1_id}, s1={top1_score:.4f}, has_detail={has_detail}")
                
                # 验证状态一致性
                assert isinstance(top1_id, str) and isinstance(top1_score, float) and isinstance(has_detail, bool), \
                    f"状态类型错误: top1_id={type(top1_id)}, top1_score={type(top1_score)}, has_detail={type(has_detail)}"
                
                # Get top2 if available
                top2 = candidates[1] if len(candidates) > 1 else None
                top2_id = top2["id"] if top2 else ""
                top2_score = float(top2["score"]) if top2 else 0.0
                
                # 🔧 NEW: Apply continuity boost to calibrated confidence
                boost_amount, boost_reason = apply_continuity_boost(
                    calibrated_confidence, session_id, site_id, top1_id
                )
                
                # Use boosted calibrated confidence for final decision
                final_confidence = calibrated_confidence + boost_amount
                final_margin = calibrated_margin
                
                print(f"🔧 Final confidence calculation:")
                print(f"   Raw scores: top1={raw_top1_score:.4f}, top2={raw_top2_score:.4f}")
                print(f"   Calibrated: confidence={calibrated_confidence:.4f}, margin={calibrated_margin:.4f}")
                print(f"   Continuity boost: {boost_amount:.4f} ({boost_reason})")
                print(f"   Final: confidence={final_confidence:.4f}, margin={final_margin:.4f}")
                
                # Determine confidence level using configurable thresholds
                # 🔧 FIX: 使用新的阈值：confidence > 40% 且 margin > 5% 就不触发low_conf
                low_conf = final_confidence < LOWCONF_SCORE_TH or final_margin < LOWCONF_MARGIN_TH
                low_conf_rule = f"score<{LOWCONF_SCORE_TH*100:.0f}% OR margin<{LOWCONF_MARGIN_TH*100:.0f}%" if low_conf else f"confidence>{LOWCONF_SCORE_TH*100:.0f}% AND margin>{LOWCONF_MARGIN_TH*100:.0f}%"
                
                # Calculate hit metrics
                hit_top1 = (gt_node_id == top1_id) if gt_node_id else ""
                hit_top2 = (gt_node_id in [top1_id, top2_id]) if gt_node_id and top2_id else ""
                hit_hop1 = is_hop1(site_id, top1_id, gt_node_id) if gt_node_id else ""
                
                # ✅ New: RQ3 misbelief rate calculation with enhanced dual-channel fusion
                misbelief = 0
                clarification_triggered = False
                
                # Check for structure-detail consistency (enhanced dual-channel fusion mode)
                # 🔧 FIX P0-5: top1 是 dict，不能用 hasattr/getattr (永远失败)
                structure_detail_conflict = False
                structure_score = top1.get('structure_score')
                detail_score = top1.get('detail_score')
                if structure_score is not None and detail_score is not None and structure_score > 0:
                    # Detail score < 30% of structure score 视为冲突
                    if detail_score < structure_score * 0.3:
                        structure_detail_conflict = True
                        print(f"⚠️ Structure-detail conflict detected: structure={structure_score:.3f}, detail={detail_score:.3f}")
                
                if gt_node_id and top1_id != gt_node_id:
                    # If prediction is wrong, check if clarification dialogue is triggered
                    clarification_triggered = low_conf or structure_detail_conflict
                    misbelief = 1 if not clarification_triggered else 0
                
                # If clarification dialogue is triggered, start clarification session
                clarification_id = None
                if clarification_triggered and gt_node_id:
                    clarification_id = start_clarification_session(
                        session_id, site_id, req_id, top1_id, gt_node_id, provider
                    )
                    
                    # Add structure-detail conflict context to clarification
                    if structure_detail_conflict:
                        print(f"🔍 Triggering clarification due to structure-detail conflict")
                        # You can add specific clarification logic here
                
                # Extract bearing from caption
                bearing = "ahead"
                t = cap.lower()
                if "left" in t: bearing = "left"
                elif "right" in t: bearing = "right"
                elif "behind" in t or "back" in t: bearing = "behind"
                
                # ✅ New: Track orientation and update session location
                # 🔧 NEW: 只有在统一检索成功后才更新会话位置，保持连续性
                orientation_info = track_orientation(session_id, cap, top1_id)
                update_session_location(session_id, top1_id, final_confidence, orientation_info)
                print(f"🔧 会话位置已更新: {top1_id} (confidence: {final_confidence:.3f})")
                
                # ✅ Collect DG metrics for successful localization (guarded on collector).
                try:
                    if enhanced_metrics_collector:
                        enhanced_metrics_collector.collect_real_time_data(
                            MetricType.USER_BEHAVIOR,
                            session_id,
                            {
                                "action": "photo_localization",
                                "site_id": site_id,
                                "provider": provider,
                                "predicted_location": top1_id,
                                "confidence": final_confidence,
                                "low_conf": low_conf,
                                "photo_count": photo_count,
                                "gt_node_id": gt_node_id,
                                "hit_top1": hit_top1 == "True",
                                "margin": final_margin
                            },
                            priority=DataPriority.HIGH,
                            tags=["navigation", "localization", "photo_analysis"]
                        )

                    # Record DG3 evaluation (Useful Precision in Localization)
                    if dg_evaluator:
                        dg_evaluator.dg3_evaluator.record_interaction_behavior(
                            session_id=session_id,
                            photo_count=photo_count,
                            first_photo_success=(photo_count == 1),
                            adjustment_actions=["photo_capture", "location_prediction"]
                        )
                        
                        # Record trust score based on confidence
                        trust_score = int(final_confidence * 10)  # Convert 0-1 to 0-10
                        dg_evaluator.dg3_evaluator.record_trust_score(
                            session_id=session_id,
                            trust_score=trust_score,
                            context="photo_localization"
                        )
                    
                    # Record user needs validation data (guarded — validator not wired yet)
                    if user_needs_validator:
                        user_needs_validator.record_validation_data(
                            session_id,
                            UserNeed.N2_POSITIONING_ACCURACY,
                            "positioning_error",
                            1.0 if hit_top1 == "True" else 2.0  # Simplified error estimation
                        )
                        user_needs_validator.record_validation_data(
                            session_id,
                            UserNeed.N2_POSITIONING_ACCURACY,
                            "task_completion_rate",
                            1.0 if hit_top1 == "True" else 0.5
                        )
                    
                except Exception as e:
                    print(f"⚠️ Failed to collect DG metrics for localization: {e}")
                
                # ✅ Detect language from caption and provider
                detected_lang = detect_language_from_caption(cap, provider)
                
                # ✅ Generate dynamic navigation response based on hierarchical fusion results
                navigation_response = generate_dynamic_navigation_response(
                    site_id, top1_id, final_confidence, low_conf, matching_data, detected_lang, top1
                )
                
                # Format response with detailed scoring and navigation
                response = {
                    "req_id": req_id,
                    "caption": cap,
                    "node_id": top1_id,
                    "confidence": final_confidence,  # 🔧 Use calibrated + boosted confidence
                    "low_conf": low_conf,
                    "bearing": bearing,
                    "margin": final_margin,  # 🔧 Use calibrated margin
                    "clarification_id": clarification_id,  # ✅ New: clarification session ID
                    "navigation_instruction": navigation_response,  # ✅ New: dynamic navigation instruction
                    # 🔧 FIX: 之前误把 site_id 当 detail_items 传入，函数体内对 string
                    # 迭代触发 AttributeError 被 try/except 吞掉，每次都退回兜底字符串。
                    # 现在传 top1 候选自带的 detail_items，detail 富集才真正生效。
                    "current_location": get_location_description(top1_id, top1.get('detail_items', [])),
                    "next_action": get_next_action(top1_id, site_id, detected_lang),  # ✅ New: next action instruction
                    "candidates": [
                        {
                            "id": c["id"],
                            "score": float(c["score"]),  # ✅ Convert numpy types to Python native types
                            "s_nl": float(c["score_nl"]),
                            "s_struct": float(c["score_struct"]),
                            "provider": c["provider"],
                            "bonus_keywords": float(c["bonus_keywords"]),
                            "bonus_bearing": float(c["bonus_bearing"]),
                            "alpha_used": float(c["alpha_used"]),
                            "retrieval_method": c.get("retrieval_method", "unknown"),  # ✅ New: retrieval method info
                            "detailed_match_score": c.get("detailed_match_score", None)  # ✅ New: detailed matching score
                        }
                        for c in candidates[:10]
                    ],
                    "retrieval_method": "enhanced_ft_dual_retrieval" if provider.lower() == "ft" and site_id == "SCENE_A_MS" else "unified_dual_channel_fusion",
                    # 🔧 NEW: Add calibration and boost information
                    "calibration_info": {
                        "raw_scores": {"top1": raw_top1_score, "top2": raw_top2_score},
                        "calibrated": {"confidence": calibrated_confidence, "margin": calibrated_margin},
                        "continuity_boost": {"amount": boost_amount, "reason": boost_reason},
                        "final": {"confidence": final_confidence, "margin": final_margin}
                    }
                }
                
                # Write comprehensive log with RQ3 data
                server_resp_ms = _now_ms()
                
                # ✅ Only write when logging is enabled
                enabled, run_id = _is_logging(session_id, provider)
                if enabled:
                    # 🔧 NEW: Enhanced logging with similarity distribution analysis
                    top3_score = float(candidates[2]["score"]) if len(candidates) > 2 else 0.0
                    top4_score = float(candidates[3]["score"]) if len(candidates) > 3 else 0.0
                    top5_score = float(candidates[4]["score"]) if len(candidates) > 4 else 0.0
                    
                    # Calculate similarity distribution metrics
                    score_range = raw_top1_score - top5_score if len(candidates) > 4 else raw_top1_score - top2_score
                    score_variance = np.var([raw_top1_score, raw_top2_score, top3_score, top4_score, top5_score]) if len(candidates) > 4 else np.var([raw_top1_score, raw_top2_score])
                    
                    with open(paths["locate"], "a", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow([
                            site_id, run_id, datetime.utcnow().isoformat(), req_id, session_id, provider,
                            "trial",  # phase: trial phase for subsequent photos
                            cap,
                            top1_id, f"{final_confidence:.6f}",  # 🔧 Use final calibrated confidence
                            top2_id, f"{raw_top2_score:.6f}",
                            f"{final_margin:.6f}",  # 🔧 Use final calibrated margin
                            gt_node_id or "",
                            str(hit_top1).lower(), str(hit_top2).lower(), str(hit_hop1).lower(),
                            str(low_conf).lower(), low_conf_rule if low_conf else "",
                            client_start_ms or "", server_recv_ms, server_resp_ms
                        ])
                    
                    # 🔧 NEW: Log detailed similarity distribution for analysis
                    similarity_log_path = os.path.join(os.path.dirname(paths["locate"]), "similarity_distribution.csv")
                    similarity_headers = [
                        "site_id", "run_id", "ts_iso", "req_id", "session_id", "provider",
                        "raw_top1", "raw_top2", "raw_top3", "raw_top4", "raw_top5",
                        "calibrated_conf", "calibrated_margin", "boost_amount", "boost_reason",
                        "final_conf", "final_margin", "score_range", "score_variance",
                        "low_conf", "low_conf_rule", "gt_node_id", "hit_top1"
                    ]
                    
                    # Ensure similarity distribution log headers
                    if not os.path.exists(similarity_log_path):
                        with open(similarity_log_path, "w", newline="", encoding="utf-8") as f:
                            csv.writer(f).writerow(similarity_headers)
                    
                    # Log similarity distribution data
                    with open(similarity_log_path, "a", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow([
                            site_id, run_id, datetime.utcnow().isoformat(), req_id, session_id, provider,
                            f"{raw_top1_score:.6f}", f"{raw_top2_score:.6f}", f"{top3_score:.6f}", f"{top4_score:.6f}", f"{top5_score:.6f}",
                            f"{calibrated_confidence:.6f}", f"{calibrated_margin:.6f}", f"{boost_amount:.6f}", boost_reason,
                            f"{final_confidence:.6f}", f"{final_margin:.6f}", f"{score_range:.6f}", f"{score_variance:.6f}",
                            str(low_conf).lower(), low_conf_rule if low_conf else "", gt_node_id or "", str(hit_top1).lower()
                        ])
                    
                    print(f"📝 Trial phase logged to {paths['locate']} (run_id: {run_id})")
                    print(f"📊 Similarity distribution logged to {similarity_log_path}")
                    print(f"   Raw scores: [{raw_top1_score:.4f}, {raw_top2_score:.4f}, {top3_score:.4f}, {top4_score:.4f}, {top5_score:.4f}]")
                    print(f"   Score range: {score_range:.4f}, Variance: {score_variance:.4f}")
                else:
                    print(f"📝 Logging disabled for session={session_id}, provider={provider}")
                
                print(f"✓ Unified dual-channel retrieval successful for {site_id}")
                print(f"  Top candidate: {top1['text'][:50]}... (score: {final_confidence:.3f})")
                print(f"  Provider: {top1['provider']}, Alpha: {top1['alpha_used']:.2f}")
                print(f"  Margin: {final_margin:.3f}, Low conf: {low_conf}")
                if gt_node_id:
                    print(f"  Ground truth: {gt_node_id}")
                    print(f"  Hit Top1: {hit_top1}, Hit Top2: {hit_top2}, Hit ±1-Hop: {hit_hop1}")
                    print(f"  Misbelief: {misbelief}, Clarification: {clarification_triggered}")
                    if clarification_id:
                        print(f"  Clarification session: {clarification_id}")
                
                return response
            else:
                # No candidates found
                server_resp_ms = _now_ms()
                
                # ✅ Only write when logging is enabled
                enabled, run_id = _is_logging(session_id, provider)
                if enabled:
                    with open(paths["locate"], "a", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow([
                            site_id, run_id, datetime.utcnow().isoformat(), req_id, session_id, provider,
                            cap,
                            "", "0.0",
                            "", "0.0",
                            "0.0",
                            gt_node_id or "",
                            "", "", "",
                            "true", "no_candidates",
                            client_start_ms or "", server_recv_ms, server_resp_ms
                        ])
                
                return {
                    "req_id": req_id,
                    "caption": cap,
                    "node_id": None,
                    "confidence": 0.0,
                    "low_conf": True,
                    "candidates": [],
                    "retrieval_method": "unified_dual_channel_fusion"
                }
                
        except Exception as e:
            print(f"⚠ Unified dual-channel retrieval failed: {e}")
            print("⚠ 异常→沿用已算出的fused top-1，不回退到legacy")
            print("⚠ 保持上一个稳定位置状态，不更新会话位置")
            # 不回退到legacy，避免位置标签漂移打断continuity
            use_legacy = False
    
    # 检查是否需要回退到legacy
    if 'use_legacy' in locals() and not use_legacy:
        print("🔧 跳过legacy回退，保持fused top-1结果")
        # 🔧 NEW: 如果有成功的检索结果，返回实际结果而不是默认值
        if 'candidates' in locals() and candidates and len(candidates) > 0:
            top1 = candidates[0]
            top1_id = top1.get("id", "unknown")
            top1_score = float(top1.get("score", 0.0))
            
            # 🔧 NEW: 计算margin值
            top2_score = 0.0
            if len(candidates) > 1:
                top2_score = float(candidates[1].get("score", 0.0))
            margin = max(0.0, top1_score - top2_score)
            
            # 🔧 REMOVED: 后置 content-relevance × 0.6 / semantic-mismatch ×0.5 块。
            # 该块有缩进 bug（content_match_score 在外层 if 不命中时未定义即被引用），
            # 且仅在 retriever 异常时才到达；硬编码 "desk" 关键词的语义检查与 dual-channel
            # 校准管线（calibrate_confidence + apply_continuity_boost）冲突。已去掉，
            # 保持 top1_score 原样返回。

            print(f"🔧 返回成功的fused top-1结果: {top1_id} (confidence: {top1_score:.3f}, margin: {margin:.3f})")
            return {
                "req_id": req_id,
                "caption": cap,
                "node_id": top1_id,
                "confidence": top1_score,
                "margin": margin,
                "low_conf": top1_score < LOWCONF_SCORE_TH,
                "candidates": candidates,
                "retrieval_method": "fused_top1_success"
            }
        else:
            # 如果没有候选结果，才返回默认值
            print("🔧 没有候选结果，返回默认响应")
            return {
                "req_id": req_id,
                "caption": cap,
                "node_id": "unknown",
                "confidence": 0.0,
                "low_conf": True,
                "candidates": [],
                "retrieval_method": "fused_top1_no_candidates"
            }
    
    # Fallback to legacy retrieval (uses the module-level EMB SentenceTransformer
    # instance from L1161 — no need to re-import the class here)
    print("Using legacy retrieval system")
    def embed_text(t: str):
        return EMB.encode([t], normalize_embeddings=True, convert_to_numpy=True)[0].astype(np.float32).reshape(1,-1)
    item = SCENE[site_id]
    v = embed_text(cap)
    if "faiss" in str(type(item["index"])).lower():
        D, I = item["index"].search(v, 4)
        sims, idxs = D[0].tolist(), I[0].tolist()
    else:
        D, I = item["index"].kneighbors(v, n_neighbors=4, return_distance=True)
        sims = (1 - D[0]).tolist(); idxs = I[0].tolist()
    cands = []
    for s,i in zip(sims,idxs):
        meta = item["ids"][i]
        cands.append({"id": meta["id"], "type": meta["type"], "text": meta["text"], "score": float(s)})
    
    # Calculate confidence metrics for legacy system
    top1_score = cands[0]["score"] if cands else 0.0
    top2_score = cands[1]["score"] if len(cands) > 1 else 0.0
    margin = top1_score - top2_score
    # 🔧 FIX: 使用新的阈值：confidence > 40% 且 margin > 5% 就不触发low_conf
    low_conf = (len(cands)==0) or (top1_score < LOWCONF_SCORE_TH or margin < LOWCONF_MARGIN_TH)
    low_conf_rule = f"score<{LOWCONF_SCORE_TH*100:.0f}% OR margin<{LOWCONF_MARGIN_TH*100:.0f}%" if low_conf else f"confidence>{LOWCONF_SCORE_TH*100:.0f}% AND margin>{LOWCONF_MARGIN_TH*100:.0f}%"
    
    # Calculate hit metrics for legacy system
    top1_id = cands[0]["id"] if cands else ""
    top2_id = cands[1]["id"] if len(cands) > 1 else ""
    hit_top1 = (gt_node_id == top1_id) if gt_node_id else ""
    hit_top2 = (gt_node_id in [top1_id, top2_id]) if gt_node_id and top2_id else ""
    hit_hop1 = is_hop1(site_id, top1_id, gt_node_id) if gt_node_id else ""
    
    bearing = "ahead"
    t = cap.lower()
    if "left" in t: bearing = "left"
    elif "right" in t: bearing = "right"
    elif "behind" in t or "back" in t: bearing = "behind"
    
    # ✅ New: Track orientation and update session location for legacy system
    orientation_info = track_orientation(session_id, cap, top1_id)
    update_session_location(session_id, top1_id, top1_score, orientation_info)
    
    # Write comprehensive log for legacy system
    server_resp_ms = _now_ms()
    
    # ✅ Only write when logging is enabled
    enabled, run_id = _is_logging(session_id, provider)
    if enabled:
        with open(paths["locate"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                site_id, run_id, datetime.utcnow().isoformat(), req_id, session_id, provider,
                cap,
                top1_id, f"{top1_score:.6f}",
                top2_id, f"{top2_score:.6f}",
                f"{margin:.6f}",
                gt_node_id or "",
                str(hit_top1).lower(), str(hit_top2).lower(), str(hit_hop1).lower(),
                str(low_conf).lower(), low_conf_rule if low_conf else "",
                client_start_ms or "", server_recv_ms, server_resp_ms
            ])
    
    return {
        "req_id": req_id,
        "caption": cap, 
        "node_id": top1_id, 
        "confidence": top1_score,
        "low_conf": low_conf,
        "bearing": bearing, 
        "margin": margin,
        "candidates": cands,
        "retrieval_method": "legacy_fallback"
    }

@app.post("/api/asr")
async def api_asr(audio: UploadFile = File(...)):
    try:
        b = await audio.read()
        print(f"Received audio file: {audio.filename}, size: {len(b)} bytes")
        
        if not b or len(b) == 0:
            print("Empty audio file received")
            return {"text": "", "error": "empty_audio"}
        
        # Check file size (reasonable limit: 10MB)
        if len(b) > 10 * 1024 * 1024:
            print(f"Audio file too large: {len(b)} bytes")
            return {"text": "", "error": "file_too_large"}
        
        text = asr_bytes_to_text(b)
        if not text.strip():
            print("No speech detected in audio")
            return {"text": "", "error": "no_speech"}
        
        print(f"ASR successful: '{text}'")
        return {"text": text}
        
    except Exception as e:
        print(f"ASR API error: {e}")
        import traceback
        traceback.print_exc()
        return {"text": "", "error": f"asr_error: {str(e)}"}

class QAIn(BaseModel):
    session_id: str
    text: str
    lang: str = "en"


@app.post("/api/qa")
async def api_qa(body: QAIn):
    """Dynamic QA using GPT with enhanced location context"""
    try:
        sess = SESSIONS.get(body.session_id, {})
        site_id = sess.get("site_id", "SCENE_A_MS")
        lang = "zh" if body.lang.lower().startswith("zh") else "en"
        
        print(f"QA request: session={body.session_id}, site={site_id}, lang={lang}, text='{body.text}'")
        
        # ✅ New: Generate enhanced location context with secondary location verification
        location_context = generate_location_context_prompt(body.session_id, body.text, site_id, lang)
        print(f"📍 Generated location context: {location_context[:200]}...")
        
        # Create enhanced prompt for GPT with location verification
        if lang == "zh":
            prompt = f"""你是一个专业的室内导航助手，专门帮助用户在 {site_id} 中导航。

{location_context}

请根据以上详细的位置信息，为用户提供：
1. 基于当前位置的抽象导航指导（不要提及具体地点名称）
2. 考虑用户当前朝向的转向建议
3. 如果位置信息不明确，建议用户重新拍照确认
4. 提供通用的移动指导，如"向前走几步"、"向左转"等
5. 基于位置稳定性给出相应的建议

回答要简洁明了，适合语音播报，使用抽象的方向和距离描述。"""
        else:
            prompt = f"""You are a professional indoor navigation assistant, specifically helping users navigate in {site_id}.

{location_context}

Please provide:
1. Abstract navigation guidance based on current location (avoid specific location names)
2. Turn-by-turn guidance considering user's current orientation
3. Suggestion to retake photo if location is unclear
4. General movement guidance like "walk forward a few steps", "turn left", etc.
5. Recommendations based on location stability

Keep your answer concise and suitable for voice output, using abstract direction and distance descriptions."""
        
        print(f"GPT enhanced prompt: {prompt[:300]}...")
        
        # Call GPT for dynamic response with location context
        response = OAI.chat.completions.create(
            model=LLM_MODEL,
            temperature=LLM_TEMP,
            messages=[
                {"role": "system", "content": "You are a helpful indoor navigation assistant with precise location awareness."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200  # Increased for more detailed navigation guidance
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"GPT response with location context: {answer}")
        
        # ✅ New: Log the location-aware QA interaction
        try:
            session = SESSIONS.get(body.session_id, {})
            current_location = session.get("current_location", "unknown")
            
            # Log to clarification log if available
            paths = _log_paths(session.get("opening_provider", "ft"))
            _ensure_headers(paths)
            
            enabled, run_id = _is_logging(body.session_id, session.get("opening_provider", "ft"))
            if enabled:
                with open(paths["clar"], "a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([
                        site_id, run_id, datetime.utcnow().isoformat(), 
                        f"qa_{uuid.uuid4()}", body.session_id, session.get("opening_provider", "ft"),
                        "qa_location_aware",  # phase
                        f"qa_{uuid.uuid4()}", 1, "location_qa",  # req_id, round_idx, event
                        body.text, answer,  # user_text, system_text
                        current_location, "",  # resolved_node_id, gt_node_id
                        "success"  # success
                    ])
                print(f"📝 Location-aware QA logged to {paths['clar']}")
        except Exception as log_error:
            print(f"⚠️ Failed to log location-aware QA: {log_error}")
        
        # ✅ Collect DG metrics for QA interaction (guarded on collector).
        try:
            if enhanced_metrics_collector:
                enhanced_metrics_collector.collect_real_time_data(
                    MetricType.USER_BEHAVIOR,
                    body.session_id,
                    {
                        "action": "qa_interaction",
                        "site_id": site_id,
                        "lang": lang,
                        "user_question": body.text,
                        "system_response": answer,
                        "current_location": current_location,
                        "response_source": "gpt_location_aware"
                    },
                    priority=DataPriority.NORMAL,
                    tags=["navigation", "qa", "gpt", "location_aware"]
                )

            # Record DG4 evaluation (Segmentable and Repeatable Instructions)
            if dg_evaluator:
                dg_evaluator.dg4_evaluator.record_task_completion(
                    session_id=body.session_id,
                    task_id=f"qa_{uuid.uuid4()}",
                    task_type="navigation_qa",
                    status="completed",
                    completion_time=0,  # Could be enhanced with actual timing
                    veering_count=0
                )
            
            # Record user needs validation data (guarded — validator not wired yet)
            if user_needs_validator:
                user_needs_validator.record_validation_data(
                    body.session_id,
                    UserNeed.N3_SEGREGATED_INSTRUCTIONS,
                    "instruction_clarity",
                    4  # Assuming good clarity for GPT responses
                )
            
        except Exception as e:
            print(f"⚠️ Failed to collect DG metrics for QA: {e}")
        
        # Return response in the same format as before
        return {
            "mode": "qa",
            "say": [answer],
            "meta": {"source": "gpt_location_aware", "site_id": site_id, "lang": lang, "current_location": current_location},
            "source": "gpt"
        }
        
    except Exception as e:
        print(f"QA API error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback response
        if lang == "zh":
            fallback = "抱歉，我现在无法回答您的问题。请稍后再试。"
        else:
            fallback = "Sorry, I cannot answer your question right now. Please try again later."
        
        return {
            "mode": "qa",
            "say": [fallback],
            "meta": {"source": "fallback", "site_id": site_id, "lang": lang},
            "source": "fallback"
        }

@app.get("/api/session/location/{session_id}")
async def get_session_location(session_id: str):
    """Get current location and history for a session"""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = SESSIONS[session_id]
    
    return {
        "session_id": session_id,
        "current_location": session.get("current_location"),
        "site_id": session.get("site_id"),
        "provider": session.get("opening_provider"),
        "last_update": session.get("last_update_time"),
        "photo_count": session.get("photo_count", 0),
        "location_history": session.get("location_history", []),
        "orientation_history": session.get("orientation_history", []),
        "confidence_history": session.get("confidence_history", [])
    }

@app.get("/api/session/status/{session_id}")
async def get_session_status(session_id: str):
    """Get comprehensive session status including location tracking"""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = SESSIONS[session_id]
    session_key = f"{session_id}_{session.get('opening_provider', 'ft')}_{session.get('site_id', 'SCENE_A_MS')}"
    photo_count = SESSIONS.get("_photo_count", {}).get(session_key, 0)
    
    # Calculate location confidence trend
    confidence_history = session.get("confidence_history", [])
    confidence_trend = "stable"
    if len(confidence_history) >= 2:
        recent_avg = sum(confidence_history[-3:]) / min(3, len(confidence_history))
        earlier_avg = sum(confidence_history[:-3]) / max(1, len(confidence_history) - 3)
        if recent_avg > earlier_avg + 0.1:
            confidence_trend = "improving"
        elif recent_avg < earlier_avg - 0.1:
            confidence_trend = "declining"
    
    return {
        "session_id": session_id,
        "site_id": session.get("site_id"),
        "provider": session.get("opening_provider"),
        "current_location": session.get("current_location"),
        "photo_count": photo_count,
        "last_update": session.get("last_update_time"),
        "confidence_trend": confidence_trend,
        "location_stability": len(session.get("location_history", [])),
        "orientation_consistency": all(
            o.get("consistent", True) for o in session.get("orientation_history", [])
        )
    }



# Startup instructions (execute in project root directory):
# uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# ✅ New: Language Detection and Dynamic Navigation Functions
def detect_language_from_caption(caption: str, provider: str) -> str:
    """Detect language from caption text and provider type"""
    caption_lower = caption.lower()
    
    # Check for Chinese characters in caption
    chinese_chars = ['的', '在', '有', '和', '与', '是', '了', '到', '从', '向', '上', '下', '左', '右', '前', '后']
    if any(char in caption for char in chinese_chars):
        return "zh"
    
    # Check for common English words
    english_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
    if any(word in caption_lower for word in english_words):
        return "en"
    
    # Default based on provider (ft mode often uses Chinese, base mode often uses English)
    if provider.lower() == "ft":
        return "zh"  # Default to Chinese for ft mode
    else:
        return "en"  # Default to English for base mode

def generate_dynamic_navigation_response(site_id: str, node_id: str, confidence: float, low_conf: bool, matching_data: dict, lang: str = "en", candidate_info: dict = None) -> str:
    """修复：改进的动态导航响应生成"""
    print(f"🏗️ Layered Fusion navigation for {site_id} - {node_id} (conf: {confidence:.3f}, low_conf: {low_conf})")
    
    try:
        # 获取结构信息
        structure_info = get_structure_based_location_info(site_id, node_id, lang)
        
        # 获取detail增强信息
        detail_info = "None"
        if candidate_info and candidate_info.get("detail_metadata"):
            detail_info = get_detail_based_conversation_enhancement(node_id, candidate_info["detail_metadata"], lang)
        
        print(f"🔍 Layered fusion info: structure={confidence:.3f}, detail_items={len(candidate_info.get('detail_metadata', []) if candidate_info else [])}, method={candidate_info.get('retrieval_method', 'unknown') if candidate_info else 'unknown'}")
        print(f"🧭 Layered fusion response: structure='{structure_info[:50]}...', detail='{detail_info[:50] if detail_info else 'None'}...'")
        
        # 组合响应
        if detail_info and detail_info != "None":
            response = f"{structure_info} {detail_info}"
        else:
            response = structure_info
            
        return response
        
    except Exception as e:
        print(f"⚠️ Layered fusion response generation failed: {e}")
        # 回退到简单响应
        return f"You are at {node_id}. Please describe what you see around you."

def get_structure_based_location_info(site_id: str, node_id: str, lang: str = "en") -> str:
    """获取位置信息，避免NameError"""
    try:
        if site_id == "SCENE_A_MS":
            return generate_scene_a_structure_info(node_id, lang)
        elif site_id == "SCENE_B_STUDIO":
            return generate_scene_b_structure_info(node_id, lang)
        else:
            if lang == "zh":
                return f"当前位置：{node_id}。请告诉我您要去哪里。"
            else:
                return f"Current location: {node_id}. Please tell me where you want to go."
    except NameError:
        # 如果函数不存在，返回简单描述
        if lang == "zh":
            return f"当前位置：{node_id}。请告诉我您要去哪里。"
        else:
            return f"Current location: {node_id}. Please tell me where you want to go."

def get_detail_based_conversation_enhancement(node_id: str, detail_metadata: list, lang: str = "en") -> str:
    """获取对话增强信息，避免NameError"""
    try:
        if not detail_metadata:
            return ""
        
        # 使用第一个detail项进行对话增强
        detail_item = detail_metadata[0]
        
        # 提取空间关系和独特特征
        spatial_relations = detail_item.get("spatial_relations", {})
        unique_features = detail_item.get("unique_features", [])
        
        enhancement_parts = []

        # 🔧 FIX: 空间标签按 lang 切换，避免英文用户拿到中英混搭输出
        labels = ({
            "front": "前方", "left": "左侧", "right": "右侧",
            "back": "后方", "features": "特色",
        } if lang == "zh" else {
            "front": "Front", "left": "Left", "right": "Right",
            "back": "Back", "features": "Features",
        })

        # 添加空间上下文
        if spatial_relations:
            for k in ("front", "left", "right", "back"):
                v = spatial_relations.get(k)
                if v and v != "n/a":
                    enhancement_parts.append(f"{labels[k]}: {v}")

        # 添加独特特征
        if unique_features:
            features = [f for f in unique_features if f]
            if features:
                enhancement_parts.append(f"{labels['features']}: {', '.join(features)}")

        if enhancement_parts:
            if lang == "zh":
                return f"环境描述：{'；'.join(enhancement_parts)}。"
            else:
                return f"Environment: {'; '.join(enhancement_parts)}."

        return ""
    except Exception as e:
        print(f"⚠️ Detail enhancement failed: {e}")
        return ""






# ✅ Enhanced preset output function that uses AI spatial reasoning

# ============================================================================
# ✅ New: DG Optimization API Endpoints
# ============================================================================

@app.post("/api/dg/metrics/collect")
async def collect_dg_metrics(
    session_id: str,
    metric_type: str,
    data: Dict[str, Any],
    priority: str = "normal",
    tags: List[str] = None
):
    """Collect DG optimization metrics"""
    if not enhanced_metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not wired (see README §8)")
    try:
        # Convert string to enum
        metric_type_enum = MetricType(metric_type)
        priority_enum = DataPriority(priority)
        
        success = enhanced_metrics_collector.collect_real_time_data(
            metric_type_enum,
            session_id,
            data,
            priority_enum,
            tags or []
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to collect metrics")
        
        return {
            "session_id": session_id,
            "metric_type": metric_type,
            "status": "collected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")

@app.get("/api/dg/metrics/export/{session_id}")
async def export_session_metrics(session_id: str, format: str = "csv"):
    """Export session metrics"""
    if not enhanced_metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not wired (see README §8)")
    try:
        if format.lower() == "csv":
            filename = f"session_{session_id}_metrics.csv"
            success = enhanced_metrics_collector.export_data_to_csv(filename, session_id=session_id)
        elif format.lower() == "json":
            filename = f"session_{session_id}_metrics.json"
            success = enhanced_metrics_collector.export_data_to_json(filename, session_id=session_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'")
        
        if not success:
            raise HTTPException(status_code=500, detail="Export failed")
        
        return {
            "session_id": session_id,
            "format": format,
            "filename": filename,
            "status": "exported",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/dg/metrics/analytics/{session_id}")
async def get_metrics_analytics(session_id: str):
    """Get analytics report for a session"""
    if not enhanced_metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not wired (see README §8)")
    try:
        report = enhanced_metrics_collector.generate_analytics_report(session_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")

@app.get("/api/dg/metrics/stats")
async def get_metrics_collection_stats():
    """Get metrics collection statistics"""
    if not enhanced_metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not wired (see README §8)")
    try:
        stats = enhanced_metrics_collector.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection stats: {str(e)}")

@app.get("/api/dg/metrics/discrimination/{session_id}")
async def get_discrimination_metrics(session_id: str, tie_threshold: float = 0.05,
                                     include_events: bool = False, limit: int = 100):
    """检索区分度（discrimination）会话级指标 + 可选的原始事件列表。
    tie_threshold: 把 margin<该阈值的事件视为 tie（区分度差）。
    include_events=true 时返回 raw events（最多 `limit` 条，按时间倒序）。
    传 session_id='all' 聚合全部 session。
    """
    if dg_evaluator is None:
        raise HTTPException(status_code=503, detail="DG evaluator not initialized")
    sid = None if session_id == "all" else session_id
    try:
        stats = dg_evaluator.dg2_evaluator.get_discrimination_stats(sid, tie_threshold=tie_threshold)
        out = {"stats": stats}
        if include_events:
            evts = dg_evaluator.dg2_evaluator.discrimination_events
            if sid is not None:
                evts = [e for e in evts if e["session_id"] == sid]
            out["events"] = list(reversed(evts))[:max(0, int(limit))]
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute discrimination stats: {e}")

@app.post("/api/dg/metrics/session/{session_id}/close")
async def close_metrics_session(session_id: str):
    """Close a metrics collection session"""
    if not enhanced_metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not wired (see README §8)")
    try:
        enhanced_metrics_collector.close_session(session_id)
        return {
            "session_id": session_id,
            "status": "closed",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close session: {str(e)}")

@app.post("/api/dg/evaluation/record")
async def record_dg_evaluation(
    session_id: str,
    design_goal: str,
    evaluation_data: Dict[str, Any]
):
    """Record DG evaluation data"""
    try:
        if not dg_evaluator:
            raise HTTPException(status_code=503, detail="DG evaluation not enabled")
        
        # Record evaluation data based on design goal
        if design_goal == "DG1":
            dg_evaluator.dg1_evaluator.record_setup_process(
                session_id=session_id,
                steps=evaluation_data.get("steps", []),
                time_taken=evaluation_data.get("time_taken", 0),
                success=evaluation_data.get("success", False)
            )
        elif design_goal == "DG2":
            dg_evaluator.dg2_evaluator.record_landmark_recall(
                session_id=session_id,
                task_id=evaluation_data.get("task_id", ""),
                landmarks_presented=evaluation_data.get("landmarks_presented", []),
                landmarks_recalled=evaluation_data.get("landmarks_recalled", []),
                time_delay=evaluation_data.get("time_delay", 0)
            )
        elif design_goal == "DG3":
            dg_evaluator.dg3_evaluator.record_interaction_behavior(
                session_id=session_id,
                photo_count=evaluation_data.get("photo_count", 0),
                first_photo_success=evaluation_data.get("first_photo_success", False),
                adjustment_actions=evaluation_data.get("adjustment_actions", [])
            )
        elif design_goal == "DG4":
            dg_evaluator.dg4_evaluator.record_task_completion(
                session_id=session_id,
                task_id=evaluation_data.get("task_id", ""),
                task_type=evaluation_data.get("task_type", ""),
                status=evaluation_data.get("status", "not_started"),
                completion_time=evaluation_data.get("completion_time", 0),
                veering_count=evaluation_data.get("veering_count", 0)
            )
        elif design_goal == "DG5":
            dg_evaluator.dg5_evaluator.record_clarification_dialogue(
                session_id=session_id,
                dialogue_id=evaluation_data.get("dialogue_id", ""),
                ambiguity_before=evaluation_data.get("ambiguity_before", 0),
                ambiguity_after=evaluation_data.get("ambiguity_after", 0),
                dialogue_count=evaluation_data.get("dialogue_count", 0)
            )
        elif design_goal == "DG6":
            dg_evaluator.dg6_evaluator.record_wcag_compliance(
                session_id=session_id,
                wcag_guideline=evaluation_data.get("wcag_guideline", ""),
                compliance_status=evaluation_data.get("compliance_status", ""),
                issues_found=evaluation_data.get("issues_found", [])
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid design goal")
        
        return {
            "session_id": session_id,
            "design_goal": design_goal,
            "status": "recorded",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation recording failed: {str(e)}")

@app.get("/api/dg/evaluation/report/{session_id}")
async def get_dg_evaluation_report(session_id: str):
    """Get comprehensive DG evaluation report"""
    try:
        if not dg_evaluator:
            raise HTTPException(status_code=503, detail="DG evaluation not enabled")
        
        report = dg_evaluator.generate_evaluation_report(session_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.post("/api/dg/accessibility/check")
async def check_accessibility_compliance(
    interface_elements: Dict[str, Any],
    target_level: str = "AA"
):
    """Check WCAG accessibility compliance"""
    try:
        if not accessibility_checker:
            raise HTTPException(status_code=503, detail="Accessibility checking not enabled")
        
        # Convert string to enum
        from accessibility_checker import WCAGLevel
        level_enum = WCAGLevel(target_level.upper())
        
        results = accessibility_checker.check_wcag_compliance(interface_elements, level_enum)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Accessibility check failed: {str(e)}")

@app.post("/api/dg/accessibility/voiceover")
async def test_voiceover_compatibility(features: Dict[str, Any]):
    """Test VoiceOver compatibility"""
    try:
        if not accessibility_checker:
            raise HTTPException(status_code=503, detail="Accessibility checking not enabled")
        
        results = accessibility_checker.test_voiceover_compatibility(features)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VoiceOver test failed: {str(e)}")

@app.post("/api/dg/indoor_gml/generate")
async def generate_indoor_gml_map(
    site_data: Dict[str, Any],
    landmarks: List[Dict[str, Any]],
    connections: List[Dict[str, Any]]
):
    """Generate IndoorGML standard map"""
    try:
        if not indoor_gml_generator:
            raise HTTPException(status_code=503, detail="IndoorGML generation not enabled")
        
        gml_content = indoor_gml_generator.generate_indoor_gml(site_data, landmarks, connections)
        return {
            "status": "generated",
            "content_length": len(gml_content),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IndoorGML generation failed: {str(e)}")

@app.post("/api/dg/indoor_gml/validate")
async def validate_indoor_gml_compliance(gml_content: str):
    """Validate IndoorGML standard compliance"""
    try:
        if not indoor_gml_generator:
            raise HTTPException(status_code=503, detail="IndoorGML validation not enabled")
        
        validation_results = indoor_gml_generator.validate_standard_compliance(gml_content)
        return validation_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IndoorGML validation failed: {str(e)}")

@app.get("/api/dg/user_needs/validation/{session_id}")
async def get_user_needs_validation(session_id: str):
    """Get user needs validation report"""
    if not user_needs_validator:
        raise HTTPException(status_code=503, detail="User needs validator not wired (see README §8)")
    try:
        report = user_needs_validator.generate_comprehensive_report(session_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User needs validation failed: {str(e)}")

@app.post("/api/dg/user_needs/record")
async def record_user_needs_data(
    session_id: str,
    user_need: str,
    metric_name: str,
    value: Any
):
    """Record user needs validation data"""
    if not user_needs_validator:
        raise HTTPException(status_code=503, detail="User needs validator not wired (see README §8)")
    try:
        # Convert string to enum
        need_enum = UserNeed(user_need)

        user_needs_validator.record_validation_data(session_id, need_enum, metric_name, value)
        return {
            "session_id": session_id,
            "user_need": user_need,
            "metric_name": metric_name,
            "status": "recorded",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User needs recording failed: {str(e)}")

@app.get("/api/dg/user_needs/matrix")
async def get_user_needs_matrix():
    """Get user needs to design goals mapping matrix"""
    if not user_needs_validator:
        raise HTTPException(status_code=503, detail="User needs validator not wired (see README §8)")
    try:
        matrix = user_needs_validator.get_requirement_goal_matrix()
        return {
            "matrix": matrix,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get matrix: {str(e)}")

# ============================================================================
# ✅ Enhanced Health Check with DG Optimization Status
# ============================================================================

@app.get("/health/enhanced")
async def enhanced_health_check():
    """Enhanced health check with DG optimization status"""
    base_health = await health_check()
    
    dg_status = {
        "dg_evaluation": {
            "enabled": ENABLE_DG_EVALUATION,
            "status": "available" if dg_evaluator else "disabled"
        },
        "accessibility_checking": {
            "enabled": ENABLE_ACCESSIBILITY_CHECKING,
            "status": "available" if accessibility_checker else "disabled"
        },
        "indoor_gml": {
            "enabled": ENABLE_INDOOR_GML,
            "status": "available" if indoor_gml_generator else "disabled"
        },
        "enhanced_metrics": {
            "status": "available" if enhanced_metrics_collector else "disabled",
            "storage_path": METRICS_STORAGE_PATH
        },
        "user_needs_validation": {
            "status": "available" if user_needs_validator else "disabled"
        }
    }
    
    return {
        **base_health,
        "dg_optimization": dg_status
    }

def generate_scene_a_structure_info(node_id: str, lang: str = "en") -> str:
    """Generate structure-based location information for SCENE_A_MS from Sense_A_Finetuned.fixed.jsonl"""
    if lang == "zh":
        # 中文导航指令 - 基于Structure文件的拓扑信息
        if node_id == "dp_ms_entrance":
            return "您在Maker Space入口。直行约6步到达3D打印机桌，然后左转继续前进进入中庭。"
        
        elif node_id == "yline_start":
            return "您在黄色引导线起点。直行约3步到达椅子位置，然后继续沿引导线前进。"
        
        elif node_id == "chair_on_yline":
            return "您在黄色引导线上的椅子旁。继续直行约2步，引导线将向左弯曲。"
        
        elif node_id == "yline_bend_mid":
            return "您在黄色引导线弯曲处。直行约7步到达窗户和软座区域，然后进入中庭。"
        
        elif node_id == "atrium_edge":
            return "您在中庭边缘，靠近窗户和软座。右转约5步到达电视区域。"
        
        elif node_id == "tv_zone":
            return "您在电视区域。前方约4步到达小会议桌，然后继续前进到橙色沙发。"
        
        elif node_id == "small_table_mid":
            return "您在低矮会议桌旁。直行约3步到达橙色沙发角落。"
        
        elif node_id == "orange_sofa_corner":
            return "您已到达橙色沙发角落，靠墙放置。导航任务完成！"
        
        else:
            return f"当前位置：{node_id}。请告诉我您要去哪里。"
    
    else:
        # English navigation instructions - based on Structure file topology
        if node_id == "dp_ms_entrance":
            return "You are at the Maker Space entrance. Walk straight about 6 steps to reach the 3D printer table, then turn left to continue into the atrium."
        
        elif node_id == "yline_start":
            return "You are at the yellow line start. Walk straight about 3 steps to reach the chair position, then continue along the guide line."
        
        elif node_id == "chair_on_yline":
            return "You are at the chair on the yellow line. Continue straight about 2 steps, the line will bend left."
        
        elif node_id == "yline_bend_mid":
            return "You are at the yellow line bend. Walk straight about 7 steps to reach the windows and soft seats, then enter the atrium."
        
        elif node_id == "atrium_edge":
            return "You are at the atrium edge, near windows and soft seats. Turn right about 5 steps to reach the TV zone."
        
        elif node_id == "tv_zone":
            return "You are in the TV zone. Walk forward about 4 steps to reach the small meeting table, then continue to the orange sofa."
        
        elif node_id == "small_table_mid":
            return "You are at the low meeting table. Walk straight about 3 steps to reach the orange sofa corner."
        
        elif node_id == "orange_sofa_corner":
            return "You have reached the orange sofa corner, against the wall. Navigation task completed!"
        
        else:
            return f"Current location: {node_id}. Please tell me where you want to go."

def generate_scene_b_structure_info(node_id: str, lang: str = "en") -> str:
    """Generate structure-based location information for SCENE_B_STUDIO from Sense_B_Finetuned.fixed.jsonl"""
    if lang == "zh":
        # 中文导航指令 - 基于Structure文件的拓扑信息
        if node_id == "atrium_desks_hub":
            return "您在中央工作台区域，面向大电视屏幕。左侧是窗户墙，右侧是橙色沙发区域。"
        
        elif node_id == "node_left_to_windows":
            return "您正在向左转向窗户方向。直行约2步到达窗户边缘的软座区域。"
        
        elif node_id == "atrium_windows_edge":
            return "您在窗户边缘的软座区域。向后转约3步到达小白色会议桌，然后继续前进到橙色沙发。"
        
        elif node_id == "poi_small_table":
            return "您在白色会议桌旁，桌上有紫色椅子。直行约2步到达橙色沙发区域。"
        
        elif node_id == "poi_orange_green_sofa":
            return "您已到达橙色沙发区域，沙发靠墙放置。附近有绿色高背扶手椅和两个黑色边桌。"
        
        else:
            return f"当前位置：{node_id}。请告诉我您要去哪里。"
    
    else:
        # English navigation instructions - based on Structure file topology
        if node_id == "atrium_desks_hub":
            return "You are at the central desks hub, facing the large TV screen. To your left is the windows wall, to your right is the orange sofa area."
        
        elif node_id == "node_left_to_windows":
            return "You are turning left toward the windows. Walk straight about 2 steps to reach the soft seats area at the window edge."
        
        elif node_id == "atrium_windows_edge":
            return "You are at the soft seats area by the windows. Turn around and walk about 3 steps to reach the small white meeting table, then continue to the orange sofa."
        
        elif node_id == "poi_small_table":
            return "You are at the white meeting table with purple chairs. Walk straight about 2 steps to reach the orange sofa area."
        
        elif node_id == "poi_orange_green_sofa":
            return "You have reached the orange sofa area, with the sofa against the wall. Nearby are a green high-back armchair and two black side tables."
        
        else:
            return f"Current location: {node_id}. Please tell me where you want to go."

# ✅ New: AI Spatial Reasoning System to Replace Preset Outputs
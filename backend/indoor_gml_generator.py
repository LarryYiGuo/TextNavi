"""
IndoorGML标准地图生成器 (IndoorGML Standard Map Generator)
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

# ============================================================================
# IndoorGML标准定义 (IndoorGML Standard Definition)
# ============================================================================

class IndoorGMLNamespace:
    """IndoorGML命名空间"""
    INDOOR_GML = "http://www.opengis.net/indoorgml/1.0/core"
    GML = "http://www.opengis.net/gml/3.2"
    XSI = "http://www.w3.org/2001/XMLSchema-instance"
    XSD = "http://www.opengis.net/indoorgml/1.0/core http://schemas.opengis.net/indoorgml/1.0/indoorgmlcore.xsd"

class IndoorGMLFeatureType(Enum):
    """IndoorGML要素类型"""
    INDOOR_FEATURES = "IndoorFeatures"
    PRIMAL_SPACE_FEATURES = "PrimalSpaceFeatures"
    MULTI_LAYERED_GRAPH = "MultiLayeredGraph"
    CELL_SPACE = "CellSpace"
    CELL_SPACE_BOUNDARY = "CellSpaceBoundary"
    STATE = "State"
    TRANSITION = "Transition"
    CONNECTED_SPACE = "ConnectedSpace"

@dataclass
class IndoorGMLGeometry:
    """IndoorGML几何信息"""
    geometry_type: str  # Point, LineString, Polygon
    coordinates: List[Tuple[float, float, float]]  # (x, y, z)
    srs_name: str = "EPSG:4326"  # 坐标参考系统

@dataclass
class IndoorGMLFeature:
    """IndoorGML要素"""
    feature_id: str
    feature_type: IndoorGMLFeatureType
    name: str
    description: str
    geometry: Optional[IndoorGMLGeometry] = None
    properties: Dict[str, Any] = None

@dataclass
class IndoorGMLConnection:
    """IndoorGML连接关系"""
    connection_id: str
    from_feature: str
    to_feature: str
    connection_type: str  # "adjacent", "connected", "transition"
    properties: Dict[str, Any] = None

# ============================================================================
# IndoorGML生成器 (IndoorGML Generator)
# ============================================================================

class IndoorGMLGenerator:
    """IndoorGML标准地图生成器"""
    
    def __init__(self):
        self.features = []
        self.connections = []
        self.metadata = {}
        self.namespaces = IndoorGMLNamespace()
    
    def add_feature(self, feature: IndoorGMLFeature):
        """添加要素"""
        self.features.append(feature)
    
    def add_connection(self, connection: IndoorGMLConnection):
        """添加连接关系"""
        self.connections.append(connection)
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """设置元数据"""
        self.metadata = metadata
    
    def generate_indoor_gml(self, site_data: Dict[str, Any], 
                           landmarks: List[Dict[str, Any]], 
                           connections: List[Dict[str, Any]]) -> str:
        """生成符合IndoorGML标准的地图文件"""
        # 清空现有数据
        self.features = []
        self.connections = []
        
        # 处理站点数据
        self._process_site_data(site_data)
        
        # 处理地标数据
        self._process_landmarks(landmarks)
        
        # 处理连接关系
        self._process_connections(connections)
        
        # 生成XML
        return self._generate_xml()
    
    def _process_site_data(self, site_data: Dict[str, Any]):
        """处理站点数据"""
        # 创建室内特征集合
        indoor_features = IndoorGMLFeature(
            feature_id=f"site_{site_data.get('site_id', 'unknown')}",
            feature_type=IndoorGMLFeatureType.INDOOR_FEATURES,
            name=site_data.get('name', 'Indoor Site'),
            description=site_data.get('description', 'Indoor navigation site'),
            properties={
                'site_type': site_data.get('type', 'general'),
                'floor_count': site_data.get('floor_count', 1),
                'total_area': site_data.get('total_area', 0)
            }
        )
        
        self.add_feature(indoor_features)
        
        # 创建原始空间特征
        primal_space = IndoorGMLFeature(
            feature_id=f"primal_space_{site_data.get('site_id', 'unknown')}",
            feature_type=IndoorGMLFeatureType.PRIMAL_SPACE_FEATURES,
            name="Primal Space Features",
            description="Primary space features of the site",
            properties={
                'parent_feature': indoor_features.feature_id
            }
        )
        
        self.add_feature(primal_space)
    
    def _process_landmarks(self, landmarks: List[Dict[str, Any]]):
        """处理地标数据"""
        for landmark in landmarks:
            # 创建空间单元
            cell_space = IndoorGMLFeature(
                feature_id=f"cell_{landmark.get('id', str(uuid.uuid4()))}",
                feature_type=IndoorGMLFeatureType.CELL_SPACE,
                name=landmark.get('name', 'Unknown Landmark'),
                description=landmark.get('description', 'Landmark description'),
                geometry=self._create_geometry_from_landmark(landmark),
                properties={
                    'landmark_type': landmark.get('type', 'general'),
                    'accessibility': landmark.get('accessibility', True),
                    'importance': landmark.get('importance', 'medium'),
                    'parent_feature': f"primal_space_{landmark.get('site_id', 'unknown')}"
                }
            )
            
            self.add_feature(cell_space)
            
            # 创建状态
            state = IndoorGMLFeature(
                feature_id=f"state_{landmark.get('id', str(uuid.uuid4()))}",
                feature_type=IndoorGMLFeatureType.STATE,
                name=f"State of {landmark.get('name', 'Unknown')}",
                description=f"Current state of {landmark.get('name', 'landmark')}",
                properties={
                    'parent_feature': cell_space.feature_id,
                    'state_type': 'occupied',  # 可以根据实际情况调整
                    'capacity': landmark.get('capacity', 1)
                }
            )
            
            self.add_feature(state)
    
    def _process_connections(self, connections: List[Dict[str, Any]]):
        """处理连接关系"""
        for connection in connections:
            # 创建转换关系
            transition = IndoorGMLFeature(
                feature_id=f"transition_{connection.get('id', str(uuid.uuid4()))}",
                feature_type=IndoorGMLFeatureType.TRANSITION,
                name=f"Transition {connection.get('from', '')} to {connection.get('to', '')}",
                description=f"Connection between {connection.get('from', '')} and {connection.get('to', '')}",
                properties={
                    'from_state': f"state_{connection.get('from', '')}",
                    'to_state': f"state_{connection.get('to', '')}",
                    'connection_type': connection.get('type', 'adjacent'),
                    'distance': connection.get('distance', 0),
                    'direction': connection.get('direction', 'unknown')
                }
            )
            
            self.add_feature(transition)
            
            # 创建连接空间
            connected_space = IndoorGMLFeature(
                feature_id=f"connected_space_{connection.get('id', str(uuid.uuid4()))}",
                feature_type=IndoorGMLFeatureType.CONNECTED_SPACE,
                name=f"Connected Space {connection.get('from', '')}-{connection.get('to', '')}",
                description=f"Space connecting {connection.get('from', '')} and {connection.get('to', '')}",
                properties={
                    'parent_feature': transition.feature_id,
                    'connectivity_type': 'adjacent'
                }
            )
            
            self.add_feature(connected_space)
    
    def _create_geometry_from_landmark(self, landmark: Dict[str, Any]) -> Optional[IndoorGMLGeometry]:
        """从地标数据创建几何信息"""
        if 'geometry' not in landmark:
            return None
        
        geom_data = landmark['geometry']
        geom_type = geom_data.get('type', 'Point')
        coordinates = geom_data.get('coordinates', [])
        
        # 转换坐标格式
        if geom_type == 'Point':
            coords = [tuple(coord) if len(coord) >= 3 else (*coord, 0) for coord in coordinates]
        elif geom_type == 'Polygon':
            coords = [tuple(coord) if len(coord) >= 3 else (*coord, 0) for coord in coordinates[0]]
        else:
            coords = []
        
        return IndoorGMLGeometry(
            geometry_type=geom_type,
            coordinates=coords,
            srs_name=geom_data.get('srs_name', 'EPSG:4326')
        )
    
    def _generate_xml(self) -> str:
        """生成XML内容"""
        # 创建根元素
        root = ET.Element(f"{{{self.namespaces.INDOOR_GML}}}IndoorFeatures")
        
        # 添加命名空间
        root.set(f"xmlns:{self.namespaces.INDOOR_GML.split('/')[-1]}", self.namespaces.INDOOR_GML)
        root.set(f"xmlns:{self.namespaces.GML.split('/')[-1]}", self.namespaces.GML)
        root.set(f"xmlns:{self.namespaces.XSI.split('/')[-1]}", self.namespaces.XSI)
        root.set(f"{{{self.namespaces.XSI}}}schemaLocation", self.namespaces.XSD)
        
        # 添加元数据
        if self.metadata:
            self._add_metadata_element(root)
        
        # 添加要素
        for feature in self.features:
            self._add_feature_element(root, feature)
        
        # 添加连接关系
        if self.connections:
            self._add_connections_element(root)
        
        # 格式化XML
        xml_string = ET.tostring(root, encoding='unicode')
        return self._pretty_xml(xml_string)
    
    def _add_metadata_element(self, root: ET.Element):
        """添加元数据元素"""
        metadata_elem = ET.SubElement(root, f"{{{self.namespaces.INDOOR_GML}}}metadata")
        
        for key, value in self.metadata.items():
            meta_elem = ET.SubElement(metadata_elem, f"{{{self.namespaces.INDOOR_GML}}}{key}")
            meta_elem.text = str(value)
    
    def _add_feature_element(self, root: ET.Element, feature: IndoorGMLFeature):
        """添加要素元素"""
        feature_elem = ET.SubElement(root, f"{{{self.namespaces.INDOOR_GML}}}{feature.feature_type.value}")
        feature_elem.set("gml:id", feature.feature_id)
        
        # 添加名称
        name_elem = ET.SubElement(feature_elem, f"{{{self.namespaces.GML}}}name")
        name_elem.text = feature.name
        
        # 添加描述
        if feature.description:
            desc_elem = ET.SubElement(feature_elem, f"{{{self.namespaces.GML}}}description")
            desc_elem.text = feature.description
        
        # 添加几何信息
        if feature.geometry:
            self._add_geometry_element(feature_elem, feature.geometry)
        
        # 添加属性
        if feature.properties:
            self._add_properties_element(feature_elem, feature.properties)
    
    def _add_geometry_element(self, parent: ET.Element, geometry: IndoorGMLGeometry):
        """添加几何元素"""
        if geometry.geometry_type == 'Point':
            geom_elem = ET.SubElement(parent, f"{{{self.namespaces.GML}}}point")
            coord_elem = ET.SubElement(geom_elem, f"{{{self.namespaces.GML}}}pos")
            coord_elem.set("srsName", geometry.srs_name)
            coord_elem.text = " ".join(str(coord) for coord in geometry.coordinates[0])
        
        elif geometry.geometry_type == 'Polygon':
            geom_elem = ET.SubElement(parent, f"{{{self.namespaces.GML}}}polygon")
            exterior_elem = ET.SubElement(geom_elem, f"{{{self.namespaces.GML}}}exterior")
            linear_ring_elem = ET.SubElement(exterior_elem, f"{{{self.namespaces.GML}}}LinearRing")
            pos_list_elem = ET.SubElement(linear_ring_elem, f"{{{self.namespaces.GML}}}posList")
            pos_list_elem.set("srsName", geometry.srs_name)
            pos_list_elem.text = " ".join(str(coord) for coord in geometry.coordinates)
    
    def _add_properties_element(self, parent: ET.Element, properties: Dict[str, Any]):
        """添加属性元素"""
        for key, value in properties.items():
            prop_elem = ET.SubElement(parent, f"{{{self.namespaces.INDOOR_GML}}}{key}")
            prop_elem.text = str(value)
    
    def _add_connections_element(self, root: ET.Element):
        """添加连接关系元素"""
        connections_elem = ET.SubElement(root, f"{{{self.namespaces.INDOOR_GML}}}connections")
        
        for connection in self.connections:
            conn_elem = ET.SubElement(connections_elem, f"{{{self.namespaces.INDOOR_GML}}}connection")
            conn_elem.set("gml:id", connection.connection_id)
            
            # 添加连接类型
            type_elem = ET.SubElement(conn_elem, f"{{{self.namespaces.INDOOR_GML}}}connectionType")
            type_elem.text = connection.connection_type
            
            # 添加连接要素
            from_elem = ET.SubElement(conn_elem, f"{{{self.namespaces.INDOOR_GML}}}fromFeature")
            from_elem.set("xlink:href", f"#{connection.from_feature}")
            
            to_elem = ET.SubElement(conn_elem, f"{{{self.namespaces.INDOOR_GML}}}toFeature")
            to_elem.set("xlink:href", f"#{connection.to_feature}")
            
            # 添加属性
            if connection.properties:
                self._add_properties_element(conn_elem, connection.properties)
    
    def _pretty_xml(self, xml_string: str) -> str:
        """格式化XML字符串"""
        try:
            dom = minidom.parseString(xml_string)
            return dom.toprettyxml(indent="  ")
        except Exception:
            return xml_string
    
    def validate_standard_compliance(self, gml_content: str) -> Dict[str, Any]:
        """验证IndoorGML标准合规性"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "compliance_score": 1.0,
            "recommendations": []
        }
        
        try:
            # 解析XML
            root = ET.fromstring(gml_content)
            
            # 检查命名空间
            self._validate_namespaces(root, validation_results)
            
            # 检查必需元素
            self._validate_required_elements(root, validation_results)
            
            # 检查要素结构
            self._validate_feature_structure(root, validation_results)
            
            # 检查几何信息
            self._validate_geometry(root, validation_results)
            
            # 计算合规性分数
            validation_results["compliance_score"] = self._calculate_compliance_score(validation_results)
            
        except ET.ParseError as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"XML parsing error: {e}")
            validation_results["compliance_score"] = 0.0
        
        return validation_results
    
    def _validate_namespaces(self, root: ET.Element, results: Dict[str, Any]):
        """验证命名空间"""
        required_namespaces = [
            self.namespaces.INDOOR_GML,
            self.namespaces.GML
        ]
        
        for ns in required_namespaces:
            if not any(ns in value for value in root.attrib.values()):
                results["warnings"].append(f"Missing namespace: {ns}")
                results["recommendations"].append(f"Add namespace declaration for {ns}")
    
    def _validate_required_elements(self, root: ET.Element, results: Dict[str, Any]):
        """验证必需元素"""
        required_elements = [
            "IndoorFeatures",
            "PrimalSpaceFeatures"
        ]
        
        for elem_name in required_elements:
            if not root.find(f".//{{{self.namespaces.INDOOR_GML}}}{elem_name}"):
                results["warnings"].append(f"Missing required element: {elem_name}")
                results["recommendations"].append(f"Add {elem_name} element")
    
    def _validate_feature_structure(self, root: ET.Element, results: Dict[str, Any]):
        """验证要素结构"""
        # 检查要素ID的唯一性
        feature_ids = []
        for feature in root.findall(f".//{{{self.namespaces.INDOOR_GML}}}*"):
            feature_id = feature.get("gml:id")
            if feature_id:
                if feature_id in feature_ids:
                    results["errors"].append(f"Duplicate feature ID: {feature_id}")
                else:
                    feature_ids.append(feature_id)
        
        # 检查要素引用
        for feature in root.findall(f".//{{{self.namespaces.INDOOR_GML}}}*"):
            for ref_attr in ["xlink:href", "href"]:
                ref_value = feature.get(ref_attr)
                if ref_value and ref_value.startswith("#"):
                    ref_id = ref_value[1:]
                    if ref_id not in feature_ids:
                        results["warnings"].append(f"Invalid reference: {ref_value}")
                        results["recommendations"].append(f"Fix reference to {ref_id}")
    
    def _validate_geometry(self, root: ET.Element, results: Dict[str, Any]):
        """验证几何信息"""
        # 检查坐标系统
        for geom_elem in root.findall(f".//{{{self.namespaces.GML}}}pos"):
            srs_name = geom_elem.get("srsName")
            if not srs_name:
                results["warnings"].append("Missing SRS name in geometry")
                results["recommendations"].append("Add srsName attribute to geometry elements")
        
        # 检查坐标值
        for coord_elem in root.findall(f".//{{{self.namespaces.GML}}}pos"):
            if coord_elem.text:
                try:
                    coords = [float(x) for x in coord_elem.text.split()]
                    if len(coords) < 2:
                        results["warnings"].append("Insufficient coordinates")
                        results["recommendations"].append("Provide at least 2D coordinates")
                except ValueError:
                    results["errors"].append("Invalid coordinate values")
                    results["recommendations"].append("Fix coordinate format")
    
    def _calculate_compliance_score(self, results: Dict[str, Any]) -> float:
        """计算合规性分数"""
        base_score = 1.0
        
        # 错误扣分
        error_penalty = len(results["errors"]) * 0.2
        base_score -= error_penalty
        
        # 警告扣分
        warning_penalty = len(results["warnings"]) * 0.05
        base_score -= warning_penalty
        
        return max(0.0, base_score)
    
    def export_to_json(self, filename: str):
        """导出为JSON格式"""
        export_data = {
            "metadata": self.metadata,
            "features": [],
            "connections": []
        }
        
        for feature in self.features:
            feature_data = {
                "id": feature.feature_id,
                "type": feature.feature_type.value,
                "name": feature.name,
                "description": feature.description,
                "properties": feature.properties or {}
            }
            
            if feature.geometry:
                feature_data["geometry"] = {
                    "type": feature.geometry.geometry_type,
                    "coordinates": feature.geometry.coordinates,
                    "srs_name": feature.geometry.srs_name
                }
            
            export_data["features"].append(feature_data)
        
        for connection in self.connections:
            connection_data = {
                "id": connection.connection_id,
                "from_feature": connection.from_feature,
                "to_feature": connection.to_feature,
                "connection_type": connection.connection_type,
                "properties": connection.properties or {}
            }
            
            export_data["connections"].append(connection_data)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to export JSON: {e}")
            return False
    
    def export_to_csv(self, filename: str):
        """导出为CSV格式"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                # 导出要素
                feature_writer = csv.writer(csvfile)
                feature_writer.writerow(['Feature ID', 'Type', 'Name', 'Description', 'Properties'])
                
                for feature in self.features:
                    properties_str = json.dumps(feature.properties or {}, ensure_ascii=False)
                    feature_writer.writerow([
                        feature.feature_id,
                        feature.feature_type.value,
                        feature.name,
                        feature.description,
                        properties_str
                    ])
                
                # 导出连接关系
                csvfile.write('\n')  # 空行分隔
                connection_writer = csv.writer(csvfile)
                connection_writer.writerow(['Connection ID', 'From Feature', 'To Feature', 'Type', 'Properties'])
                
                for connection in self.connections:
                    properties_str = json.dumps(connection.properties or {}, ensure_ascii=False)
                    connection_writer.writerow([
                        connection.connection_id,
                        connection.from_feature,
                        connection.to_feature,
                        connection.connection_type,
                        properties_str
                    ])
            
            return True
        except Exception as e:
            print(f"Failed to export CSV: {e}")
            return False

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 创建IndoorGML生成器
    generator = IndoorGMLGenerator()
    
    # 设置元数据
    metadata = {
        "creation_date": datetime.utcnow().isoformat(),
        "creator": "IndoorGML Generator",
        "version": "1.0",
        "description": "Sample indoor navigation map"
    }
    generator.set_metadata(metadata)
    
    # 示例站点数据
    site_data = {
        "site_id": "SCENE_A_MS",
        "name": "Maker Space Scene A",
        "description": "Indoor navigation test environment",
        "type": "laboratory",
        "floor_count": 1,
        "total_area": 150.0
    }
    
    # 示例地标数据
    landmarks = [
        {
            "id": "entrance",
            "name": "Entrance",
            "description": "Main entrance to the space",
            "type": "entrance",
            "accessibility": True,
            "importance": "high",
            "site_id": "SCENE_A_MS",
            "geometry": {
                "type": "Point",
                "coordinates": [[0.0, 0.0, 0.0]],
                "srs_name": "EPSG:4326"
            }
        },
        {
            "id": "3d_printer",
            "name": "3D Printer Area",
            "description": "3D printing workspace",
            "type": "workstation",
            "accessibility": True,
            "importance": "medium",
            "site_id": "SCENE_A_MS",
            "geometry": {
                "type": "Point",
                "coordinates": [[5.0, 0.0, 0.0]],
                "srs_name": "EPSG:4326"
            }
        }
    ]
    
    # 示例连接数据
    connections = [
        {
            "id": "entrance_to_3d_printer",
            "from": "entrance",
            "to": "3d_printer",
            "type": "adjacent",
            "distance": 5.0,
            "direction": "east"
        }
    ]
    
    # 生成IndoorGML
    gml_content = generator.generate_indoor_gml(site_data, landmarks, connections)
    
    # 验证标准合规性
    validation_results = generator.validate_standard_compliance(gml_content)
    
    print("IndoorGML Generation Results:")
    print(f"Generated content length: {len(gml_content)} characters")
    print(f"Validation passed: {validation_results['valid']}")
    print(f"Compliance score: {validation_results['compliance_score']:.2f}")
    
    if validation_results['errors']:
        print("\nErrors:")
        for error in validation_results['errors']:
            print(f"  - {error}")
    
    if validation_results['warnings']:
        print("\nWarnings:")
        for warning in validation_results['warnings']:
            print(f"  - {warning}")
    
    if validation_results['recommendations']:
        print("\nRecommendations:")
        for rec in validation_results['recommendations']:
            print(f"  - {rec}")
    
    # 导出文件
    generator.export_to_json("indoor_map.json")
    generator.export_to_csv("indoor_map.csv")
    
    print("\nFiles exported: indoor_map.json, indoor_map.csv")

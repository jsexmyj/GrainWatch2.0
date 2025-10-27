import json
import os
from typing import Any, Dict
import geopandas as gpd
from utils.logger import get_logger

logger = get_logger("geojson_handler")

def load_geojson(input_geojson: Any) -> Dict:
    '''加载 GeoJSON 数据，支持字符串、字典和本地文件路径格式'''
    if isinstance(input_geojson, str):
        # 如果是文件路径，尝试加载文件内容
        try:
            with open(input_geojson, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果不是文件路径，尝试解析为 JSON 字符串
            return json.loads(input_geojson)
    if isinstance(input_geojson, dict):
        return input_geojson
    raise ValueError("geojson must be a str, dict, or a valid file path")

def save_geojson(gdf: gpd.GeoDataFrame, output_path: str):
    """
    将 GeoDataFrame 保存为 GeoJSON 文件。

    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise ValueError("输入必须是 GeoDataFrame 对象")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    gdf.to_file(output_path, driver="GeoJSON")
    return output_path
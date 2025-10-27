import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.vector.buffer import buffer_geojson
from utils.geojson_handler import load_geojson
from config.config import ConfigManager

# 初始化配置管理器
ConfigManager.load_config("config/config.yaml")

# geojson = load_geojson(r"data\uploads\多个shp\多个shp_3857.geojson")
# print(geojson)

buffer = buffer_geojson.invoke(
    {"geojson_input": r"data\uploads\多个shp\多个shp_3857.geojson", "distance": 10}
)
print(buffer)

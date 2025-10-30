import os
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.vector.union import union_core
from service.tool_manager import ToolManager
from config.config import ConfigManager

# 初始化配置管理器
ConfigManager.load_config("config/config.yaml")

input_paths = [
    Path(r"data\uploads\土地利用\土地利用_3857.shp"),
    Path(r"data\uploads\buffers\土地利用_buffer.shp"),
]
save_path, geojson = union_core(input_paths)
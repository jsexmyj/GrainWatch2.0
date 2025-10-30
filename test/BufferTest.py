import os
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service.tool_manager import ToolManager
from config.config import ConfigManager

# 初始化配置管理器
ConfigManager.load_config("config/config.yaml")

shp_path = r"data\uploads\多个shp\土地利用.shp"
save_path, geojson = ToolManager.buffer_tool.invoke(
    {
        "input_path": Path(shp_path),
        "distance": 50,
        "unit": "meters",
    }
)
print(save_path)

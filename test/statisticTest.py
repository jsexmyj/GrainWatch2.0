import os
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.strategies.path_strategy import ChangeAnalyzePathStrategy
from config.config import ConfigManager
from tools.vector.statistics.change_analyze import (
    ChangeAnalyzeTool,
    change_analyze_core,
)


# 初始化配置管理器
ConfigManager.load_config("config/config.yaml")
union_path = Path(r"data\uploads\unions\土地利用_3857_土地利用_buffer_union_2.shp")
change_tool = ChangeAnalyzeTool(ChangeAnalyzePathStrategy())
out_path, geojson = change_tool.execute(input_paths=[union_path])
print(out_path)

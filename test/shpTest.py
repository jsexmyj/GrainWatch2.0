import os
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service.tool_manager import ToolManager
from config.config import ConfigManager

# 初始化配置管理器
ConfigManager.load_config("config/config.yaml")
tool_manager = ToolManager()

shp_path = [
    r"data\uploads\unions\土地利用_3857_土地利用_buffer_union_1.shp",
    r"data\uploads\unions\土地利用_3857_土地利用_buffer_union_2.shp",
    r'data\uploads\unions\Union.shp',
    r'data\uploads\vectors\Union_change_5_cal.shp'
]

# # 获取变化分析工具
# change_tool = tool_manager._tools["change_analyze"]
# # 直接调用工具实例的execute方法
# change_path, geojson = change_tool.execute(
#     input_paths=[Path(shp_path[2])], save_path=None,  # None会触发策略生成默认路径
# )
# print(f"变化分析完成，结果保存在: {change_path}")

# # 计算面积
# caculte_tool = tool_manager._tools["calculate_filed"]
# cal_path, cal_geojson = caculte_tool.execute(
#     input_paths=[Path(change_path)],
#     mode="area",
#     save_path=None,
# )
# print(f"计算面积完成，结果保存在: {cal_path}")

# 统计面积
aggregate_tool = tool_manager._tools["aggregate_group"]
agg_path, agg_geojson = aggregate_tool.execute(
    input_paths=[Path(shp_path[3])],
    mode="area",
    group_field="changed",
    save_path=None,
)
print(f"统计面积完成，结果保存在: {agg_path}")

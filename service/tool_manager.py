from pathlib import Path
import geopandas as gpd
from shapely import make_valid
from config.config import ConfigManager
from langchain_core.tools import tool
from utils.file_handler import get_unique_filename
from tools.vector.buffer import buffer_core
from utils.crs_validator import CRSValidator
from utils.logger import get_logger

logger = get_logger("工具管理器")


class ToolManager:
    def __init__(self):
        pass

    @staticmethod
    @tool
    def buffer(
        input_path: Path,
        save_path: Path = None,
        distance: float = 10,
        unit="meters",
        target_crs: str = None,
    ):
        """对输入的矢量数据进行缓冲区处理。
        Args:
            input_path: 输入矢量数据的路径。
            save_path: 处理后数据的保存路径。如果未提供，则保存到默认目录。
            distance: 缓冲区距离，默认为10。
            unit: 距离单位，默认为米（meters）。
            target_crs: 目标坐标系，默认为EPSG:3857。
        Returns:
            save_path: 处理后数据的保存路径。
            geojson: 处理后的数据可视化的 GeoJSON。
        """

        save_path, geojson = buffer_core(
            input_path,
            distance,
            unit,
            target_crs,
            save_path,
        )

        return str(save_path), geojson

    def get_tool_lists(self):
        """获取工具列表，供 LangChain Agent 使用"""
        tools = [self.buffer]
        return tools

from pathlib import Path
from typing import Optional
import geopandas as gpd
from shapely import make_valid
from config.config import ConfigManager
from langchain_core.tools import tool
from tools.vector.union import union_core
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
    def buffer_tool(
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

    @staticmethod
    @tool
    def union_tool(
        input_paths: list[Path],
        keep_fid: Optional[bool] = True,
        save_path: Path = None,
    ):
        """
        对多个矢量数据进行合并(union)处理

        Args:
            input_paths (List[Path]): 输入矢量数据路径列表，至少需要两个文件
            keep_fid (bool): 是否保留原始 FID 字段，默认为 True,以便后续执行数据来源追踪
            save_path (Optional[Path]): 处理后数据的保存路径。如果未提供，则保存到默认目录

        Returns:
            Tuple[Path, str]: 保存路径和GeoJSON格式的结果

        Raises:
            ValueError: 当输入文件少于2个时
            Exception: 当读取文件或处理数据过程中出现错误时

        Example:
            >>> paths = [Path("data1.shp"), Path("data2.shp")]
            >>> save_path, geojson = union_core(paths)
        """
        save_path, geojson = union_core(
            input_paths=input_paths, keep_fid=keep_fid, save_path=save_path
        )
        return str(save_path), geojson

    def get_tool_lists(self):
        """获取工具列表，供 LangChain Agent 使用"""
        tools = [self.buffer_tool, self.union_tool]
        return tools

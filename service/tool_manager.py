from pathlib import Path
from typing import List, Literal, Optional
import geopandas as gpd
from shapely import make_valid
from config.config import ConfigManager
from langchain_core.tools import tool
from tools.strategies.path_strategy import (
    AggregateGroupPathStrategy,
    BufferPathStrategy,
    CalculateFieldPathStrategy,
    ChangeAnalyzePathStrategy,
    UnionPathStrategy,
)
from tools.vector.statistics.aggregate_group import AggregateGroupTool
from tools.vector.statistics.calculate_geo import CalculateGeoAttributesTool
from tools.vector.statistics.change_analyze import ChangeAnalyzeTool
from tools.vector.union import UnionTool, union_core
from tools.vector.buffer import BufferTool, buffer_core
from utils.crs_validator import CRSValidator
from utils.logger import get_logger

logger = get_logger("工具管理器")


class ToolManager:
    def __init__(self):
        self._tools = {}
        self._register_tools()

    def _register_tools(self):
        """注册所有工具"""
        self._tools["buffer"] = BufferTool(BufferPathStrategy())
        self._tools["union"] = UnionTool(UnionPathStrategy())
        self._tools["change_analyze"] = ChangeAnalyzeTool(
            ChangeAnalyzePathStrategy(),
        )
        self._tools["calculate_filed"] = CalculateGeoAttributesTool(
            CalculateFieldPathStrategy()
        )
        self._tools["aggregate_group"] = AggregateGroupTool(
            AggregateGroupPathStrategy()
        )

    def get_tool_lists(self) -> list:
        """获取工具列表，供 LangChain Agent 使用"""
        tools = [
            self._create_buffer_tool,
            self._create_union_tool,
            self._create_change_analyze_tool,
            self._create_calculate_field_tool,
            self._create_aggregate_group_tool,
        ]
        return tools

    def _create_buffer_tool(self):
        """创建 buffer 工具函数"""
        buffer_instance = self._tools["buffer"]

        @tool
        def buffer_tool(
            input_path: str,
            save_path: str = None,
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

            return buffer_instance.execute(
                input_paths=[Path(input_path)],
                distance=distance,
                unit=unit,
                target_crs=target_crs,
                save_path=Path(save_path),
            )

        return buffer_tool

    def _create_union_tool(self):
        """创建 union 工具函数"""
        union_instance = self._tools["union"]

        @tool
        def union_tool(
            input_paths: list[str],
            keep_fid: Optional[bool] = True,
            save_path: str = None,
        ) -> tuple[str, str]:
            """
            对多个矢量数据进行合并(union)处理

            Args:
                input_paths (List[Path]): 输入矢量数据路径列表，至少需要两个文件
                keep_fid (bool): 是否保留原始 FID 字段，默认为 True,之后每个数据都会保留唯一FID，如FID_1、FID_2、FID_3...
                save_path (Optional[Path]): 处理后数据的保存路径。如果未提供，则保存到默认目录

            Returns:
                Tuple[Path, str]: 保存路径和GeoJSON格式的结果

            Raises:
                ValueError: 当输入文件少于2个时
                Exception: 当读取文件或处理数据过程中出现错误时

            Example:
                >>> paths = ["data1.shp", "data2.shp"]
                >>> save_path, geojson = union_tool(paths)
            """
            return union_instance.execute(
                input_paths=[Path(p) for p in input_paths],
                keep_fid=keep_fid,
                save_path=Path(save_path) if save_path else None,
            )

        return union_tool

    def _create_change_analyze_tool(self):
        change_analyze_instance = self._tools["change_analyze"]

        @tool
        def change_analyze_tool(
            input_paths: list[str],
            before_fid: str = "FID_1",
            after_fid: str = "FID_2",
            change_type_field: str = "changed",
            output_path: str = None,
        ) -> tuple[str, str]:
            """
            分析矢量数据中的变化类型，共有new、lost、unchanged、unknown四种类型。
            args:
                input_paths: 输入矢量数据的路径。
                before_fid: 变化前的FID字段名称，默认为 "FID_1"。
                after_fid: 变化后的FID字段名称，默认为 "FID_2"。
                change_type_field: 变化类型字段名称，默认为 "changed"。
                output_path: 处理后数据的保存路径。如果未提供，则保存到默认目录。
            Returns:
                tuple[str, str]: 保存路径和GeoJSON格式的结果
            Example:
                >>> save_path, geojson = change_analyze_tool(
                        input_paths="data/change_data.shp",
                        before_fid="FID_1",
                        after_fid="FID_2",
                        change_type_field="changed",
                        output_path="data/change_result.shp"
                    )
            """
            return change_analyze_instance.execute(
                input_paths=Path(input_paths[0]),
                before_fid=before_fid,
                after_fid=after_fid,
                change_type_field=change_type_field,
                save_path=Path(output_path),
            )

        return change_analyze_tool

    def _create_calculate_field_tool(self):
        calculate_field_instance = self._tools["calculate_field"]

        @tool
        def calculate_field_tool(
            input_path: list[str],
            output_path: str,
            mode: Literal["area", "length"],
            target_crs: str = None,
            field_name: str = None,
            overwrite: bool = True,
            area_unit: Literal["m2", "km2", "mu"] = "m2",
            length_unit: Literal["m", "km"] = "m",
        ) -> tuple[str, str]:
            """
            计算矢量数据的几何属性（面积或长度）

            Args:
                input_path (Path): 输入矢量文件路径
                output_path (Path): 输出矢量文件路径
                mode (Literal["area", "length"]): 计算模式，"area"表示面积，"length"表示长度
                target_crs (str, optional): 目标坐标系，默认从配置获取或使用EPSG:3857
                field_name (str, optional): 存储计算结果的字段名称，默认使用mode值
                overwrite (bool, optional): 是否覆盖已存在的字段，默认为True
                area_unit (Literal["m2", "km2", "mu"]): 面积单位，默认为"m2"
                length_unit (Literal["m", "km"]): 长度单位，默认为"m"

            Returns:
                tuple: (保存路径, GeoJSON字符串)

            Raises:
                ValueError: 当输入数据为空或mode参数无效时
                TypeError: 当几何类型与计算模式不匹配时
                Exception: 其他未预期的错误
            """
            return calculate_field_instance.execute(
                input_paths=Path(input_path[0]),
                field_name=field_name,
                mode=mode,
                target_crs=target_crs,
                overwrite=overwrite,
                save_path=Path(output_path),
                area_unit=area_unit,
                length_unit=length_unit,
            )

        return calculate_field_tool

    def _create_aggregate_group_tool(self):
        aggregate_group_instance = self._tools["aggregate_group"]

        @tool
        def aggregate_group_tool(
            input_path: list[str],
            output_path: str,
            mode: Literal["area", "length"],
            group_field: str,
            field_name: str = None,
            target_crs: str = None,
            area_unit: Literal["m2", "km2", "mu"] = "m2",
            length_unit: Literal["m", "km"] = "m",
        ) -> tuple[str, str]:
            """
            按字段汇总几何统计结果

            Args:
                input_path (Path): 输入矢量文件路径
                mode (Literal["area", "length"]): 统计模式，"area"表示面积，"length"表示长度
                group_field (str): 分组字段名
                field_name (str, optional): 计算结果字段名称，默认使用mode值
                target_crs (str, optional): 目标坐标系，默认从配置获取或使用EPSG:3857
                area_unit (Literal["m2", "km2", "mu"]): 面积单位，默认为"m2"
                length_unit (Literal["m", "km"]): 长度单位，默认为"m"
                output_path (Path, optional): 保存路径，默认使用配置的默认路径。

            Returns:
                tuple: (保存路径, GeoJSON字符串)

            Raises:
                ValueError: 当mode参数无效、分组字段不存在或计算字段不存在时
            """
            return aggregate_group_instance.execute(
                input_paths=Path(input_path[0]),
                save_path=Path(output_path),
                mode=mode,
                group_field=group_field,
                field_name=field_name,
                target_crs=target_crs,
                area_unit=area_unit,
                length_unit=length_unit,
            )

        return aggregate_group_tool

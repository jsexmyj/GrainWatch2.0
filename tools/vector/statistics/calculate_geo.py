from pathlib import Path
from typing import List, Literal, Tuple
import geopandas as gpd
import pandas as pd
from shapely import make_valid
from config.config import ConfigManager
from tools.vector.base import BaseVectorTool
from utils.crs_validator import CRSValidator
from utils.logger import get_logger

logger = get_logger("change_analyze")


def calculate_core(
    input_path: Path,
    output_path: Path,
    mode: Literal["area", "length"],
    target_crs: str = None,
    field_name: str = None,
    overwrite: bool = True,
    area_unit: Literal["m2", "km2", "mu"] = "m2",
    length_unit: Literal["m", "km"] = "m",
):
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
    try:
        # 获取默认参数
        DEFAULT_OUTPUT_CRS = target_crs or ConfigManager.get("project_crs", "EPSG:3857")
        field_name = field_name or mode.lower()

        # 参数验证
        if mode not in ["area", "length"]:
            raise ValueError("mode 只能是 'area' 或 'length'")

        # 读取数据
        logger.info(f"开始读取数据: {input_path}")
        gdf = gpd.read_file(input_path)

        if gdf.empty:
            raise ValueError("输入数据为空。")

        if not gdf.crs:
            raise ValueError("输入数据缺少坐标系定义。")

        # 修复几何图形
        gdf["geometry"] = gdf["geometry"].apply(make_valid)

        # 检查字段是否已存在且不需要覆盖
        if not overwrite and field_name in gdf.columns:
            logger.warning(f"字段 '{field_name}' 已存在，且未设置覆盖，跳过计算。")
            save_path = gdf.to_file(output_path)
            geojson = gdf.to_json()
            return str(save_path), geojson

        # 坐标系验证和转换
        gdf = CRSValidator.ensure_projected_crs(gdf, DEFAULT_OUTPUT_CRS)
        logger.debug(f"已自动将数据重投影为 {DEFAULT_OUTPUT_CRS}。")

        # 几何类型检查
        geom_types = gdf.geometry.geom_type.unique()
        logger.debug(f"检测到几何类型: {geom_types}")

        if mode == "area" and not any(
            g in ["Polygon", "MultiPolygon"] for g in geom_types
        ):
            raise TypeError("当前数据不是面要素，无法计算面积。")
        if mode == "length" and not any(
            g in ["LineString", "MultiLineString"] for g in geom_types
        ):
            raise TypeError("当前数据不是线要素，无法计算长度。")

        # 执行计算
        if mode == "area":
            gdf[field_name] = gdf.geometry.area
            # 单位转换
            if area_unit == "km2":
                gdf[field_name] /= 1e6
            elif area_unit == "mu":
                gdf[field_name] /= 666.6667
            logger.info(
                f"成功计算面积（单位：{area_unit}），结果存储在字段 '{field_name}' 中"
            )
        elif mode == "length":
            gdf[field_name] = gdf.geometry.length
            # 单位转换
            if length_unit == "km":
                gdf[field_name] /= 1000
            logger.info(
                f"成功计算长度（单位：{length_unit}），结果存储在字段 '{field_name}' 中"
            )

        logger.debug(f"字段 '{field_name}' 计算完成，共 {len(gdf)} 条记录。")
        gdf.to_file(output_path)
        logger.info(f"计算{mode}完成，保存路径: {output_path}")
        geojson = gdf.to_json()
        return str(output_path), geojson

    except FileNotFoundError:
        logger.error(f"输入文件不存在: {input_path}")
        raise
    except ValueError as ve:
        logger.error(f"数据值错误: {ve}")
        raise
    except TypeError as te:
        logger.error(f"数据类型错误: {te}")
        raise
    except Exception as e:
        logger.error(f"计算过程中发生未知错误: {e}")
        raise


# ===== 新增：Calculate_Attributes_Tool 类 =====
class CalculateGeoAttributesTool(BaseVectorTool):
    """CalculateGeoAttributesTool工具类，封装路径管理和业务逻辑调用
    计算每个字段要素的几何属性"""

    def _execute_core(
        self, input_paths: List[Path], save_path: Path, **kwargs
    ) -> Tuple[str, str]:
        # 从 kwargs 提取参数
        mode = kwargs.get("mode", "area")
        target_crs = kwargs.get("target_crs", "EPSG:3857")
        field_name = kwargs.get("field_name", None)
        overwrite = kwargs.get("overwrite", True)
        area_unit = kwargs.get("area_unit", "m2")
        length_unit = kwargs.get("length_unit", "m")

        # 调用核心函数，传入准备好的 save_path
        return calculate_core(
            input_path=input_paths[0],
            output_path=save_path,
            mode=mode,
            target_crs=target_crs,
            field_name=field_name,
            overwrite=overwrite,
            area_unit=area_unit,
            length_unit=length_unit,
        )

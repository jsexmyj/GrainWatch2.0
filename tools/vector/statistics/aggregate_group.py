# 分组统计几何要素工具
import json
from pathlib import Path
from typing import List, Literal, Tuple
import geopandas as gpd
from config.config import ConfigManager
from tools.vector.base import BaseVectorTool
from utils.crs_validator import CRSValidator
from utils.logger import get_logger

logger = get_logger("aggregate_group")


def aggregate_core(
    input_path: Path,
    mode: Literal["area", "length"],
    group_field: str,
    field_name: str = None,
    target_crs: str = None,
    area_unit: Literal["m2", "km2", "mu"] = "m2",
    length_unit: Literal["m", "km"] = "m",
    output_path: Path = None,
):
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
        Tuple[str, str]: 处理后数据的保存路径和可视化的 GeoJSON。

    Raises:
        ValueError: 当mode参数无效、分组字段不存在或计算字段不存在时
    """
    # 参数验证
    if mode not in ["area", "length"]:
        raise ValueError("mode 只能是 'area' 或 'length'")

    # 读取数据
    logger.info(f"开始读取数据: {input_path}")
    gdf = gpd.read_file(input_path)
    if gdf.empty:
        raise ValueError("输入数据为空。")

    group_field = group_field or mode.lower()
    if group_field not in gdf.columns:
        raise ValueError(f"分组字段 '{group_field}' 不存在。")

    # 坐标系验证和转换
    DEFAULT_OUTPUT_CRS = target_crs or ConfigManager.get("project_crs", "EPSG:3857")
    gdf = CRSValidator.ensure_projected_crs(gdf, DEFAULT_OUTPUT_CRS)

    # 检查计算字段是否存在
    field_name = field_name or mode.lower()
    if field_name not in gdf.columns:
        raise ValueError(
            f"计算字段 '{field_name}' 不存在。请先使用 calculate_geo 工具计算几何属性。"
        )

    # 聚合
    df_sum = (
        gdf.groupby(group_field)[field_name]
        .sum()
        .reset_index()
        .rename(columns={field_name: f"{field_name}_sum"})
    )

    # 单位换算
    result_unit = area_unit if mode == "area" else length_unit
    if mode == "area":
        if result_unit == "km2":
            df_sum[f"{field_name}_sum"] /= 1e6
        elif result_unit == "mu":
            df_sum[f"{field_name}_sum"] /= 666.6667
    elif mode == "length":
        if result_unit == "km":
            df_sum[f"{field_name}_sum"] /= 1000

    
    # 优化：后期要保存成表，shp输出就做融合（dissolve工具）
    df_sum.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.debug(f"分组统计{mode}完成，结果保存到: {output_path}")
    
    # 构造轻量级 GeoJSON（无 geometry，仅 properties）
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": None,  # 占位，方便未来扩展
                "properties": row.to_dict()
            }
            for _, row in df_sum.iterrows()
        ]
    }

    geojson_str = json.dumps(geojson, ensure_ascii=False, indent=2)
    return str(output_path), geojson_str

# ===== 新增：AggregateGroupTool 类 =====
class AggregateGroupTool(BaseVectorTool):
    def _execute_core(
        self, input_paths: List[Path], save_path: Path, **kwargs
    ) -> Tuple[str, str]:
        """
        调用 aggregate_core 函数
        """
        # 从 kwargs 提取参数
        mode = kwargs.get("mode", "area")
        group_field = kwargs.get("group_field", None)
        field_name = kwargs.get("field_name", None)
        target_crs = kwargs.get("target_crs", "EPSG:3857")
        area_unit = kwargs.get("area_unit", "m2")
        length_unit = kwargs.get("length_unit", "m")

        return aggregate_core(
            input_path=input_paths[0],
            output_path=save_path,
            mode=mode,
            group_field=group_field,
            field_name=field_name,
            target_crs=target_crs,
            area_unit=area_unit,
            length_unit=length_unit,
        )
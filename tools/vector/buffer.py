import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import geopandas as gpd
from shapely import make_valid
from shapely.geometry import shape, mapping
from utils.crs_validator import CRSValidator
from utils.file_handler import get_unique_filename
from utils.geojson_handler import load_geojson, save_geojson
from utils.logger import get_logger
from config.config import ConfigManager

logger = get_logger("buffer_tool")


def _normalize_unit_to_meters(distance: float, unit: str) -> float:
    """
    将不同单位的距离标准化为米

    Args:
        distance: 距离值
        unit: 单位

    Returns:
        标准化后的米值，如果单位是度则返回NaN
    """
    unit = (unit or ConfigManager.get("buffer.distance_unit", "meters")).strip().lower()
    if unit in ("m", "meter", "meters"):
        return distance
    if unit in ("km", "kilometer", "kilometers"):
        return distance * 1000.0
    if unit in ("ft", "feet"):
        return distance * 0.3048
    if unit in ("mi", "mile", "miles"):
        return distance * 1609.344
    if unit in ("degree", "degrees", "deg"):
        # marker: degrees are not converted to meters; return sentinel
        return float("nan")
    # default assume meters
    return distance


def buffer_core(
    input_path: Path,
    distance: float,
    unit: str = "meters",
    target_crs: str = "EPSG:3857",
    save_path: Path = None,
) -> tuple[str, str]:
    """
    处理缓冲区操作的核心逻辑。
    """
    try:
        # 在函数执行时才读取配置，确保配置已经被加载
        DEFAULT_DISTANCE_UNIT = unit or ConfigManager.get(
            "buffer.distance_unit", "meters"
        )
        DEFAULT_OUTPUT_CRS = target_crs or ConfigManager.get(
            "buffer.output_crs", "EPSG:3857"
        )
        DEFAULT_METRIC_CRS = ConfigManager.get("buffer.metric_crs", "EPSG:3857")

        # Step 1. 读取数据
        gdf = gpd.read_file(input_path)
        gdf["geometry"] = gdf["geometry"].apply(make_valid)

        # Step 2. 验证输入
        if gdf.empty:
            raise ValueError("输入数据为空。")
        if not gdf.crs:
            raise ValueError("输入数据缺少坐标系定义。")
        gdf = CRSValidator.ensure_projected_crs(gdf, DEFAULT_OUTPUT_CRS)
        logger.debug(f"已自动将数据重投影为 {DEFAULT_OUTPUT_CRS}。")

        # Step 3. 计算缓冲区
        meters = _normalize_unit_to_meters(distance, DEFAULT_DISTANCE_UNIT)
        if meters != meters:  # NaN => unit was degrees
            # buffer in degrees directly (no reprojection)
            gdf["geometry"] = gdf.geometry.buffer(distance)
            out_gdf = gdf
        else:
            # 重投影到度量单位的CRS，进行缓冲后再投影回目标CRS
            try:
                gdf_m = gdf.to_crs(DEFAULT_METRIC_CRS)
                gdf_m["geometry"] = gdf_m.geometry.buffer(meters)
                out_gdf = gdf_m.to_crs(DEFAULT_OUTPUT_CRS)
            except Exception as e:
                logger.warning(f"投影转换失败，尝试在原始CRS中缓冲: {e}")
                # fallback: try buffering in original CRS if reprojection fails
                gdf["geometry"] = gdf.geometry.buffer(meters)
                out_gdf = gdf

        logger.info(f"缓冲区处理完成，缓冲距离: {distance} {DEFAULT_DISTANCE_UNIT} 。")

        # Step 4. 保存结果
        if save_path is None:
            save_dir = ConfigManager.get("buffer.BUFFER_DIR", "data/uploads/buffer")
            save_path = get_unique_filename(
                directory=Path(save_dir),
                original_filename=f"{input_path.stem}_buffer.shp",
            )
        else:
            save_path = get_unique_filename(
                directory=save_path.parent, original_filename=save_path.name
            )
        out_gdf.to_file(save_path)
        logger.info(f"缓冲区结果已保存到: {save_path}")

        # Step 5. 生成可视化的 GeoJSON
        geojson = out_gdf.to_json()

        return str(save_path), geojson
    except Exception as e:
        logger.error(f"缓冲区处理失败: {e}")
        raise

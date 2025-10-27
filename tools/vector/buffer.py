import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import geopandas as gpd
from shapely.geometry import shape, mapping
from langchain.tools import tool
from dotenv import load_dotenv
from utils.crs_validator import CRSValidator
from utils.file_handler import get_unique_filename
from utils.geojson_handler import load_geojson, save_geojson
from utils.logger import get_logger
from config.config import ConfigManager

logger = get_logger("buffer_tool")
load_dotenv()

# 默认配置常量
DEFAULT_DISTANCE_UNIT = "meters"
DEFAULT_INPUT_CRS = "EPSG:3857"
DEFAULT_OUTPUT_CRS = "EPSG:3857"
DEFAULT_METRIC_CRS = "EPSG:3857"


def _features_from_geojson(gj: Dict) -> List[Dict]:
    """从 GeoJSON 中提取 feature，支持 FeatureCollection, Feature, 以及单一 Geometry 对象"""
    t = gj.get("type")
    features: List[Dict] = []
    if t == "FeatureCollection":
        features = gj.get("features", [])
    elif t == "Feature":
        features = [gj]
    elif t in (
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
        "GeometryCollection",
    ):
        # raw geometry -> wrap into a Feature without properties
        features = [{"type": "Feature", "geometry": gj, "properties": {}}]
    else:
        raise ValueError(f"Unsupported GeoJSON type: {t}")
    return features


def _normalize_unit_to_meters(distance: float, unit: str) -> float:
    """
    将不同单位的距离标准化为米

    Args:
        distance: 距离值
        unit: 单位

    Returns:
        标准化后的米值，如果单位是度则返回NaN
    """
    unit = (unit or DEFAULT_DISTANCE_UNIT).strip().lower()
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


@tool
def buffer_geojson(
    geojson_input: Union[str, Dict, Path],
    distance: float,
    unit: str = DEFAULT_DISTANCE_UNIT,
    input_crs: str = DEFAULT_INPUT_CRS,
    save_path: Optional[str] = None,
) -> str:
    """
    对输入的 GeoJSON 做缓冲并以 GeoJSON 返回。

    Args:
        geojson_input: 输入的GeoJSON，可以是字符串、字典格式或者本地GeoJSON 文件路径
        distance: 缓冲距离（数值）
        unit: 单位, 支持 "meters" (默认), "km", "feet", "miles", "degrees"
        input_crs: 输入 GeoJSON 的 CRS，默认 "EPSG:3857"（Web Mercator）
        save_path: 缓冲区输出路径，默认为配置文件中的 BUFFER_DIR

    Returns:
        缓冲区输出文件路径

    Raises:
        ValueError: 当输入GeoJSON类型不支持时
        Exception: 其他处理过程中可能发生的异常
    """
    try:
        gj = load_geojson(geojson_input)
        features = _features_from_geojson(gj)
        records = []
        for feat in features:
            geom = feat.get("geometry")
            props = feat.get("properties", {}) or {}
            if geom is None:
                # skip empty geometry
                continue
            geom_shape = shape(geom)
            records.append({**props, "geometry": geom_shape})

        if not records:
            # return empty FeatureCollection
            result = json.dumps(
                {"type": "FeatureCollection", "features": []}, ensure_ascii=False
            )
            logger.warning("输入GeoJSON为空，返回空的FeatureCollection")
            return result

        gdf = gpd.GeoDataFrame(records, geometry="geometry")
        # set input CRS if provided; default to EPSG:3857
        try:
            gdf = gdf.set_crs(input_crs, allow_override=True)
        except Exception as e:
            logger.warning(
                f"设置输入CRS失败: {input_crs}, 使用默认值: {DEFAULT_INPUT_CRS}, 错误: {e}"
            )
            # fallback: try EPSG:3857
            gdf = gdf.set_crs(DEFAULT_INPUT_CRS, allow_override=True)

        meters = _normalize_unit_to_meters(distance, unit)

        if meters != meters:  # NaN => unit was degrees
            # buffer in degrees directly (no reprojection)
            gdf["geometry"] = gdf.geometry.buffer(distance)
            out_gdf = gdf
        else:
            # buffer in meters: reproject to a metric CRS (Web Mercator), buffer, then back
            try:
                gdf_m = gdf.to_crs(DEFAULT_METRIC_CRS)
                gdf_m["geometry"] = gdf_m.geometry.buffer(meters)
                out_gdf = gdf_m.to_crs(DEFAULT_OUTPUT_CRS)
            except Exception as e:
                logger.warning(f"投影转换失败，尝试在原始CRS中缓冲: {e}")
                # fallback: try buffering in original CRS if reprojection fails
                gdf["geometry"] = gdf.geometry.buffer(meters)
                out_gdf = gdf

        # 处理保存路径
        if save_path is None:
            save_dir = ConfigManager.get("BUFFER_DIR", "data/uploads/buffers")
            save_path = get_unique_filename(
                directory=Path(save_dir), original_filename="buffer_output.geojson"
            )

        buffer_path = save_geojson(out_gdf, output_path=str(save_path))
        logger.info(
            f"缓冲区输出成功！缓冲距离: {distance} {unit}, 输入CRS: {input_crs}, 输出CRS: {out_gdf.crs}"
        )
        return buffer_path
    except Exception as e:
        logger.error(f"缓冲区处理失败: {e}")
        raise

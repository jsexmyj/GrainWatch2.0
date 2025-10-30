from pathlib import Path
import geopandas as gpd
import pandas as pd
from utils.logger import get_logger

logger = get_logger("change_analyze")


def _get_change_type(row, before_field, after_field):
    has_before = not pd.isna(row.get(before_field))
    has_after = not pd.isna(row.get(after_field))
    if has_before and has_after:
        return "unchanged"
    elif has_before and not has_after:
        return "lost"
    elif not has_before and has_after:
        return "new"
    else:
        return "unknown"


def change_analyze_core(
    path: Path,
    before_fid: str = "FID_1",
    after_fid: str = "FID_2",
    output_path: Path = None,
) -> Path:
    gdf = gpd.read_file(path)

    if before_fid not in gdf.columns or after_fid not in gdf.columns:
        logger.error(f"输入文件缺少必要字段：{before_fid}, {after_fid}")
        raise ValueError(f"输入文件缺少必要字段：{before_fid}, {after_fid}")
    
    gdf["change_type"] = gdf.apply(_get_change_type, axis=1,before_field=before_fid, after_field=after_fid)

    # 默认保存路径
    if output_path is None:
        output_path = path.with_stem(path.stem + "_change")

    gdf.to_file(output_path)
    logger.info(f"变化分析完成，结果保存到: {output_path}")
    return output_path

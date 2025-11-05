from pathlib import Path
from typing import List, Tuple
import geopandas as gpd
import pandas as pd
from tools.vector.base import BaseVectorTool
from utils.logger import get_logger

logger = get_logger("change_analyze")


def _get_change_type(row, before_field, after_field):
    val_before = row.get(before_field, 0)
    val_after = row.get(after_field, 0)
    has_before = val_before != 0
    has_after = val_after != 0
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
    change_type_field: str = "change_type",
    output_path: Path = None,
) -> Path:

    gdf = gpd.read_file(path)

    if before_fid not in gdf.columns or after_fid not in gdf.columns:
        logger.error(f"输入文件缺少必要字段：{before_fid}, {after_fid}")
        raise ValueError(f"输入文件缺少必要字段：{before_fid}, {after_fid}")

    gdf[change_type_field] = gdf.apply(
        _get_change_type, axis=1, before_field=before_fid, after_field=after_fid
    )

    gdf.to_file(output_path)
    logger.info(f"变化分析完成，结果保存到: {output_path}")
    geojson = gdf.to_json()
    return str(output_path), geojson


# ===== 新增：ChangeAnalyzeTool 类 =====
class ChangeAnalyzeTool(BaseVectorTool):
    """ChangeAnalyze工具类，封装路径管理和业务逻辑调用"""

    def _execute_core(
        self, input_paths: List[Path], save_path: Path, **kwargs
    ) -> Tuple[str, str]:
        """
        调用 change_analyze_core 函数

        Args:
            input_paths: 输入路径列表（change_analyze只需要一个）
            save_path: 已准备好的保存路径
            **kwargs: before_fid, after_fid 等参数
        """
        # 从 kwargs 提取参数
        before_fid = kwargs.get("before_fid", "FID_1")
        after_fid = kwargs.get("after_fid", "FID_2")
        change_type_field = kwargs.get("change_type_field", "changed")

        # 调用核心函数，传入准备好的 save_path
        return change_analyze_core(
            path=input_paths[0],
            before_fid=before_fid,
            after_fid=after_fid,
            change_type_field=change_type_field,
            output_path=save_path,
        )

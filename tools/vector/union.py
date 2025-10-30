import geopandas as gpd
from pathlib import Path
from typing import List, Tuple, Optional
from utils.file_handler import ensure_folder_exists, get_unique_filename
from utils.logger import get_logger
from config.config import ConfigManager

logger = get_logger("union_tool")


def union_core(
    input_paths: List[Path], keep_fid: bool = True, save_path: Optional[Path] = None
) -> Tuple[Path, str]:
    if not input_paths or len(input_paths) < 2:
        logger.error("至少需要两个输入文件进行合并")
        raise ValueError("至少需要两个输入文件进行合并。")

    try:
        # 保存路径确认存在
        if save_path is None:
            save_dir = Path(ConfigManager.get("UNION_DIR", "data/uploads/unions"))
            ensure_folder_exists(save_dir)
            save_path = get_unique_filename(
                directory=save_dir,
                original_filename=f"{input_paths[0].stem}_{input_paths[1].stem}_union.shp",
            )
        else:
            ensure_folder_exists(save_path.parent)  # 确保保存目录存在
            save_path = get_unique_filename(
                directory=save_path.parent, original_filename=save_path.name
            )

        # 读取所有图层
        layers = []
        for i, path in enumerate(input_paths):
            logger.debug(f"正在读取第{i+1}个图层: {path}")
            layer = gpd.read_file(path)
            # 添加 FID 字段以区分来源
            if keep_fid:
                fid_field = f"FID_{i+1}"
                if fid_field not in layer.columns:
                    layer[fid_field] = layer.index + 1  # 从1开始编号,避免与0混淆
            layers.append(layer)
        logger.info(f"成功读取{len(layers)}个图层，开始合并操作")

        result = layers[0]
        # 依次合并图层
        for i, layer in enumerate(layers[1:]):
            logger.debug(f"正在合并第{i+2}个图层")
            result = gpd.overlay(result, layer, how="union", keep_geom_type=True)
            dropped_count = len(layer) - len(result)
            if dropped_count > 0:
                logger.warning(
                    f"⚠️ {dropped_count} 个几何被丢弃（非 Polygon 类型）。如需保留，请设置 keep_geom_type=False。"
                )

        # 保存结果
        result.to_file(save_path)
        logger.info(f"合并完成，结果保存到: {save_path}")

        geojson = result.to_json()
        return save_path, geojson

    except Exception as e:
        logger.error(f"合并操作失败: {str(e)}")
        raise

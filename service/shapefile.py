import json
from pathlib import Path
import geopandas as gpd
from utils.crs_validator import CRSValidator
from utils.file_handler import extract_zip
from utils.logger import get_logger
logger = get_logger("ShapefileService")


def validate_shapefile_components(folder: Path) -> Path:
    """
    检查文件夹内是否存在.shp, .shx, .prj, .dbf
    返回 .shp 文件路径
    """
    shp_files = list(folder.glob("*.shp"))
    if not shp_files:
        raise ValueError("未找到 .shp 文件")
    shp_path = shp_files[0]
    required_ext = [".shx", ".prj", ".dbf"]
    for ext in required_ext:
        if not (folder / (shp_path.stem + ext)).exists():
            raise ValueError(f"缺少 {ext} 文件")
    return shp_path

class ShapefileService:
    """
    处理上传的ZIP文件，验证是否有合法的shapefile，并返回处理结果
    1. 解压ZIP文件
    2. 验证shapefile组成
    3. 读取shapefile
    4、判断坐标系并统一为4326
    5. 转为GeoJSON返回前端
    6. 转换为3857并保存到本地
    7. 返回结果
    """

    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir

    def process_zip(self, zip_path: Path):
        try: 
            logger.debug("开始处理ZIP文件")
            # 1. 解压
            extract_dir = zip_path.with_suffix('')
            extract_path = extract_zip(zip_path, extract_dir)

            # 2. 验证 shapefile 组成
            shp_path = validate_shapefile_components(extract_path)
            logger.debug(f"找到 shapefile: {shp_path}")

            # 3. 读取 shapefile
            gdf = gpd.read_file(shp_path)

            # 4. 判断坐标系并统一为4326
            gdf_4326 = CRSValidator.ensure_crs_4326(gdf)

            # 5. 转为GeoJSON返回前端
            geojson_str = gdf_4326.to_json()
            geojson = json.loads(geojson_str)

            # 6. 转换为3857并存储本地
            gdf_3857 = CRSValidator.to_3857(gdf_4326)
            output_path = self.upload_dir / f"{zip_path.stem}_3857.geojson"
            gdf_3857.to_file(output_path, driver="GeoJSON")

            logger.info(f"ZIP文件处理完成, 结果保存至 {output_path}")
            # 7. 返回GeoJSON和文件路径
            return {
                "geojson": geojson,
                "local_path": str(output_path)
            }
        except Exception as e:
            logger.error(f"处理ZIP文件时出错: {str(e)}")
            raise ValueError(f"处理ZIP文件时出错: {str(e)}")
        
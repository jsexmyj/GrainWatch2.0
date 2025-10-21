from shapely import Polygon
from shapely.ops import transform
import pyproj
from utils.logger import get_logger

logger = get_logger("CRSValidator")


class CRSValidator:
    @staticmethod
    def crs_equal(crs1, crs2) -> bool:
        """
        判断两个 CRS 是否等价（可以是 EPSG 字符串、整数或 rasterio.CRS 对象）
        """
        try:
            return pyproj.CRS.from_user_input(crs1) == pyproj.CRS.from_user_input(crs2)
        except Exception as e:
            logger.error(f"CRS 比较失败: {e}", exc_info=True)
            return False

    @staticmethod
    def ensure_crs_4326(gdf):
        if gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        return gdf

    @staticmethod
    def to_3857(gdf):
        return gdf.to_crs(epsg=3857)

    @staticmethod
    def get_epsg_code(crs_input) -> str:
        """
        接受 EPSG 字符串、整数、rasterio.CRS 或 WKT 字符串，统一转为 EPSG:xxxx 格式。

        Returns:
            标准 EPSG 字符串，如 'EPSG:32650'
        """
        try:
            crs = pyproj.CRS.from_user_input(crs_input)
            epsg = crs.to_epsg()
            if epsg:
                return f"EPSG:{epsg}"
            else:
                logger.warning(f"无法识别 EPSG 编码，返回原始 WKT: {crs_input}")
                return crs.to_wkt()
        except Exception as e:
            logger.error(f"CRS 转 EPSG 失败: {e}", exc_info=True)
            raise

# 路径生成策略
# 用于对不同类型的路径生成进行策略定义，有通用策略和矢量策略两层
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from config.config import ConfigManager


class PathStrategy(ABC):
    """路径生成策略基类，定义通用接口"""

    @abstractmethod
    def get_default_filename(self, input_paths: List[Path]) -> str:
        """生成默认文件名"""
        pass


class VectorPathStrategy(PathStrategy):
    """矢量类工具的路径策略基类，本身已经继承了get_default_filename接口"""

    def get_default_vector_dir(self) -> Path:
        """获取默认矢量数据保存目录"""
        path = Path(ConfigManager.get("vector_dir","data/upload/vector"))
        return path


# -----------------Concrete Strategy Classes 矢量类工具路径策略类---------------------
class BufferPathStrategy(VectorPathStrategy):
    """Buffer工具的路径策略"""

    def get_default_dir(self) -> Path:
        return self.get_default_vector_dir()

    def get_default_filename(self, input_paths: List[Path]) -> str:
        return f"{input_paths[0].stem}_buffer.shp"


class UnionPathStrategy(VectorPathStrategy):
    """Union工具的路径策略"""

    def get_default_dir(self) -> Path:
        return self.get_default_vector_dir()

    def get_default_filename(self, input_paths: List[Path]) -> str:
        return f"{input_paths[0].stem}_union.shp"


class BufferPathStrategy(VectorPathStrategy):
    """Buffer工具的路径策略"""

    def get_default_dir(self) -> Path:
        return self.get_default_vector_dir()

    def get_default_filename(self, input_paths: List[Path]) -> str:
        if len(input_paths) >= 2:
            return f"{input_paths[0].stem}_{input_paths[1].stem}_union.shp"
        return f"{input_paths[0].stem}_union.shp"


class ChangeAnalyzePathStrategy(VectorPathStrategy):
    """ChangeAnalyze工具的路径策略"""

    def get_default_dir(self) -> Path:
        return self.get_default_vector_dir()

    def get_default_filename(self, input_paths: List[Path]) -> str:
        return f"{input_paths[0].stem}_change.shp"


class CalculateFieldPathStrategy(VectorPathStrategy):
    """ChangeAnalyze工具的路径策略"""

    def get_default_dir(self) -> Path:
        return self.get_default_vector_dir()

    def get_default_filename(self, input_paths: List[Path]) -> str:
        return f"{input_paths[0].stem}_cal.shp"

class AggregateGroupPathStrategy(VectorPathStrategy):
    """AggregateGroup工具的路径策略"""
    def get_default_dir(self) -> Path:
        return self.get_default_vector_dir()
    def get_default_filename(self, input_paths: List[Path]) -> str:
        return f"{input_paths[0].stem}_aggre.csv"
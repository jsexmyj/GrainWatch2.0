from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple, Callable
from tools.strategies.path_strategy import VectorPathStrategy
from utils.file_handler import ensure_folder_exists, get_unique_filename
from utils.logger import get_logger

logger = get_logger("vector_base")


class BaseVectorTool(ABC):
    """
    向量工具基类

    职责：
    1. 统一路径管理逻辑（通过策略模式）
    2. 定义工具执行流程模板
    3. 委托具体业务逻辑给 *_core 函数
    """

    def __init__(self, path_strategy: VectorPathStrategy):
        """
        Args:
            path_strategy: 路径生成策略实例
        """
        self.path_strategy = path_strategy

    def execute(
        self, input_paths: List[Path], save_path: Optional[Path] = None, **kwargs
    ) -> Tuple[str, str]:
        """
        执行工具的统一流程

        Args:
            input_paths: 输入文件路径列表
            save_path: 保存路径（可选）
            **kwargs: 传递给 core_function 的其他参数

        Returns:
            Tuple[str, str]: (保存路径, GeoJSON字符串)
        """
        # 准备保存路径
        prepared_save_path = self._prepare_save_path(input_paths, save_path)

        # 调用核心业务函数
        save_path, geojson = self._execute_core(
            input_paths, prepared_save_path, **kwargs
        )

        return save_path, geojson

    def _prepare_save_path(self, input_paths, save_path):
        """统一的路径准备逻辑"""
        if save_path is None:
            save_dir = self.path_strategy.get_default_dir()
            ensure_folder_exists(save_dir)
            filename = self.path_strategy.get_default_filename(input_paths)
            save_path = get_unique_filename(save_dir, filename)
        else:
            ensure_folder_exists(save_path.parent)
            save_path = get_unique_filename(save_path.parent, save_path.name)
        return save_path

    @abstractmethod
    def _execute_core(
        self, input_paths: List[Path], save_path: Path, **kwargs
    ) -> Tuple[str, str]:
        """
        调用具体的 *_core 函数执行业务逻辑

        子类需要实现此方法，调用对应的 core 函数

        Args:
            input_paths: 输入文件路径列表
            save_path: 已准备好的保存路径
            **kwargs: 其他参数

        Returns:
            Tuple[str, str]: (保存路径, GeoJSON字符串)
        """
        pass
import tempfile
import os
from datetime import datetime

from config.config import ConfigManager


# 全局变量，用于存储会话临时根目录
_SESSION_TEMP_ROOT = None


def _get_session_temp_root():
    """获取或创建会话临时根目录"""
    global _SESSION_TEMP_ROOT
    if _SESSION_TEMP_ROOT is None:
        PROGRAM_START_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")
        CONFIG_TEMP_DIR = ConfigManager.get("temp_dir") or tempfile.gettempdir()
        _SESSION_TEMP_ROOT = os.path.join(CONFIG_TEMP_DIR, f"{PROGRAM_START_TIME}")
        os.makedirs(_SESSION_TEMP_ROOT, exist_ok=True)
    return _SESSION_TEMP_ROOT


def mkd_temp(prefix="tmp", suffix="", dir=None):
    """
    创建临时子文件夹,可以选择在指定目录下创建

    :param prefix: 子文件夹名称前缀
    :param suffix: 子文件夹名称后缀
    :param dir: 若指定子目录，则在该子目录下创建（可选）
    :return: 创建的临时目录路径
    """
    base_dir = dir if dir else _get_session_temp_root()
    os.makedirs(base_dir, exist_ok=True)
    return tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=base_dir)


def cleanup_all():
    """
    清理整个 SESSION_TEMP_ROOT 目录（慎用）
    """
    session_root = _get_session_temp_root()
    if os.path.exists(session_root):
        import shutil

        shutil.rmtree(session_root)

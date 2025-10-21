import os
from pathlib import Path
import zipfile
from utils.logger import get_logger

logger = get_logger("file_handler")


def ensure_folder_exists(folder_path):
    """
    验证文件夹路径是否为空，如果文件夹路径为空，则创建文件夹
    """
    if not folder_path:
        raise ValueError("文件夹路径不能为空")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def ensure_file_exists(file_path):
    """
    验证文件路径是否为空，如果文件路径为空，则创建文件
    """
    ensure_folder_exists(os.path.dirname(file_path))
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            pass
    return file_path


def get_unique_filename(directory: Path, original_filename: str) -> Path:
    """
    生成唯一的文件名，如果文件已存在，则添加_{n}后缀，n从1开始递增

    Args:
        directory: 目标目录
        original_filename: 原始文件名

    Returns:
        Path: 唯一的文件路径
    """
    base_name = Path(original_filename).stem
    extension = Path(original_filename).suffix
    counter = 1
    new_filename = original_filename
    file_path = directory / new_filename

    while file_path.exists():
        new_filename = f"{base_name}_{counter}{extension}"
        file_path = directory / new_filename
        counter += 1

    return file_path


def extract_zip(zip_path: Path, extract_to: Path) -> Path:
    """解压ZIP文件到指定目录
    Args:
        zip_path: ZIP文件路径
        extract_to: 解压目标目录
    Returns:
    Path: 解压后的目录路径
    """
    extract_to.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # 处理中文文件名编码问题
        for info in zf.infolist():
            # 使用UTF-8解码文件名
            info.filename = info.filename.encode("cp437", errors="ignore").decode(
                "gbk", errors="ignore"
            )

            # 确保目标路径安全，防止路径遍历攻击
            target_path = extract_to / info.filename
            resolved_target = target_path.resolve()
            resolved_extract = extract_to.resolve()

            if resolved_target.is_relative_to(resolved_extract):
                zf.extract(info, resolved_extract)

    # 查找解压后的实际目录
    extracted_items = list(extract_to.iterdir())
    if len(extracted_items) == 1 and extracted_items[0].is_dir():
        result_path = extracted_items[0]
    else:
        result_path = extract_to

    logger.info(f"解压完成：{zip_path} -> {result_path}")
    return result_path

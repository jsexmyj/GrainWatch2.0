import os
import shutil
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
    """解压ZIP文件，处理中文编码和文件名冲突，并返回实际解压目录。

    Args:
        zip_path: ZIP文件路径
        extract_to: 解压操作的根目录

    Returns:
        Path: 本次解压操作创建的实际目录路径。
    """
    # 1. 确定解压目录名（基于zip文件名），并处理重名
    dir_name = zip_path.stem
    # get_unique_filename 会找到一个不存在的路径，我们用它作为新目录
    actual_extract_dir = get_unique_filename(extract_to, dir_name)

    # 2. 创建实际的解压目录
    actual_extract_dir.mkdir(parents=True, exist_ok=True)
    resolved_extract_dir = actual_extract_dir.resolve()

    def decode_filename(raw_name: bytes) -> str:
        """尝试用GBK和UTF-8解码文件名"""
        try:
            return raw_name.decode('gbk')
        except UnicodeDecodeError:
            return raw_name.decode('utf-8', errors='ignore')

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            # 3. 处理中文文件名
            # zipfile 默认使用 cp437, 我们需要先编码回 bytes 再用正确编码解码
            file_name = decode_filename(member.filename.encode('cp437'))

            # 4. 确保路径安全，防止目录穿越
            target_path = (resolved_extract_dir / file_name).resolve()
            if not target_path.is_relative_to(resolved_extract_dir):
                logger.warning(f"跳过不安全路径: {file_name}")
                continue

            # 5. 解压
            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                # 确保父目录存在
                target_path.parent.mkdir(parents=True, exist_ok=True)
                # 从zip中读取并写入新文件
                with zf.open(member) as source, open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)

    actual_extractor_path = actual_extract_dir / dir_name
    logger.info(f"解压完成: '{zip_path}' -> '{actual_extractor_path}'")
    # 6. 返回实际创建的解压目录
    return actual_extractor_path


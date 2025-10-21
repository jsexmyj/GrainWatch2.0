import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
from service.shapefile import ShapefileService
from utils.file_handler import get_unique_filename
from dotenv import load_dotenv
from utils.logger import get_logger
from utils.tempfile import mkd_temp, mkd_tempdir

load_dotenv()
logger = get_logger("upload_router")
router = APIRouter()

upload_dir = os.getenv("UPLOAD_DIR", "data/uploads")
service = ShapefileService(Path(upload_dir))


@router.post("/upload")
async def upload_zip(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持上传ZIP文件")

    # 保存上传文件到一个临时子目录中
    temp_dir = mkd_tempdir(prefix="upload_dir_", dir=upload_dir)
    # 在临时目录中创建实际的文件名
    temp_path = Path(temp_dir) / file.filename
    logger.debug(f"保存上传文件到临时路径: {temp_path}")
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = service.process_zip(temp_path)
        return {
            "status": "success",
            "label": result["label"],
            "geojson": result["geojson"],
            "local_path": result["local_path"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 处理完成后立即删除临时目录及其内容，释放磁盘空间
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            # 清理失败不影响主流程，退出时 atexit 仍会尝试清理
            pass

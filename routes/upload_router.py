import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
from service.shapefile import ShapefileService
from utils.file_handler import get_unique_filename
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

upload_dir = os.getenv("UPLOAD_DIR", "data/uploads")
service = ShapefileService(Path(upload_dir))

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持上传ZIP文件")

    # 保存上传文件
    temp_path = get_unique_filename(Path(upload_dir), file.filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = service.process_zip(temp_path)
        return {
            "status": "success",
            "geojson": result["geojson"],
            "local_path": result["local_path"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
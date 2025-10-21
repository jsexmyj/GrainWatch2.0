# app/main.py
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from config.config import ConfigManager
from routes.upload_router import router as upload_router
ConfigManager.load_config()
app = FastAPI(title="GrainWatch API", version="1.0")

# ======= 跨域配置 =======
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段全开放
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加这些配置到你的FastAPI应用
UPLOAD_DIR = Path(r"data\uploads")  # 创建上传目录
UPLOAD_DIR.mkdir(exist_ok=True)  # 确保目录存在

# 添加静态文件服务，这样上传的文件可以通过URL访问
app.mount("/uploads", StaticFiles(directory=r"data\uploads"), name="uploads")

# ======= 注册接口路由 =======
app.include_router(upload_router, tags=["Upload"])


# ======= 启动入口 =======
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
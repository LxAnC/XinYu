"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import init_db

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="心语 - 心理健康社区应用后端API",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件（上传的文件）
upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), settings.upload_dir)
if os.path.exists(upload_path):
    app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")


@app.on_event("startup")
async def startup():
    """应用启动时执行"""
    # 初始化数据库表
    init_db()
    print(f"[OK] {settings.app_name} backend started")
    print(f"[OK] API docs: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown():
    """应用关闭时执行"""
    print(f"[OK] {settings.app_name} backend stopped")


# 健康检查
@app.get("/", tags=["健康检查"])
async def root():
    """根路径 - 健康检查"""
    return {
        "app": settings.app_name,
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


# 导入并注册路由
from app.routers import auth, posts, counselors, messages, payments, upload

app.include_router(auth.router, prefix="/api/v1/auth", tags=["用户认证"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["内容管理"])
app.include_router(counselors.router, prefix="/api/v1/counselors", tags=["咨询服务"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["消息系统"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["支付系统"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["文件上传"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)

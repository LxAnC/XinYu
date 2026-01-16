"""
文件上传路由
"""
import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.dependencies import require_auth
from app.config import settings

router = APIRouter()

# 允许的图片类型
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
# 允许的文件类型（证书等）
ALLOWED_FILE_TYPES = {"application/pdf", "image/jpeg", "image/png"}
# 最大文件大小 (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


def get_upload_dir() -> str:
    """获取上传目录路径"""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def generate_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    ext = os.path.splitext(original_filename)[1].lower()
    date_path = datetime.now().strftime("%Y/%m/%d")
    unique_id = uuid.uuid4().hex[:16]
    return f"{date_path}/{unique_id}{ext}"


@router.post("/image", summary="上传图片")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_auth),
):
    """
    上传单张图片
    - 支持 jpg/png/gif/webp
    - 最大 5MB
    - 返回图片访问 URL
    """
    # 检查文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式，仅支持: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    # 读取文件内容
    content = await file.read()

    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)"
        )

    # 生成文件路径
    relative_path = generate_filename(file.filename)
    upload_dir = get_upload_dir()
    full_path = os.path.join(upload_dir, relative_path)

    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # 保存文件
    with open(full_path, "wb") as f:
        f.write(content)

    # 返回访问 URL
    url = f"/uploads/{relative_path}"

    return {
        "url": url,
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type
    }


@router.post("/images", summary="批量上传图片")
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_auth),
):
    """
    批量上传图片
    - 最多 9 张
    - 每张最大 5MB
    """
    if len(files) > 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多上传 9 张图片"
        )

    results = []
    errors = []

    for i, file in enumerate(files):
        try:
            # 检查文件类型
            if file.content_type not in ALLOWED_IMAGE_TYPES:
                errors.append({
                    "index": i,
                    "filename": file.filename,
                    "error": f"不支持的图片格式"
                })
                continue

            # 读取文件内容
            content = await file.read()

            # 检查文件大小
            if len(content) > MAX_FILE_SIZE:
                errors.append({
                    "index": i,
                    "filename": file.filename,
                    "error": "文件过大"
                })
                continue

            # 生成文件路径
            relative_path = generate_filename(file.filename)
            upload_dir = get_upload_dir()
            full_path = os.path.join(upload_dir, relative_path)

            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # 保存文件
            with open(full_path, "wb") as f:
                f.write(content)

            results.append({
                "index": i,
                "url": f"/uploads/{relative_path}",
                "filename": file.filename,
                "size": len(content)
            })

        except Exception as e:
            errors.append({
                "index": i,
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "success": results,
        "errors": errors,
        "total": len(files),
        "success_count": len(results),
        "error_count": len(errors)
    }


@router.post("/file", summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_auth),
):
    """
    上传文件（PDF、图片等）
    用于咨询师证书等材料上传
    """
    # 检查文件类型
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式，仅支持: {', '.join(ALLOWED_FILE_TYPES)}"
        )

    # 读取文件内容
    content = await file.read()

    # 检查文件大小 (10MB for files)
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({max_size // 1024 // 1024}MB)"
        )

    # 生成文件路径
    relative_path = f"files/{generate_filename(file.filename)}"
    upload_dir = get_upload_dir()
    full_path = os.path.join(upload_dir, relative_path)

    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # 保存文件
    with open(full_path, "wb") as f:
        f.write(content)

    return {
        "url": f"/uploads/{relative_path}",
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type
    }


@router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    上传用户头像
    - 仅支持 jpg/png
    - 最大 2MB
    - 自动更新用户资料
    """
    allowed_types = {"image/jpeg", "image/png"}

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="头像仅支持 jpg/png 格式"
        )

    # 读取文件内容
    content = await file.read()

    # 检查文件大小 (2MB)
    max_size = 2 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="头像大小不能超过 2MB"
        )

    # 生成文件路径
    ext = os.path.splitext(file.filename)[1].lower()
    relative_path = f"avatars/{current_user.id}{ext}"
    upload_dir = get_upload_dir()
    full_path = os.path.join(upload_dir, relative_path)

    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # 保存文件
    with open(full_path, "wb") as f:
        f.write(content)

    # 更新用户头像
    avatar_url = f"/uploads/{relative_path}"
    current_user.avatar = avatar_url
    db.commit()

    return {
        "url": avatar_url,
        "message": "头像更新成功"
    }

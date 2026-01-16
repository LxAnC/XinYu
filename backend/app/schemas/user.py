"""
用户相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")


class UserCreate(BaseModel):
    """用户注册"""
    # 手机号注册
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: Optional[str] = Field(None, min_length=6, max_length=6, description="验证码")

    # 邮箱注册
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, min_length=6, max_length=32, description="密码")

    # 通用字段
    nickname: Optional[str] = Field("用户", max_length=50, description="昵称")


class UserLogin(BaseModel):
    """用户登录"""
    # 手机号登录
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    code: Optional[str] = Field(None, min_length=6, max_length=6)

    # 邮箱登录
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    # 微信登录
    wechat_code: Optional[str] = None


class UserUpdate(BaseModel):
    """用户资料更新"""
    nickname: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = Field(None, max_length=255)


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    phone: Optional[str] = None
    email: Optional[str] = None
    nickname: str
    avatar: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """登录成功响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

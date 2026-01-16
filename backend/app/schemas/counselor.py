"""
咨询师相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.counselor import AppointmentStatus
from app.schemas.user import UserResponse


class CounselorApply(BaseModel):
    """申请成为咨询师"""
    title: str = Field(..., max_length=50, description="职称")
    introduction: str = Field(..., min_length=10, description="简介")
    specialties: str = Field(..., description="擅长领域，逗号分隔")
    price: Decimal = Field(..., gt=0, description="咨询单价")
    certificates: Optional[str] = Field("", description="资质证书URL，JSON格式")


class CounselorResponse(BaseModel):
    """咨询师信息响应"""
    user_id: int
    title: str
    introduction: str
    specialties: str
    price: Decimal
    rating: Decimal
    consult_count: int
    is_verified: bool
    user: UserResponse  # 关联的用户信息

    class Config:
        from_attributes = True


class CounselorListResponse(BaseModel):
    """咨询师列表响应"""
    items: List[CounselorResponse]
    total: int
    page: int
    page_size: int


class AppointmentCreate(BaseModel):
    """创建预约"""
    counselor_id: int = Field(..., description="咨询师ID")
    scheduled_time: datetime = Field(..., description="预约时间")
    duration: int = Field(60, ge=30, le=120, description="时长（分钟）")
    notes: Optional[str] = Field("", max_length=500, description="备注")


class AppointmentResponse(BaseModel):
    """预约响应"""
    id: int
    user_id: int
    counselor_id: int
    scheduled_time: datetime
    duration: int
    status: AppointmentStatus
    amount: Decimal
    notes: str
    created_at: datetime
    counselor: Optional[CounselorResponse] = None

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """预约列表响应"""
    items: List[AppointmentResponse]
    total: int

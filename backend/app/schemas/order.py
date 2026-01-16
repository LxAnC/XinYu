"""
订单相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.order import PaymentMethod, OrderStatus


class OrderCreate(BaseModel):
    """创建订单"""
    appointment_id: int = Field(..., description="预约ID")
    payment_method: PaymentMethod = Field(..., description="支付方式")


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    order_no: str
    user_id: int
    appointment_id: Optional[int]
    amount: Decimal
    payment_method: Optional[PaymentMethod]
    status: OrderStatus
    paid_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """订单列表响应"""
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int


class PaymentCreateResponse(BaseModel):
    """创建支付响应"""
    order_no: str
    amount: Decimal
    # 微信/支付宝的支付参数
    pay_params: dict = {}

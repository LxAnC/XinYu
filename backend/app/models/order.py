"""
订单模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PaymentMethod(str, enum.Enum):
    """支付方式"""
    WECHAT = "wechat"
    ALIPAY = "alipay"


class OrderStatus(str, enum.Enum):
    """订单状态"""
    PENDING = "pending"     # 待支付
    PAID = "paid"           # 已支付
    REFUNDED = "refunded"   # 已退款


class Order(Base):
    """订单表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(64), unique=True, index=True)  # 订单号
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)  # 金额
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    paid_at = Column(DateTime, nullable=True)  # 支付时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="orders")
    appointment = relationship("Appointment", back_populates="order")

    def __repr__(self):
        return f"<Order(id={self.id}, order_no={self.order_no}, status={self.status})>"

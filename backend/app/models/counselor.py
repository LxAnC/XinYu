"""
咨询师相关模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AppointmentStatus(str, enum.Enum):
    """预约状态"""
    PENDING = "pending"       # 待确认
    CONFIRMED = "confirmed"   # 已确认
    COMPLETED = "completed"   # 已完成
    CANCELLED = "cancelled"   # 已取消


class CounselorProfile(Base):
    """咨询师资料表"""
    __tablename__ = "counselor_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    title = Column(String(50), default="")  # 职称
    introduction = Column(Text, default="")  # 简介
    specialties = Column(String(255), default="")  # 擅长领域，逗号分隔
    price = Column(Numeric(10, 2), default=0)  # 咨询单价
    rating = Column(Numeric(2, 1), default=5.0)  # 评分
    consult_count = Column(Integer, default=0)  # 咨询次数
    is_verified = Column(Boolean, default=False)  # 是否认证
    certificates = Column(Text, default="")  # 资质证书URL，JSON格式
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="counselor_profile")
    appointments = relationship("Appointment", back_populates="counselor", foreign_keys="Appointment.counselor_id")

    def __repr__(self):
        return f"<CounselorProfile(user_id={self.user_id}, title={self.title})>"


class Appointment(Base):
    """预约表"""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    counselor_id = Column(Integer, ForeignKey("counselor_profiles.user_id"), nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=False)  # 预约时间
    duration = Column(Integer, default=60)  # 时长（分钟）
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    amount = Column(Numeric(10, 2), default=0)  # 金额
    notes = Column(Text, default="")  # 备注
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    counselor = relationship("CounselorProfile", back_populates="appointments")
    order = relationship("Order", back_populates="appointment", uselist=False)

    def __repr__(self):
        return f"<Appointment(id={self.id}, status={self.status})>"

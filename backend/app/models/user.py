"""
用户模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """用户角色"""
    USER = "user"
    COUNSELOR = "counselor"
    ADMIN = "admin"


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    wechat_openid = Column(String(100), unique=True, nullable=True, index=True)
    nickname = Column(String(50), default="用户")
    avatar = Column(String(255), default="")
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    counselor_profile = relationship("CounselorProfile", back_populates="user", uselist=False)
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    orders = relationship("Order", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, nickname={self.nickname})>"

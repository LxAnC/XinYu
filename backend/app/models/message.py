"""
消息模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class MessageType(str, enum.Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    msg_type = Column(Enum(MessageType), default=MessageType.TEXT)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关联关系
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

    def __repr__(self):
        return f"<Message(id={self.id}, sender={self.sender_id}, receiver={self.receiver_id})>"

"""
消息相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.message import MessageType
from app.schemas.user import UserResponse


class MessageCreate(BaseModel):
    """发送消息"""
    receiver_id: int = Field(..., description="接收者ID")
    content: str = Field(..., min_length=1, max_length=1000, description="消息内容")
    msg_type: MessageType = Field(MessageType.TEXT, description="消息类型")


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    sender_id: int
    receiver_id: int
    content: str
    msg_type: MessageType
    is_read: bool
    created_at: datetime
    sender: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """会话响应"""
    user: UserResponse  # 对方用户信息
    last_message: Optional[MessageResponse] = None  # 最后一条消息
    unread_count: int = 0  # 未读消息数


class MessageListResponse(BaseModel):
    """消息列表响应"""
    items: List[MessageResponse]
    total: int
    page: int
    page_size: int


class WebSocketMessage(BaseModel):
    """WebSocket 消息格式"""
    type: str = Field(..., description="消息类型: chat/system/typing")
    from_user_id: int
    to_user_id: int
    content: str
    timestamp: datetime

"""
消息路由
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func

from app.database import get_db
from app.models.user import User
from app.models.message import Message, MessageType
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ConversationResponse,
    WebSocketMessage,
)
from app.schemas.user import UserResponse
from app.utils.dependencies import require_auth
from app.utils.security import decode_access_token

router = APIRouter()

# WebSocket 连接管理器
class ConnectionManager:
    """WebSocket 连接管理"""
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, message: dict, user_id: int):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for websocket in self.active_connections.values():
            await websocket.send_json(message)


manager = ConnectionManager()


@router.get("/conversations", response_model=list[ConversationResponse], summary="获取会话列表")
async def list_conversations(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的所有会话列表
    按最后一条消息时间倒序排列
    """
    # 获取与当前用户相关的所有消息中涉及的用户ID
    subquery = db.query(
        func.least(Message.sender_id, Message.receiver_id).label('user1'),
        func.greatest(Message.sender_id, Message.receiver_id).label('user2'),
        func.max(Message.created_at).label('last_time')
    ).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).group_by(
        func.least(Message.sender_id, Message.receiver_id),
        func.greatest(Message.sender_id, Message.receiver_id)
    ).subquery()

    # 找出所有聊过天的用户
    other_user_ids = set()
    messages = db.query(Message).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).all()

    for msg in messages:
        if msg.sender_id == current_user.id:
            other_user_ids.add(msg.receiver_id)
        else:
            other_user_ids.add(msg.sender_id)

    conversations = []
    for other_id in other_user_ids:
        # 获取对方用户信息
        other_user = db.query(User).filter(User.id == other_id).first()
        if not other_user:
            continue

        # 获取最后一条消息
        last_message = db.query(Message).filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
                and_(Message.sender_id == other_id, Message.receiver_id == current_user.id)
            )
        ).order_by(desc(Message.created_at)).first()

        # 统计未读消息数
        unread_count = db.query(Message).filter(
            Message.sender_id == other_id,
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).count()

        conversations.append(ConversationResponse(
            user=UserResponse.model_validate(other_user),
            last_message=MessageResponse.model_validate(last_message) if last_message else None,
            unread_count=unread_count
        ))

    # 按最后消息时间排序
    conversations.sort(
        key=lambda x: x.last_message.created_at if x.last_message else datetime.min,
        reverse=True
    )

    return conversations


@router.get("/{user_id}", response_model=MessageListResponse, summary="获取与某用户的消息记录")
async def get_messages(
    user_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """获取与指定用户的聊天记录"""
    # 检查用户是否存在
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 查询消息
    query = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    )

    total = query.count()

    messages = query.order_by(desc(Message.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 标记消息为已读
    db.query(Message).filter(
        Message.sender_id == user_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({"is_read": True})
    db.commit()

    # 构建响应
    items = []
    for msg in messages:
        msg_response = MessageResponse.model_validate(msg)
        msg_response.sender = UserResponse.model_validate(msg.sender)
        items.append(msg_response)

    # 反转顺序，让旧消息在前
    items.reverse()

    return MessageListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=MessageResponse, summary="发送消息")
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """发送消息"""
    # 检查接收者是否存在
    receiver = db.query(User).filter(User.id == message_data.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接收者不存在"
        )

    # 不能给自己发消息
    if current_user.id == message_data.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能给自己发消息"
        )

    # 创建消息
    message = Message(
        sender_id=current_user.id,
        receiver_id=message_data.receiver_id,
        content=message_data.content,
        msg_type=message_data.msg_type,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # 通过 WebSocket 推送给接收者
    await manager.send_personal_message(
        {
            "type": "chat",
            "from_user_id": current_user.id,
            "to_user_id": message_data.receiver_id,
            "content": message_data.content,
            "msg_type": message_data.msg_type.value,
            "message_id": message.id,
            "timestamp": message.created_at.isoformat(),
        },
        message_data.receiver_id
    )

    response = MessageResponse.model_validate(message)
    response.sender = UserResponse.model_validate(current_user)
    return response


@router.put("/{message_id}/read", summary="标记消息已读")
async def mark_as_read(
    message_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """标记消息为已读"""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.receiver_id == current_user.id
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )

    message.is_read = True
    db.commit()

    return {"message": "已标记为已读"}


@router.get("/unread/count", summary="获取未读消息数")
async def get_unread_count(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """获取未读消息总数"""
    count = db.query(Message).filter(
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).count()

    return {"unread_count": count}


# ================== WebSocket 实时消息 ==================

@router.websocket("/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket 实时消息连接
    客户端通过 ws://host/api/messages/ws/{jwt_token} 连接
    """
    # 验证 token
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=4001)
        return

    # 建立连接
    await manager.connect(user_id, websocket)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()

            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                # 处理聊天消息
                receiver_id = data.get("to_user_id")
                content = data.get("content", "")

                if receiver_id and content:
                    # 保存到数据库
                    message = Message(
                        sender_id=user_id,
                        receiver_id=receiver_id,
                        content=content,
                        msg_type=MessageType.TEXT,
                    )
                    db.add(message)
                    db.commit()
                    db.refresh(message)

                    # 推送给接收者
                    await manager.send_personal_message(
                        {
                            "type": "chat",
                            "from_user_id": user_id,
                            "to_user_id": receiver_id,
                            "content": content,
                            "message_id": message.id,
                            "timestamp": message.created_at.isoformat(),
                        },
                        receiver_id
                    )

            elif msg_type == "typing":
                # 处理正在输入状态
                receiver_id = data.get("to_user_id")
                if receiver_id:
                    await manager.send_personal_message(
                        {
                            "type": "typing",
                            "from_user_id": user_id,
                        },
                        receiver_id
                    )

    except WebSocketDisconnect:
        manager.disconnect(user_id)

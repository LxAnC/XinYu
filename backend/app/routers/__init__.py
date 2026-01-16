"""
路由模块
"""
from app.routers import auth, posts, counselors, messages, payments, upload

__all__ = [
    "auth",
    "posts",
    "counselors",
    "messages",
    "payments",
    "upload",
]

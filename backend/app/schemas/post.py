"""
帖子相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.post import PostCategory, PostStatus
from app.schemas.user import UserResponse


class PostCreate(BaseModel):
    """创建帖子"""
    title: str = Field(..., min_length=1, max_length=100, description="标题")
    content: str = Field(..., min_length=1, description="内容")
    cover_image: Optional[str] = Field("", max_length=255, description="封面图URL")
    category: PostCategory = Field(PostCategory.OTHER, description="分类")


class PostUpdate(BaseModel):
    """更新帖子"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1)
    cover_image: Optional[str] = Field(None, max_length=255)
    category: Optional[PostCategory] = None
    status: Optional[PostStatus] = None


class PostResponse(BaseModel):
    """帖子详情响应"""
    id: int
    title: str
    content: str
    cover_image: str
    category: PostCategory
    like_count: int
    collect_count: int
    comment_count: int
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    author: UserResponse

    # 当前用户状态（需要额外设置）
    is_liked: bool = False
    is_collected: bool = False

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """帖子列表响应"""
    items: List[PostResponse]
    total: int
    page: int
    page_size: int
    pages: int


class CommentCreate(BaseModel):
    """创建评论"""
    content: str = Field(..., min_length=1, max_length=500, description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID，用于回复")


class CommentResponse(BaseModel):
    """评论响应"""
    id: int
    content: str
    created_at: datetime
    author: UserResponse
    parent_id: Optional[int] = None
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True


# 支持嵌套引用
CommentResponse.model_rebuild()

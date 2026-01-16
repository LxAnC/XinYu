"""
帖子相关模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PostStatus(str, enum.Enum):
    """帖子状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    HIDDEN = "hidden"


class PostCategory(str, enum.Enum):
    """帖子分类"""
    ANXIETY = "焦虑"
    EMOTION = "情绪"
    RELATIONSHIP = "亲密关系"
    CAREER = "职场"
    GROWTH = "成长"
    OTHER = "其他"


class Post(Base):
    """帖子表"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    cover_image = Column(String(255), default="")
    category = Column(Enum(PostCategory), default=PostCategory.OTHER)
    like_count = Column(Integer, default=0)
    collect_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    status = Column(Enum(PostStatus), default=PostStatus.PUBLISHED)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, title={self.title})>"


class Like(Base):
    """点赞表"""
    __tablename__ = "likes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    post = relationship("Post", back_populates="likes")


class Collection(Base):
    """收藏表"""
    __tablename__ = "collections"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    post = relationship("Post", back_populates="collections")


class Comment(Base):
    """评论表"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id})>"

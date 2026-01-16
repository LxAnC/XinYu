"""
帖子路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.post import Post, Like, Collection, Comment, PostStatus, PostCategory
from app.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    CommentCreate,
    CommentResponse,
)
from app.schemas.user import UserResponse
from app.utils.dependencies import require_auth, get_current_user

router = APIRouter()


def get_post_response(post: Post, current_user: Optional[User], db: Session) -> PostResponse:
    """构建帖子响应，包含当前用户的点赞/收藏状态"""
    is_liked = False
    is_collected = False

    if current_user:
        is_liked = db.query(Like).filter(
            Like.post_id == post.id,
            Like.user_id == current_user.id
        ).first() is not None

        is_collected = db.query(Collection).filter(
            Collection.post_id == post.id,
            Collection.user_id == current_user.id
        ).first() is not None

    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        cover_image=post.cover_image,
        category=post.category,
        like_count=post.like_count,
        collect_count=post.collect_count,
        comment_count=post.comment_count,
        status=post.status,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=UserResponse.model_validate(post.author),
        is_liked=is_liked,
        is_collected=is_collected,
    )


@router.get("", response_model=PostListResponse, summary="获取帖子列表")
async def list_posts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    category: Optional[PostCategory] = Query(None, description="分类筛选"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取帖子列表（分页、分类筛选）"""
    query = db.query(Post).filter(Post.status == PostStatus.PUBLISHED)

    if category:
        query = query.filter(Post.category == category)

    # 总数
    total = query.count()

    # 分页
    posts = query.order_by(desc(Post.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 构建响应
    items = [get_post_response(post, current_user, db) for post in posts]

    return PostListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{post_id}", response_model=PostResponse, summary="获取帖子详情")
async def get_post(
    post_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取帖子详情"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    return get_post_response(post, current_user, db)


@router.post("", response_model=PostResponse, summary="发布帖子")
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """发布帖子"""
    post = Post(
        user_id=current_user.id,
        title=post_data.title,
        content=post_data.content,
        cover_image=post_data.cover_image,
        category=post_data.category,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return get_post_response(post, current_user, db)


@router.put("/{post_id}", response_model=PostResponse, summary="编辑帖子")
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """编辑帖子（仅作者可编辑）"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权编辑此帖子"
        )

    # 更新字段
    if post_data.title is not None:
        post.title = post_data.title
    if post_data.content is not None:
        post.content = post_data.content
    if post_data.cover_image is not None:
        post.cover_image = post_data.cover_image
    if post_data.category is not None:
        post.category = post_data.category
    if post_data.status is not None:
        post.status = post_data.status

    db.commit()
    db.refresh(post)

    return get_post_response(post, current_user, db)


@router.delete("/{post_id}", summary="删除帖子")
async def delete_post(
    post_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """删除帖子（仅作者可删除）"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此帖子"
        )

    db.delete(post)
    db.commit()

    return {"message": "删除成功"}


@router.post("/{post_id}/like", summary="点赞")
async def like_post(
    post_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """点赞帖子"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 检查是否已点赞
    existing_like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经点赞过了"
        )

    # 添加点赞
    like = Like(user_id=current_user.id, post_id=post_id)
    db.add(like)
    post.like_count += 1
    db.commit()

    return {"message": "点赞成功", "like_count": post.like_count}


@router.delete("/{post_id}/like", summary="取消点赞")
async def unlike_post(
    post_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """取消点赞"""
    like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()

    if not like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未点赞过"
        )

    post = db.query(Post).filter(Post.id == post_id).first()
    db.delete(like)
    post.like_count = max(0, post.like_count - 1)
    db.commit()

    return {"message": "取消点赞成功", "like_count": post.like_count}


@router.post("/{post_id}/collect", summary="收藏")
async def collect_post(
    post_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """收藏帖子"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 检查是否已收藏
    existing = db.query(Collection).filter(
        Collection.post_id == post_id,
        Collection.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经收藏过了"
        )

    # 添加收藏
    collection = Collection(user_id=current_user.id, post_id=post_id)
    db.add(collection)
    post.collect_count += 1
    db.commit()

    return {"message": "收藏成功", "collect_count": post.collect_count}


@router.delete("/{post_id}/collect", summary="取消收藏")
async def uncollect_post(
    post_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """取消收藏"""
    collection = db.query(Collection).filter(
        Collection.post_id == post_id,
        Collection.user_id == current_user.id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未收藏过"
        )

    post = db.query(Post).filter(Post.id == post_id).first()
    db.delete(collection)
    post.collect_count = max(0, post.collect_count - 1)
    db.commit()

    return {"message": "取消收藏成功", "collect_count": post.collect_count}


@router.get("/{post_id}/comments", response_model=list[CommentResponse], summary="获取评论列表")
async def list_comments(
    post_id: int,
    db: Session = Depends(get_db)
):
    """获取帖子评论列表"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 获取顶级评论（parent_id 为空）
    comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_id == None
    ).order_by(Comment.created_at.desc()).all()

    return [CommentResponse.model_validate(c) for c in comments]


@router.post("/{post_id}/comments", response_model=CommentResponse, summary="发表评论")
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """发表评论"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 如果是回复，检查父评论是否存在
    if comment_data.parent_id:
        parent = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
        if not parent or parent.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父评论不存在"
            )

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        parent_id=comment_data.parent_id,
        content=comment_data.content,
    )
    db.add(comment)
    post.comment_count += 1
    db.commit()
    db.refresh(comment)

    return CommentResponse.model_validate(comment)

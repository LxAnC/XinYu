"""
用户认证路由
"""
import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
    SendCodeRequest,
)
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.utils.dependencies import require_auth
from app.config import settings

router = APIRouter()

# 模拟验证码存储（生产环境应使用 Redis）
verification_codes: dict = {}


@router.post("/send-code", summary="发送验证码")
async def send_code(request: SendCodeRequest, db: Session = Depends(get_db)):
    """
    发送手机验证码
    - 开发模式：验证码固定为 123456
    - 生产模式：调用短信服务商 API
    """
    phone = request.phone

    if settings.debug:
        # 开发模式：固定验证码
        code = "123456"
    else:
        # 生产模式：生成随机6位验证码
        code = str(random.randint(100000, 999999))
        # TODO: 调用短信服务商 API 发送验证码

    # 存储验证码（生产环境应存入 Redis 并设置过期时间）
    verification_codes[phone] = code

    return {"message": "验证码已发送", "debug_code": code if settings.debug else None}


@router.post("/register/email", response_model=TokenResponse, summary="邮箱注册")
async def register_email(user_data: UserCreate, db: Session = Depends(get_db)):
    """邮箱注册"""
    if not user_data.email or not user_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱和密码不能为空"
        )

    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )

    # 创建用户
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        nickname=user_data.nickname or f"用户{random.randint(10000, 99999)}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 生成 Token
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/register/phone", response_model=TokenResponse, summary="手机号注册")
async def register_phone(user_data: UserCreate, db: Session = Depends(get_db)):
    """手机号注册"""
    if not user_data.phone or not user_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号和验证码不能为空"
        )

    # 验证验证码
    stored_code = verification_codes.get(user_data.phone)
    if not stored_code or stored_code != user_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )

    # 检查手机号是否已存在
    existing_user = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已被注册"
        )

    # 创建用户
    user = User(
        phone=user_data.phone,
        nickname=user_data.nickname or f"用户{random.randint(10000, 99999)}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 清除验证码
    verification_codes.pop(user_data.phone, None)

    # 生成 Token
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login/email", response_model=TokenResponse, summary="邮箱登录")
async def login_email(login_data: UserLogin, db: Session = Depends(get_db)):
    """邮箱密码登录"""
    if not login_data.email or not login_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱和密码不能为空"
        )

    # 查找用户
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )

    # 验证密码
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )

    # 生成 Token
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login/phone", response_model=TokenResponse, summary="手机号登录")
async def login_phone(login_data: UserLogin, db: Session = Depends(get_db)):
    """手机号验证码登录"""
    if not login_data.phone or not login_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号和验证码不能为空"
        )

    # 验证验证码
    stored_code = verification_codes.get(login_data.phone)
    if not stored_code or stored_code != login_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )

    # 查找用户
    user = db.query(User).filter(User.phone == login_data.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    # 清除验证码
    verification_codes.pop(login_data.phone, None)

    # 生成 Token
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login/wechat", response_model=TokenResponse, summary="微信登录")
async def login_wechat(login_data: UserLogin, db: Session = Depends(get_db)):
    """微信登录"""
    if not login_data.wechat_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信授权码不能为空"
        )

    if settings.debug:
        # 开发模式：模拟 openid
        openid = f"debug_openid_{login_data.wechat_code}"
    else:
        # 生产模式：调用微信 API 获取 openid
        # TODO: 实现微信 OAuth 流程
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="微信登录暂未实现"
        )

    # 查找或创建用户
    user = db.query(User).filter(User.wechat_openid == openid).first()
    if not user:
        user = User(
            wechat_openid=openid,
            nickname=f"微信用户{random.randint(10000, 99999)}",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 生成 Token
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(require_auth)):
    """获取当前登录用户信息"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse, summary="更新用户资料")
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """更新当前用户资料"""
    if user_data.nickname is not None:
        current_user.nickname = user_data.nickname
    if user_data.avatar is not None:
        current_user.avatar = user_data.avatar

    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)

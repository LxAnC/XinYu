"""
咨询师路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User, UserRole
from app.models.counselor import CounselorProfile, Appointment, AppointmentStatus
from app.schemas.counselor import (
    CounselorApply,
    CounselorResponse,
    CounselorListResponse,
    AppointmentCreate,
    AppointmentResponse,
    AppointmentListResponse,
)
from app.schemas.user import UserResponse
from app.utils.dependencies import require_auth, require_role

router = APIRouter()


@router.get("", response_model=CounselorListResponse, summary="获取咨询师列表")
async def list_counselors(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    specialty: Optional[str] = Query(None, description="擅长领域筛选"),
    db: Session = Depends(get_db)
):
    """获取咨询师列表"""
    query = db.query(CounselorProfile).filter(CounselorProfile.is_verified == True)

    if specialty:
        query = query.filter(CounselorProfile.specialties.contains(specialty))

    total = query.count()

    counselors = query.order_by(
        desc(CounselorProfile.rating),
        desc(CounselorProfile.consult_count)
    ).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for c in counselors:
        items.append(CounselorResponse(
            user_id=c.user_id,
            title=c.title,
            introduction=c.introduction,
            specialties=c.specialties,
            price=c.price,
            rating=c.rating,
            consult_count=c.consult_count,
            is_verified=c.is_verified,
            user=UserResponse.model_validate(c.user)
        ))

    return CounselorListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{counselor_id}", response_model=CounselorResponse, summary="获取咨询师详情")
async def get_counselor(
    counselor_id: int,
    db: Session = Depends(get_db)
):
    """获取咨询师详情"""
    counselor = db.query(CounselorProfile).filter(
        CounselorProfile.user_id == counselor_id
    ).first()

    if not counselor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="咨询师不存在"
        )

    return CounselorResponse(
        user_id=counselor.user_id,
        title=counselor.title,
        introduction=counselor.introduction,
        specialties=counselor.specialties,
        price=counselor.price,
        rating=counselor.rating,
        consult_count=counselor.consult_count,
        is_verified=counselor.is_verified,
        user=UserResponse.model_validate(counselor.user)
    )


@router.post("/apply", summary="申请成为咨询师")
async def apply_counselor(
    apply_data: CounselorApply,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """申请成为咨询师"""
    # 检查是否已经申请过
    existing = db.query(CounselorProfile).filter(
        CounselorProfile.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经申请过了"
        )

    # 创建咨询师资料
    profile = CounselorProfile(
        user_id=current_user.id,
        title=apply_data.title,
        introduction=apply_data.introduction,
        specialties=apply_data.specialties,
        price=apply_data.price,
        certificates=apply_data.certificates,
        is_verified=False,  # 需要管理员审核
    )
    db.add(profile)

    # 更新用户角色（待审核状态可以考虑用别的方式处理）
    current_user.role = UserRole.COUNSELOR
    db.commit()

    return {"message": "申请已提交，请等待审核"}


@router.get("/{counselor_id}/schedule", summary="获取咨询师可预约时间")
async def get_counselor_schedule(
    counselor_id: int,
    db: Session = Depends(get_db)
):
    """
    获取咨询师可预约时间
    实际项目中需要咨询师设置自己的可用时间段
    这里简化处理，返回模拟数据
    """
    counselor = db.query(CounselorProfile).filter(
        CounselorProfile.user_id == counselor_id
    ).first()

    if not counselor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="咨询师不存在"
        )

    # 模拟可预约时间（实际项目需要从数据库读取）
    from datetime import datetime, timedelta
    now = datetime.now()
    available_slots = []

    for i in range(1, 8):  # 未来7天
        date = now + timedelta(days=i)
        for hour in [9, 10, 11, 14, 15, 16, 17]:  # 可用时段
            slot_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            available_slots.append(slot_time.isoformat())

    return {"available_slots": available_slots}


# ================== 预约相关 ==================

@router.post("/appointments", response_model=AppointmentResponse, summary="创建预约")
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """创建预约"""
    # 检查咨询师是否存在
    counselor = db.query(CounselorProfile).filter(
        CounselorProfile.user_id == appointment_data.counselor_id,
        CounselorProfile.is_verified == True
    ).first()

    if not counselor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="咨询师不存在或未认证"
        )

    # 不能预约自己
    if current_user.id == appointment_data.counselor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能预约自己"
        )

    # 计算金额
    amount = counselor.price * (appointment_data.duration / 60)

    # 创建预约
    appointment = Appointment(
        user_id=current_user.id,
        counselor_id=appointment_data.counselor_id,
        scheduled_time=appointment_data.scheduled_time,
        duration=appointment_data.duration,
        amount=amount,
        notes=appointment_data.notes,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return AppointmentResponse.model_validate(appointment)


@router.get("/appointments/my", response_model=AppointmentListResponse, summary="我的预约列表")
async def my_appointments(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """获取我的预约列表（作为用户或咨询师）"""
    # 作为用户的预约
    user_appointments = db.query(Appointment).filter(
        Appointment.user_id == current_user.id
    ).all()

    # 作为咨询师的预约
    counselor_appointments = db.query(Appointment).filter(
        Appointment.counselor_id == current_user.id
    ).all()

    all_appointments = user_appointments + counselor_appointments
    all_appointments.sort(key=lambda x: x.created_at, reverse=True)

    return AppointmentListResponse(
        items=[AppointmentResponse.model_validate(a) for a in all_appointments],
        total=len(all_appointments)
    )


@router.put("/appointments/{appointment_id}/confirm", summary="确认预约")
async def confirm_appointment(
    appointment_id: int,
    current_user: User = Depends(require_role([UserRole.COUNSELOR])),
    db: Session = Depends(get_db)
):
    """确认预约（咨询师操作）"""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.counselor_id == current_user.id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )

    if appointment.status != AppointmentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="预约状态不正确"
        )

    appointment.status = AppointmentStatus.CONFIRMED
    db.commit()

    return {"message": "预约已确认"}


@router.put("/appointments/{appointment_id}/cancel", summary="取消预约")
async def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """取消预约"""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )

    # 检查权限（用户或咨询师可取消）
    if appointment.user_id != current_user.id and appointment.counselor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权取消此预约"
        )

    if appointment.status == AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的预约无法取消"
        )

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()

    return {"message": "预约已取消"}

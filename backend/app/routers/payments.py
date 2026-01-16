"""
支付路由
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.counselor import Appointment, AppointmentStatus
from app.models.order import Order, OrderStatus, PaymentMethod
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
    PaymentCreateResponse,
)
from app.utils.dependencies import require_auth
from app.config import settings

router = APIRouter()


def generate_order_no() -> str:
    """生成订单号"""
    now = datetime.now()
    return f"{now.strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


@router.post("", response_model=PaymentCreateResponse, summary="创建支付订单")
async def create_payment(
    order_data: OrderCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    创建支付订单
    - 关联预约
    - 生成订单号
    - 返回支付参数（微信/支付宝）
    """
    # 检查预约是否存在
    appointment = db.query(Appointment).filter(
        Appointment.id == order_data.appointment_id,
        Appointment.user_id == current_user.id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预约不存在"
        )

    # 检查是否已有未支付订单
    existing_order = db.query(Order).filter(
        Order.appointment_id == order_data.appointment_id,
        Order.status == OrderStatus.PENDING
    ).first()

    if existing_order:
        # 返回已有的未支付订单
        return PaymentCreateResponse(
            order_no=existing_order.order_no,
            amount=existing_order.amount,
            pay_params=get_pay_params(existing_order, order_data.payment_method)
        )

    # 创建订单
    order = Order(
        order_no=generate_order_no(),
        user_id=current_user.id,
        appointment_id=order_data.appointment_id,
        amount=appointment.amount,
        payment_method=order_data.payment_method,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 获取支付参数
    pay_params = get_pay_params(order, order_data.payment_method)

    return PaymentCreateResponse(
        order_no=order.order_no,
        amount=order.amount,
        pay_params=pay_params
    )


def get_pay_params(order: Order, payment_method: PaymentMethod) -> dict:
    """
    获取支付参数
    开发模式返回模拟参数
    生产模式调用微信/支付宝 API
    """
    if settings.debug:
        # 开发模式：返回模拟支付参数
        if payment_method == PaymentMethod.WECHAT:
            return {
                "appId": "wx_debug_app_id",
                "timeStamp": str(int(datetime.now().timestamp())),
                "nonceStr": uuid.uuid4().hex,
                "package": f"prepay_id=debug_{order.order_no}",
                "signType": "MD5",
                "paySign": "DEBUG_PAY_SIGN",
            }
        elif payment_method == PaymentMethod.ALIPAY:
            return {
                "orderString": f"alipay_debug_order_{order.order_no}",
            }

    # 生产模式
    # TODO: 调用微信/支付宝支付 API
    return {}


@router.get("", response_model=OrderListResponse, summary="获取订单列表")
async def list_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    status_filter: Optional[OrderStatus] = Query(None, description="状态筛选"),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """获取当前用户的订单列表"""
    query = db.query(Order).filter(Order.user_id == current_user.id)

    if status_filter:
        query = query.filter(Order.status == status_filter)

    total = query.count()

    orders = query.order_by(desc(Order.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{order_no}", response_model=OrderResponse, summary="获取订单详情")
async def get_order(
    order_no: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """获取订单详情"""
    order = db.query(Order).filter(
        Order.order_no == order_no,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    return OrderResponse.model_validate(order)


@router.post("/{order_no}/pay", summary="模拟支付（开发模式）")
async def simulate_pay(
    order_no: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    模拟支付完成（仅开发模式可用）
    生产环境通过回调接口处理
    """
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该接口仅在开发模式可用"
        )

    order = db.query(Order).filter(
        Order.order_no == order_no,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单状态不正确"
        )

    # 更新订单状态
    order.status = OrderStatus.PAID
    order.paid_at = datetime.now()

    # 更新预约状态为已确认
    if order.appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == order.appointment_id
        ).first()
        if appointment:
            appointment.status = AppointmentStatus.CONFIRMED

    db.commit()

    return {"message": "支付成功", "order_no": order_no}


@router.post("/callback/wechat", summary="微信支付回调")
async def wechat_callback(request: Request, db: Session = Depends(get_db)):
    """
    微信支付回调接口
    由微信服务器调用
    """
    # TODO: 验证签名
    # TODO: 解析回调数据
    # TODO: 更新订单状态

    # 开发模式返回成功
    if settings.debug:
        return {"return_code": "SUCCESS", "return_msg": "OK"}

    # 生产模式处理逻辑
    try:
        body = await request.body()
        # TODO: 解析 XML 数据
        # TODO: 验证签名
        # TODO: 处理业务逻辑

        return {"return_code": "SUCCESS", "return_msg": "OK"}
    except Exception as e:
        return {"return_code": "FAIL", "return_msg": str(e)}


@router.post("/callback/alipay", summary="支付宝支付回调")
async def alipay_callback(request: Request, db: Session = Depends(get_db)):
    """
    支付宝支付回调接口
    由支付宝服务器调用
    """
    # TODO: 验证签名
    # TODO: 解析回调数据
    # TODO: 更新订单状态

    # 开发模式返回成功
    if settings.debug:
        return "success"

    # 生产模式处理逻辑
    try:
        form_data = await request.form()
        # TODO: 验证签名
        # TODO: 处理业务逻辑

        return "success"
    except Exception as e:
        return "fail"


@router.post("/{order_no}/refund", summary="申请退款")
async def refund_order(
    order_no: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """申请退款"""
    order = db.query(Order).filter(
        Order.order_no == order_no,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已支付的订单可以申请退款"
        )

    # TODO: 检查预约时间，判断是否可以退款

    # 更新订单状态
    order.status = OrderStatus.REFUNDED

    # 取消预约
    if order.appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == order.appointment_id
        ).first()
        if appointment:
            appointment.status = AppointmentStatus.CANCELLED

    db.commit()

    # TODO: 调用支付平台退款接口

    return {"message": "退款申请已提交", "order_no": order_no}

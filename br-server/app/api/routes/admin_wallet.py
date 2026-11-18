"""管理端钱包相关路由."""

import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.dependencies import AdminContext, get_current_admin, require_admin_permission
from app.core.database import get_db
from app.models.wallet import WalletTransaction
from app.schemas.wallet import (
    AdminWalletStatisticsResponse,
    AdminWalletTransactionListResponse,
)
from app.services.data_scope import wallet_scope_condition
from app.services.wallet_service import (
    _wallet_scope_joins,
    _wallet_user_info_map,
    admin_get_statistics,
    admin_list_transactions,
)

router = APIRouter(prefix="/api/v1/admin/wallet", tags=["admin-wallet"])


def _admin_wallet_base_conditions() -> list:
    """管理端钱包流水默认不导出待处理记录."""
    return [WalletTransaction.status != "pending"]


@router.get("/transactions", response_model=AdminWalletTransactionListResponse, dependencies=[Depends(require_admin_permission("wallet:view"))])
async def list_transactions(
    page: int = 1,
    page_size: int = 10,
    type: str | None = None,
    transaction_status: str | None = Query(default=None, alias="status"),
    user_id: str | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> AdminWalletTransactionListResponse:
    """获取钱包交易流水列表（分页）."""
    # 将 date 转换为 datetime
    start_dt = datetime.combine(date_start, datetime.min.time()) if date_start else None
    end_dt = datetime.combine(date_end, datetime.max.time()) if date_end else None

    return await admin_list_transactions(
        db,
        page=page,
        page_size=page_size,
        type=type,
        status=transaction_status,
        user_id=user_id,
        date_start=start_dt,
        date_end=end_dt,
        viewer=context,
    )


@router.get("/statistics", response_model=AdminWalletStatisticsResponse, dependencies=[Depends(require_admin_permission("wallet:view"))])
async def get_statistics(
    date_start: date | None = None,
    date_end: date | None = None,
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> AdminWalletStatisticsResponse:
    """获取财务统计信息."""
    # 将 date 转换为 datetime
    start_dt = datetime.combine(date_start, datetime.min.time()) if date_start else None
    end_dt = datetime.combine(date_end, datetime.max.time()) if date_end else None

    return await admin_get_statistics(
        db,
        date_start=start_dt,
        date_end=end_dt,
        viewer=context,
    )


@router.get("/transactions/export", dependencies=[Depends(require_admin_permission("wallet:export"))])
async def export_transactions(
    type: str | None = None,
    transaction_status: str | None = Query(default=None, alias="status"),
    user_id: str | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> StreamingResponse:
    """导出钱包交易流水为 CSV."""
    # 将 date 转换为 datetime
    start_dt = datetime.combine(date_start, datetime.min.time()) if date_start else None
    end_dt = datetime.combine(date_end, datetime.max.time()) if date_end else None

    # 构建查询条件
    conditions = _admin_wallet_base_conditions()
    if type is not None:
        conditions.append(WalletTransaction.type == type)
    if transaction_status is not None:
        conditions.append(WalletTransaction.status == transaction_status)
    if user_id is not None:
        conditions.append(WalletTransaction.user_id == user_id)
    if start_dt is not None:
        conditions.append(WalletTransaction.created_at >= start_dt)
    if end_dt is not None:
        conditions.append(WalletTransaction.created_at <= end_dt)

    scope = wallet_scope_condition(context)
    if scope is not None:
        conditions.append(scope)

    # 查询总数
    count_stmt = select(func.count()).select_from(WalletTransaction)
    if scope is not None:
        count_stmt = _wallet_scope_joins(count_stmt)
    count_result = await db.execute(count_stmt.where(*conditions))
    total = count_result.scalar_one()

    # 检查是否超过上限
    if total > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="导出数据超过10000条上限，请缩小筛选范围"
        )

    # 查询数据
    stmt = select(WalletTransaction)
    if scope is not None:
        stmt = _wallet_scope_joins(stmt)
    stmt = stmt.where(*conditions).order_by(
        WalletTransaction.created_at.desc(), WalletTransaction.id.desc()
    )
    result = await db.execute(stmt)
    transactions = result.scalars().all()
    user_map = await _wallet_user_info_map(db, [t.user_id for t in transactions])

    # 生成 CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    headers = [
        "交易时间",
        "用户ID",
        "用户昵称",
        "手机号",
        "交易类型",
        "金额",
        "余额",
        "状态",
        "支付方式",
    ]
    writer.writerow(headers)

    # 写入数据行
    for transaction in transactions:
        nickname, phone = user_map.get(transaction.user_id, (None, None))
        transaction_type = transaction.type
        transaction_status = transaction.status

        # 交易类型中文
        type_map = {
            "recharge": "钱包充值",
            "consume": "预约消费",
            "booking_refund": "预约退款",
            "refund": "钱包退款",
            "wallet_refund": "钱包退款",
        }
        type_cn = type_map.get(transaction_type, transaction_type)

        # 状态中文
        status_map = {
            "completed": "已完成",
            "pending": "待支付",
            "failed": "失败",
        }
        status_cn = status_map.get(transaction_status, transaction_status)

        # 支付方式中文
        payment_method_map = {
            "wechat": "微信",
            "alipay": "支付宝",
        }
        payment_method_cn = payment_method_map.get(transaction.payment_method, transaction.payment_method or "-")

        writer.writerow([
            transaction.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            transaction.user_id,
            nickname or "",
            phone or "",
            type_cn,
            float(transaction.amount),
            float(transaction.balance_after) if transaction.balance_after is not None else "",
            status_cn,
            payment_method_cn,
        ])

    # 准备响应
    output.seek(0)
    filename_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wallet_transactions_{filename_date}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
        },
    )

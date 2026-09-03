"""课程预约服务层。"""

import json
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.booking_status import BookingStatus, resolve_course_status
from app.models.booking import Booking
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.course_schedule import CourseSchedule
from app.models.lesson_schedule import LessonSchedule
from app.models.teacher import Teacher
from app.models.coupon import Coupon, UserCoupon
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.schemas.course_booking import (
    CourseBookingCreate,
    CourseBookingResponse,
)
from app.services import coupon_service
from app.core.config import settings
from app.utils.timezone import CHINA_TIMEZONE, booking_now


class CourseBookingError(ValueError):
    """课程预约基础异常。"""


class CourseNotFoundError(CourseBookingError):
    pass


class LessonValidationError(CourseBookingError):
    pass


class CouponUnavailableError(CourseBookingError):
    pass


class WalletBalanceInsufficientError(CourseBookingError):
    pass


class CourseBookingService:
    """课程预约服务。"""

    async def get_course_with_lessons(
        self, course_id: int, db: AsyncSession
    ) -> dict | None:
        """查询课程详情 + 课时列表 + 排课信息。

        仅关联固定班课（schedule_type=fixed）排课，定制课时记录不在 C 端展示。
        """
        # 使用 JOIN 一次性获取课程和排课信息（仅固定班课排课，取最早一条）
        result = await db.execute(
            select(Course, CourseSchedule, Teacher)
            .outerjoin(
                CourseSchedule,
                and_(
                    Course.id == CourseSchedule.course_id,
                    CourseSchedule.schedule_type == "fixed",
                    CourseSchedule.schedule_status == "in_progress",
                ),
            )
            .outerjoin(Teacher, CourseSchedule.teacher_id == Teacher.id)
            .where(Course.id == course_id)
            .order_by(CourseSchedule.created_at.asc())
            .limit(1)
        )
        row = result.one_or_none()
        if row is None:
            return None
        
        course, schedule, teacher = row

        lessons_result = await db.execute(
            select(CourseLesson)
            .where(CourseLesson.course_id == course_id)
            .order_by(CourseLesson.sort_order.asc())
        )
        lessons = list(lessons_result.scalars().all())

        # 构建返回数据，将排课信息合并到课程对象中
        course_dict = {
            "id": course.id,
            "name": course.name,
            "cover_image": course.cover_image,
            "category": course.category,
            "description": course.description,
            "rating": course.rating,
            "enrollment_count": course.enrollment_count,
            "status": course.status,
            "tags": course.tags,
            "room_id": course.room_id,
            # 从排课表获取价格信息
            "price": schedule.price if schedule else 0,
            "custom_price": schedule.custom_price if schedule else 0,
            "full_package_price": schedule.full_package_price if schedule else None,
            "full_custom_price": schedule.full_custom_price if schedule else None,
            # 从排课表获取时间信息
            "schedule": schedule.time_slots if schedule else None,
            # 教师信息
            "teacher": {
                "id": teacher.id,
                "name": teacher.name,
                "avatar": teacher.avatar,
                "title": teacher.title,
                "rating": teacher.rating,
            } if teacher else None,
        }

        # 将老师的可排课时间段附加到 teacher 信息中
        if teacher and teacher.available_time_slots:
            try:
                course_dict["teacher"]["available_time_slots"] = json.loads(teacher.available_time_slots)
            except (json.JSONDecodeError, TypeError):
                course_dict["teacher"]["available_time_slots"] = []
        elif teacher:
            course_dict["teacher"]["available_time_slots"] = []

        # 查询 lesson_schedules（新中间表）
        lesson_schedules_list = []
        if schedule:
            ls_result = await db.execute(
                select(LessonSchedule)
                .where(LessonSchedule.schedule_id == schedule.id)
                .order_by(LessonSchedule.sort_order.asc())
            )
            lesson_schedules_list = [
                {
                    "lesson_id": ls.lesson_id,
                    "lesson_date": ls.lesson_date.isoformat() if ls.lesson_date else None,
                    "lesson_time_slot": ls.lesson_time_slot,
                }
                for ls in ls_result.scalars().all()
            ]

        # 构建 schedule dict（包含 lesson_schedules 数据）
        schedule_dict = None
        if schedule:
            schedule_dict = {
                "id": schedule.id,
                "course_id": schedule.course_id,
                "teacher_id": schedule.teacher_id,
                "start_date": schedule.start_date.isoformat() if schedule.start_date else None,
                "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
                "time_slots": schedule.time_slots,
                "price": float(schedule.price) if schedule.price else None,
                "custom_price": float(schedule.custom_price) if schedule.custom_price else None,
                "full_package_price": float(schedule.full_package_price) if schedule.full_package_price else None,
                "full_custom_price": float(schedule.full_custom_price) if schedule.full_custom_price else None,
                "lesson_schedules": lesson_schedules_list,
            }

        return {
            "course": course_dict,
            "lessons": lessons,
            "total_lessons_count": len(lessons),
            "schedule": schedule_dict,
        }

    def calculate_price(
        self,
        course: Course,
        schedule: dict | CourseSchedule | None,
        booking_type: str,
        lesson_ids: list[int],
        total_lessons: int,
        selected_count: int | None = None,
    ) -> dict:
        """价格计算。

        从排课表获取价格信息：
        - fixed: len(lesson_ids) × schedule.price
        - custom: len(lesson_ids) × schedule.custom_price
        - 全套优惠: 选择课时数（含免费试听课时）== total_lessons 且对应全套价存在时，
          fixed 用 schedule.full_package_price，custom 用 schedule.full_custom_price

        返回 {original_price, discount_amount, unit_price, total_price}
        """
        lesson_count = len(lesson_ids)
        # 用户选择的课时总数（含免费试听课时），用于判断是否选择全套；
        # lesson_ids 为计费课时（已排除试听），含试听时两者不一致

        total_selected = selected_count if selected_count is not None else lesson_count

        # 从排课表获取价格（支持 dict 和 ORM 对象两种形式）
        if isinstance(schedule, dict):
            price_val = schedule.get("price")
            custom_price_val = schedule.get("custom_price")
            full_package_price_val = schedule.get("full_package_price")
            full_custom_price_val = schedule.get("full_custom_price")
        else:
            price_val = schedule.price if schedule else None
            custom_price_val = schedule.custom_price if schedule else None
            full_package_price_val = schedule.full_package_price if schedule else None
            full_custom_price_val = schedule.full_custom_price if schedule else None

        price = Decimal(str(price_val)) if price_val else Decimal("0")
        custom_price = Decimal(str(custom_price_val)) if custom_price_val else Decimal("0")
        full_package_price = (
            Decimal(str(full_package_price_val))
            if full_package_price_val is not None
            else None
        )
        full_custom_price = (
            Decimal(str(full_custom_price_val))
            if full_custom_price_val is not None
            else None
        )

        # 全套价与基准单价按预约类型区分：定制用定制价，固定班课用班课价
        if booking_type == "custom":
            unit_price_base = custom_price
            full_price = full_custom_price
        else:
            unit_price_base = price
            full_price = full_package_price

        # 检查是否满足全包条件（选择全部课时 + 对应全套价存在）
        if (
            total_selected == total_lessons
            and full_price is not None
            and full_price > Decimal("0")
        ):
            standard_total = unit_price_base * lesson_count
            original_price = standard_total
            discount_amount = standard_total - full_price
            if discount_amount < Decimal("0"):
                discount_amount = Decimal("0")
            unit_price = full_price / lesson_count if lesson_count > 0 else Decimal("0")
            total_price = full_price
        elif booking_type == "fixed":
            unit_price = price
            original_price = unit_price * lesson_count
            discount_amount = Decimal("0")
            total_price = original_price
        else:  # custom
            unit_price = custom_price
            original_price = unit_price * lesson_count
            discount_amount = Decimal("0")
            total_price = original_price

        if total_price < Decimal("0"):
            total_price = Decimal("0")

        return {
            "original_price": original_price.quantize(Decimal("0.01")),
            "discount_amount": discount_amount.quantize(Decimal("0.01")),
            "unit_price": unit_price.quantize(Decimal("0.01")),
            "total_price": total_price.quantize(Decimal("0.01")),
        }

    async def _validate_coupon_for_course(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        user_coupon_id: int,
        original_price: Decimal,
    ) -> tuple[Decimal, Decimal, UserCoupon]:
        """验证优惠券对课程预约的有效性。

        返回 (discount_amount, total_price, user_coupon)。
        """
        result = await db.execute(
            select(UserCoupon, Coupon)
            .join(Coupon, Coupon.id == UserCoupon.coupon_id)
            .where(UserCoupon.id == user_coupon_id)
            .with_for_update()
        )
        row = result.one_or_none()
        if row is None:
            raise CouponUnavailableError("卡券不可用")

        user_coupon, coupon = row

        # 基本检查
        if user_coupon.user_id != str(user_id):
            raise CouponUnavailableError("卡券不可用")
        if not coupon.is_active:
            raise CouponUnavailableError("卡券不可用")
        if coupon_service._get_coupon_status(user_coupon, coupon) != "available":
            raise CouponUnavailableError("卡券不可用")

        # 适用范围检查（课程预约不做 seat_zone 检查）
        has_history = await coupon_service._has_booking_history(db, str(user_id))
        user = await coupon_service._load_user(db, user_id)
        if not coupon_service._check_scope(user, coupon, has_prior_bookings=has_history):
            raise CouponUnavailableError("卡券不可用")

        # 计算折扣
        discount_amount = coupon_service._calc_discount(coupon, original_price)
        if discount_amount <= Decimal("0"):
            raise CouponUnavailableError("卡券不可用")

        total_price = original_price - discount_amount
        if total_price < Decimal("0"):
            total_price = Decimal("0")

        return (
            discount_amount.quantize(Decimal("0.01")),
            total_price.quantize(Decimal("0.01")),
            user_coupon,
        )

    async def create_course_booking(
        self,
        user_id: uuid.UUID,
        data: CourseBookingCreate,
        db: AsyncSession,
        wechat_client=None,
    ) -> CourseBookingResponse:
        """创建课程预约（完整流程）。

        1. 验证课程存在且 status='active'
        2. 验证 lesson_ids 均属于该课程
        3. 计算价格
        4. 如有 coupon_id，验证优惠券有效性
        5. 创建 Booking 记录
        6. 根据 payment_method 处理支付
        7. 如使用优惠券，标记优惠券已使用
        8. 返回响应
        """
        # 1. 查询课程 + 课时
        course_data = await self.get_course_with_lessons(data.course_id, db)
        if course_data is None:
            raise CourseNotFoundError("课程不存在")

        course = course_data["course"]
        lessons = course_data["lessons"]
        total_lessons = course_data["total_lessons_count"]
        schedule = course_data.get("schedule")

        if course["status"] != "active":
            raise CourseBookingError("课程不可预约")

        # 2. 验证 lesson_ids
        valid_lesson_ids = {lesson.id for lesson in lessons}
        invalid_ids = set(data.lesson_ids) - valid_lesson_ids
        if invalid_ids:
            raise LessonValidationError(
                f"课时 ID 无效: {list(invalid_ids)}"
            )

        # 获取选中的课时信息
        selected_lessons = [
            lesson for lesson in lessons if lesson.id in data.lesson_ids
        ]
        lesson_titles = [lesson.title for lesson in selected_lessons]

        # 3. 计算价格（排除试听课时）
        #    试听课时 (is_free_preview=True) 费用为 ¥0，不计入支付金额
        free_preview_ids = {
            lesson.id for lesson in selected_lessons if getattr(lesson, 'is_free_preview', False)
        }
        paid_lesson_ids = [lid for lid in data.lesson_ids if lid not in free_preview_ids]

        if not paid_lesson_ids:
            # 全部为试听课时，无需支付
            price_info = {
                "original_price": Decimal("0"),
                "discount_amount": Decimal("0"),
                "unit_price": Decimal("0"),
                "total_price": Decimal("0"),
            }
        else:
            price_info = self.calculate_price(
                course, schedule, data.booking_type, paid_lesson_ids, total_lessons,
                selected_count=len(data.lesson_ids),
            )
        original_price = price_info["original_price"]
        discount_amount = price_info["discount_amount"]
        total_price = price_info["total_price"]

        # 4. 优惠券验证
        user_coupon = None
        if data.coupon_id is not None:
            try:
                (
                    coupon_discount,
                    total_price_after_coupon,
                    user_coupon,
                ) = await self._validate_coupon_for_course(
                    db, user_id, data.coupon_id, total_price
                )
                discount_amount = discount_amount + coupon_discount
                total_price = total_price_after_coupon
            except coupon_service.CouponError as exc:
                raise CouponUnavailableError("卡券不可用，请重新选择") from exc

        # 5. 余额支付检查
        balance_payment = data.payment_method == "balance"
        user = None
        if balance_payment:
            user_result = await db.execute(
                select(User).where(User.id == user_id).with_for_update()
            )
            user = user_result.scalar_one_or_none()
            if user is None:
                raise CourseBookingError("用户不存在")
            if Decimal(str(user.balance)) < total_price:
                raise WalletBalanceInsufficientError("余额不足")

        # 6. 根据预约类型和开课日期判断订单状态（开课日期统一取已预约第一课时日期）
        #    1V1私人定制(custom) → pending_confirm（待确认），需管理员确认
        #    固定班课(fixed):
        #      第一课时日期 <= 今天 → confirmed（进行中）
        #      第一课时日期 > 今天  → pending（待开始）
        today = datetime.now(CHINA_TIMEZONE).date()
        first_lesson_date = None
        if data.booking_type != "custom" and isinstance(schedule, dict):
            # 从排课的课时列表中取已预约第一课时的日期（不修改排课表记录）
            selected_lesson_id_set = set(data.lesson_ids)
            for ls in schedule.get("lesson_schedules") or []:
                if ls.get("lesson_id") in selected_lesson_id_set and ls.get("lesson_date"):
                    first_lesson_date = date.fromisoformat(ls["lesson_date"])
                    break

        if data.booking_type == "custom":
            initial_status = BookingStatus.PENDING_CONFIRM.value
        else:
            initial_status = resolve_course_status(
                today=today, first_lesson_date=first_lesson_date
            ).value

        # 7. 创建 Booking 记录
        #    1V1定制：将用户选择的日期和时间段存入 booking 记录，供管理员确认时使用
        #    date → 对应 course_schedules.start_date
        #    time_slots → 对应 course_schedules.time_slots（JSON 数组）
        #    teacher_id → 对应 course_schedules.teacher_id
        booking_date = today
        booking_start_time = datetime.now(CHINA_TIMEZONE).time()
        booking_end_time = datetime.now(CHINA_TIMEZONE).time()
        booking_time_slots = None
        if data.booking_type != "custom":
            # 固定班课：预约日期取已预约第一课时日期（与开课日期口径一致），
            # 时段复制排课记录的 time_slots，供管理端按"周几 HH:MM-HH:MM"格式展示；
            # 不更新 course_schedules / lesson_schedules 表记录
            if first_lesson_date is not None:
                booking_date = first_lesson_date
            if isinstance(schedule, dict):
                raw_time_slots = schedule.get("time_slots")
            else:
                raw_time_slots = getattr(schedule, "time_slots", None) if schedule else None
            if raw_time_slots:
                if isinstance(raw_time_slots, str):
                    booking_time_slots = raw_time_slots
                else:
                    booking_time_slots = json.dumps(raw_time_slots, ensure_ascii=False)
        if data.booking_type == "custom":
            from datetime import time as time_type
            if data.start_date:
                try:
                    from datetime import date as date_type
                    booking_date = date_type.fromisoformat(data.start_date)
                except (ValueError, TypeError):
                    pass
            if data.time_slot and '-' in data.time_slot:
                try:
                    parts = data.time_slot.split('-')
                    booking_start_time = time_type.fromisoformat(parts[0].strip())
                    booking_end_time = time_type.fromisoformat(parts[1].strip())
                except (ValueError, TypeError):
                    pass
            if data.time_slot:
                # 与课程排课 time_slots 格式一致：[{"weekday": N, "time_slot": "HH:MM-HH:MM"}]
                # weekday 从用户选择的开课日期推算（isoweekday: 1=周一, 7=周日）
                weekday = booking_date.isoweekday()
                booking_time_slots = json.dumps(
                    [{"weekday": weekday, "time_slot": data.time_slot}],
                    ensure_ascii=False,
                )

        # 授课老师取自课程排课记录（course_schedules.teacher_id）
        booking_teacher_id = None
        if isinstance(schedule, dict):
            booking_teacher_id = schedule.get("teacher_id")
        elif schedule is not None:
            booking_teacher_id = getattr(schedule, "teacher_id", None)

        # 固定班课订单直接关联当前排课记录（定制订单在管理员确认创建定制排课后关联），
        # 用于按订单维度隔离课时数据，支持同一课程下多个订单并存
        booking_schedule_id = None
        if data.booking_type != "custom":
            if isinstance(schedule, dict):
                booking_schedule_id = schedule.get("id")
            elif schedule is not None:
                booking_schedule_id = getattr(schedule, "id", None)

        booking = Booking(
            user_id=str(user_id),
            room_id=course["room_id"],
            seat_id=None,  # 课程预约不需要座位
            date=booking_date,
            start_time=booking_start_time,
            end_time=booking_end_time,
            status=initial_status,
            original_price=original_price,
            discount_amount=discount_amount,
            total_price=total_price,
            coupon_id=data.coupon_id,
            payment_method=data.payment_method,
            payment_status="paid" if balance_payment else "pending",
            payment_provider=None if balance_payment else data.payment_method,
            payment_check_count=0,
            next_payment_check_at=None if balance_payment else booking_now(settings.BOOKING_TIMEZONE) + timedelta(minutes=1),
            booking_type="course",
            course_id=course["id"],
            lesson_ids=data.lesson_ids,
            schedule_type=data.schedule_type,
            schedule_id=booking_schedule_id,
            time_slots=booking_time_slots,
            teacher_id=booking_teacher_id,
        )
        db.add(booking)
        await db.flush()

        # 7.5. 1V1定制预约不在这里写入排课表，等管理员确认后再创建排课记录

        # 8. 余额扣款
        payment_params = None
        if balance_payment and user is not None:
            user.balance = Decimal(str(user.balance)) - total_price

            wallet_transaction = WalletTransaction(
                user_id=str(user_id),
                type="consume",
                amount=total_price,
                bonus_amount=Decimal("0.00"),
                balance_after=Decimal(str(user.balance)),
                order_id=str(uuid.uuid4()),
                status="completed",
                payment_method="balance",
                booking_id=booking.id,
            )
            setattr(wallet_transaction, "payment_provider", "balance")
            setattr(wallet_transaction, "payment_status", "paid")
            db.add(wallet_transaction)

        # 9. 微信支付
        if data.payment_method == "wechat" and wechat_client is not None:
            from app.services.booking_payment_service import BookingPaymentService

            # 重新加载 user 用于微信支付
            if user is None:
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()

            if user is not None:
                payment_service = BookingPaymentService(
                    db, wechat_client=wechat_client
                )
                try:
                    payment_params = await payment_service.create_booking_payment(
                        booking, user
                    )
                except Exception:
                    # 微信支付创建失败，不阻断预约创建
                    payment_params = None

        # 10. 标记优惠券已使用
        if user_coupon is not None:
            coupon_service.mark_coupon_used(user_coupon, booking.id)

        await db.flush()

        return CourseBookingResponse(
            booking_id=booking.id,
            course_name=course["name"],
            lesson_count=len(data.lesson_ids),
            lesson_titles=lesson_titles,
            original_price=float(original_price),
            discount_amount=float(discount_amount),
            total_price=float(total_price),
            payment_status=booking.payment_status,
            payment_method=data.payment_method,
            booking_type="course",
            schedule_type=data.schedule_type,
            payment_params=payment_params,
        )

    async def cancel_course_booking(
        self,
        booking_id: int,
        user_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict:
        """取消课程预约。

        1. 验证预约存在且属于当前用户
        2. 复用 booking_service 的取消逻辑
        3. 如果 booking.coupon_id 存在，恢复优惠券
        """
        from app.services.booking_service import (
            BookingAlreadyCancelledError,
            BookingCancellationNotAllowedError,
            BookingNotFoundError,
        )

        # 查询预约
        result = await db.execute(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        )
        booking = result.scalar_one_or_none()

        if booking is None or booking.user_id != str(user_id):
            raise BookingNotFoundError("预约不存在")

        if booking.booking_type != "course":
            raise CourseBookingError("该预约不是课程预约")

        if booking.status == "cancelled":
            raise BookingAlreadyCancelledError("该预约已取消")

        # 待支付状态直接取消
        if booking.payment_status == "pending" and booking.status == "pending":
            now = booking_now(settings.BOOKING_TIMEZONE)
            booking.status = "cancelled"
            booking.cancelled_at = now
            await coupon_service.restore_user_coupon_for_booking(db, booking)
            await db.flush()
            return {
                "booking_id": booking.id,
                "status": "cancelled",
                "refund_amount": 0.0,
            }

        # 已支付状态取消 - 需要退款
        # 支持 confirmed（进行中）、pending + paid（待开始已支付）、pending_confirm + paid（待确认已支付）
        if booking.status not in ("confirmed",) and not (
            booking.status == "pending" and booking.payment_status == "paid"
        ) and not (
            booking.status == "pending_confirm" and booking.payment_status == "paid"
        ):
            raise BookingCancellationNotAllowedError("该预约不可取消")

        if booking.payment_status != "paid":
            raise BookingCancellationNotAllowedError("未支付预约不可取消")

        # 获取用户并退款
        user_result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            raise CourseBookingError("用户不存在")

        # 全额退款（课程预约暂不支持阶梯退款策略）
        refund_amount = Decimal(str(booking.total_price))
        user.balance = (
            Decimal(str(user.balance)) + refund_amount
        ).quantize(Decimal("0.01"))

        now = booking_now(settings.BOOKING_TIMEZONE)
        booking.status = "cancelled"
        booking.cancelled_at = now
        booking.refund_amount = refund_amount

        # 恢复优惠券
        await coupon_service.restore_user_coupon_for_booking(db, booking)

        # 创建退款流水
        wallet_transaction = WalletTransaction(
            user_id=str(user_id),
            type="booking_refund",
            amount=refund_amount,
            bonus_amount=Decimal("0.00"),
            balance_after=Decimal(str(user.balance)),
            order_id=str(uuid.uuid4()),
            status="completed",
            payment_method=booking.payment_method,
            booking_id=booking.id,
        )
        setattr(wallet_transaction, "payment_provider", booking.payment_provider or booking.payment_method)
        setattr(wallet_transaction, "payment_status", "paid")
        setattr(wallet_transaction, "paid_at", now)
        db.add(wallet_transaction)

        await db.flush()

        return {
            "booking_id": booking.id,
            "status": "cancelled",
            "refund_amount": float(refund_amount),
        }

    async def _save_custom_schedule(
        self, db: AsyncSession, course_id: int, start_date: str | None, time_slot: str | None
    ) -> None:
        """保存自定义预约的时间到排课表。
        
        如果该课程已有排课记录，则更新；否则创建新记录。
        """
        from datetime import date as date_type
        from app.models.course_schedule import CourseSchedule
        
        # 查询该课程的现有排课记录
        schedule_result = await db.execute(
            select(CourseSchedule)
            .where(CourseSchedule.course_id == course_id)
            .order_by(CourseSchedule.created_at)
            .limit(1)
        )
        schedule = schedule_result.scalar_one_or_none()
        
        if schedule:
            # 更新现有排课记录
            if start_date:
                try:
                    schedule.start_date = date_type.fromisoformat(start_date)
                except (ValueError, TypeError):
                    pass  # 日期格式无效，忽略
            
            if time_slot:
                # 将时间段添加到 time_slots 中（JSON 数组）
                existing_slots = []
                if schedule.time_slots:
                    try:
                        existing_slots = json.loads(schedule.time_slots)
                    except (json.JSONDecodeError, TypeError):
                        existing_slots = []
                
                # 检查是否已存在相同的时间段
                if time_slot not in existing_slots:
                    existing_slots.append(time_slot)
                    schedule.time_slots = json.dumps(existing_slots, ensure_ascii=False)
        else:
            # 创建新的排课记录
            new_schedule = CourseSchedule(
                course_id=course_id,
                teacher_id=None,  # 自定义预约暂时不指定老师
            )
            
            if start_date:
                try:
                    new_schedule.start_date = date_type.fromisoformat(start_date)
                except (ValueError, TypeError):
                    pass
            
            if time_slot:
                new_schedule.time_slots = json.dumps([time_slot], ensure_ascii=False)
            
            db.add(new_schedule)

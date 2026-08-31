"""管理端老师管理服务。"""

from __future__ import annotations

import json

from sqlalchemy import delete as sa_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_schedule import CourseSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.teacher_room import TeacherRoom
from app.schemas.admin_teacher import (
    AdminTeacherCreate,
    AdminTeacherDetail,
    AdminTeacherListItem,
    AdminTeacherListResponse,
    AdminTeacherUpdate,
    TeacherRoomBrief,
)

ALLOWED_ROOM_TYPES = ("training", "comprehensive")


def _tags_to_db(tags: list[str]) -> str | None:
    cleaned = [t.strip() for t in tags if t and t.strip()]
    return ",".join(cleaned) if cleaned else None


async def _course_count_map(db: AsyncSession, teacher_ids: list[int]) -> dict[int, int]:
    """按老师统计关联课程数（去重 course_id）。"""
    if not teacher_ids:
        return {}
    result = await db.execute(
        select(
            CourseSchedule.teacher_id,
            func.count(func.distinct(CourseSchedule.course_id)),
        )
        .where(CourseSchedule.teacher_id.in_(teacher_ids))
        .group_by(CourseSchedule.teacher_id)
    )
    return {row[0]: row[1] for row in result.all()}


async def _validate_room_ids(db: AsyncSession, room_ids: list[int]) -> None:
    """校验房间存在且 room_type 为培训室或综合室。"""
    unique_ids = list(dict.fromkeys(room_ids))
    if not unique_ids:
        return
    result = await db.execute(
        select(StudyRoom.id, StudyRoom.room_type).where(StudyRoom.id.in_(unique_ids))
    )
    rooms = {row[0]: row[1] for row in result.all()}
    for room_id in unique_ids:
        if room_id not in rooms:
            raise ValueError(f"房间不存在: {room_id}")
        if rooms[room_id] not in ALLOWED_ROOM_TYPES:
            raise ValueError("所属房间仅支持培训室或综合室")


async def _sync_teacher_rooms(db: AsyncSession, teacher_id: int, room_ids: list[int]) -> None:
    await db.execute(sa_delete(TeacherRoom).where(TeacherRoom.teacher_id == teacher_id))
    unique_ids = list(dict.fromkeys(room_ids))
    for room_id in unique_ids:
        db.add(TeacherRoom(teacher_id=teacher_id, room_id=room_id))


async def _load_rooms_for_teachers(db: AsyncSession, teacher_ids: list[int]) -> dict[int, list[TeacherRoomBrief]]:
    if not teacher_ids:
        return {}
    result = await db.execute(
        select(TeacherRoom.teacher_id, StudyRoom)
        .join(StudyRoom, TeacherRoom.room_id == StudyRoom.id)
        .where(TeacherRoom.teacher_id.in_(teacher_ids))
        .order_by(TeacherRoom.id)
    )
    rooms_map: dict[int, list[TeacherRoomBrief]] = {}
    for teacher_id, room in result.all():
        rooms_map.setdefault(teacher_id, []).append(
            TeacherRoomBrief(id=room.id, name=room.name, room_type=room.room_type)
        )
    return rooms_map


async def list_teachers(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    status: str | None = None,
) -> AdminTeacherListResponse:
    filters = []
    if keyword:
        filters.append(Teacher.name.ilike(f"%{keyword}%"))
    if status:
        filters.append(Teacher.status == status)

    total = await db.scalar(select(func.count(Teacher.id)).where(*filters)) or 0
    result = await db.execute(
        select(Teacher)
        .where(*filters)
        .order_by(Teacher.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    teachers = list(result.scalars().all())
    counts = await _course_count_map(db, [t.id for t in teachers])
    items = [
        AdminTeacherListItem.model_validate(t, from_attributes=True).model_copy(
            update={"course_count": counts.get(t.id, 0)}
        )
        for t in teachers
    ]
    return AdminTeacherListResponse(items=items, total=total, page=page, page_size=page_size)


async def get_teacher_detail(db: AsyncSession, teacher_id: int) -> AdminTeacherDetail | None:
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        return None
    # server-side onupdate/default（func.now()）在 flush 后会 expire，
    # 显式 refresh 避免异步 session 下同步访问触发 MissingGreenlet
    await db.refresh(teacher)
    counts = await _course_count_map(db, [teacher_id])
    rooms_map = await _load_rooms_for_teachers(db, [teacher_id])
    rooms = rooms_map.get(teacher_id, [])
    qualifications = teacher.qualifications or []
    detail = AdminTeacherDetail.model_validate(teacher, from_attributes=True)
    return detail.model_copy(
        update={
            "course_count": counts.get(teacher_id, 0),
            "qualifications": qualifications if isinstance(qualifications, list) else [],
            "room_ids": [r.id for r in rooms],
            "rooms": rooms,
        }
    )


async def create_teacher(db: AsyncSession, data: AdminTeacherCreate) -> Teacher:
    await _validate_room_ids(db, data.room_ids)
    teacher = Teacher(
        name=data.name,
        avatar=data.avatar,
        title=data.title,
        specialty=data.specialty,
        teaching_years=data.teaching_years,
        education=data.education,
        school=data.school,
        bio=data.bio,
        teaching_tags=_tags_to_db(data.teaching_tags),
        qualifications=[q.model_dump() for q in data.qualifications] or None,
        status=data.status,
    )
    db.add(teacher)
    await db.flush()
    await _sync_teacher_rooms(db, teacher.id, data.room_ids)
    return teacher


async def update_teacher(
    db: AsyncSession, teacher_id: int, data: AdminTeacherUpdate
) -> Teacher | None:
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "room_ids" in payload:
        await _validate_room_ids(db, payload.pop("room_ids") or [])
    if "teaching_tags" in payload:
        payload["teaching_tags"] = _tags_to_db(payload["teaching_tags"] or [])
    if "qualifications" in payload:
        quals = payload.pop("qualifications")
        payload["qualifications"] = quals or None
    for field, value in payload.items():
        setattr(teacher, field, value)
    await db.flush()
    if data.room_ids is not None:
        await _sync_teacher_rooms(db, teacher_id, data.room_ids)
    return teacher


async def delete_teacher(db: AsyncSession, teacher_id: int) -> str:
    """删除老师。返回 "ok"；不存在返回 "not_found"；存在排课返回 "has_schedules"。"""
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        return "not_found"
    schedule_count = await db.scalar(
        select(func.count(CourseSchedule.id)).where(CourseSchedule.teacher_id == teacher_id)
    )
    if schedule_count:
        return "has_schedules"
    await db.execute(sa_delete(TeacherRoom).where(TeacherRoom.teacher_id == teacher_id))
    await db.delete(teacher)
    return "ok"


async def toggle_status(db: AsyncSession, teacher_id: int, status: str) -> Teacher | None:
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        return None
    teacher.status = status
    return teacher


async def get_available_time_slots(db: AsyncSession, teacher_id: int) -> list | None:
    """获取老师可排课时间段。"""
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        return None
    if teacher.available_time_slots:
        return json.loads(teacher.available_time_slots)
    return []


async def update_available_time_slots(
    db: AsyncSession, teacher_id: int, time_slots: list | None
) -> bool:
    """更新老师可排课时间段。"""
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        return False
    teacher.available_time_slots = json.dumps(time_slots, ensure_ascii=False) if time_slots is not None else None
    await db.flush()
    return True

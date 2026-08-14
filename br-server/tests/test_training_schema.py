"""TrainingRoomDetailResponse schema 单元测试

验证培训室详情响应 schema 的字段构造、默认值及嵌套 tags 解析。
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError


class TestTrainingRoomDetailResponse:
    """TrainingRoomDetailResponse schema 测试"""

    def test_可以用所有必填字段构造_TrainingRoomDetailResponse(self):
        """验证使用所有必填字段可以成功构造"""
        from app.schemas.course import TrainingRoomDetailResponse

        data = {
            "id": 1,
            "name": "杭州培训中心",
            "description": "位于市中心的培训中心",
            "cover_image": "https://example.com/cover.jpg",
            "address": "杭州市西湖区文三路 100 号",
            "business_hours": "09:00-21:00",
            "status": "active",
            "room_type": "training",
            "min_price": Decimal("99.00"),
            "city_id": 10,
            "city_name": "杭州",
            "rating": Decimal("4.8"),
            "classroom_count": 5,
            "class_capacity": "200人",
            "teacher_count": 10,
            "total_students": 500,
            "teachers": [],
            "courses": [],
        }

        resp = TrainingRoomDetailResponse(**data)

        assert resp.id == 1
        assert resp.name == "杭州培训中心"
        assert resp.address == "杭州市西湖区文三路 100 号"
        assert resp.status == "active"
        assert resp.room_type == "training"
        assert resp.min_price == Decimal("99.00")
        assert resp.rating == Decimal("4.8")
        assert resp.classroom_count == 5
        assert resp.class_capacity == "200人"
        assert resp.teacher_count == 10
        assert resp.total_students == 500

    def test_teachers_and_courses_默认为空列表(self):
        """验证 teachers 和 courses 字段默认值为空列表"""
        from app.schemas.course import TrainingRoomDetailResponse

        data = {
            "id": 1,
            "name": "测试培训室",
            "address": "测试地址",
            "status": "active",
            "room_type": "training",
            "min_price": Decimal("50.00"),
            "rating": Decimal("4.0"),
            "classroom_count": 1,
            "class_capacity": "50人",
            "teacher_count": 1,
            "total_students": 10,
        }

        resp = TrainingRoomDetailResponse(**data)

        assert resp.teachers == []
        assert resp.courses == []
        assert resp.description is None
        assert resp.cover_image is None
        assert resp.business_hours is None
        assert resp.city_id is None
        assert resp.city_name is None

    def test_嵌套_CourseResponse_tags_解析(self):
        """验证嵌套的 CourseResponse 中 tags 字段可以正确解析逗号分隔字符串"""
        from app.schemas.course import CourseResponse, TrainingRoomDetailResponse, TeacherBrief

        teacher_data = {
            "id": 1,
            "name": "张老师",
            "avatar": "https://example.com/avatar.jpg",
            "title": "高级讲师",
            "rating": Decimal("4.9"),
        }

        course_data = {
            "id": 101,
            "name": "Python 基础课",
            "cover_image": "https://example.com/course.jpg",
            "teacher": teacher_data,
            "category": "编程",
            "price": Decimal("199.00"),
            "rating": Decimal("4.7"),
            "enrollment_count": 120,
            "schedule": "每周六 10:00-12:00",
            "tags": "编程,入门,Python",  # 逗号分隔字符串
            "status": "active",
            "room_id": 1,
            "room_name": "杭州培训中心",
        }

        data = {
            "id": 1,
            "name": "杭州培训中心",
            "address": "测试地址",
            "status": "active",
            "room_type": "training",
            "min_price": Decimal("99.00"),
            "rating": Decimal("4.8"),
            "classroom_count": 3,
            "class_capacity": "100人",
            "teacher_count": 5,
            "total_students": 200,
            "teachers": [teacher_data],
            "courses": [course_data],
        }

        resp = TrainingRoomDetailResponse(**data)

        # 验证 teachers 嵌套正确
        assert len(resp.teachers) == 1
        assert resp.teachers[0].name == "张老师"
        assert resp.teachers[0].rating == Decimal("4.9")

        # 验证 courses 嵌套正确，tags 从逗号分隔字符串解析为列表
        assert len(resp.courses) == 1
        assert resp.courses[0].name == "Python 基础课"
        assert resp.courses[0].tags == ["编程", "入门", "Python"]
        assert resp.courses[0].teacher.name == "张老师"

    def test_嵌套_CourseResponse_tags_为None时返回空列表(self):
        """验证嵌套 CourseResponse 的 tags 为 None 时解析为空列表"""
        from app.schemas.course import CourseResponse, TrainingRoomDetailResponse

        course_data = {
            "id": 102,
            "name": "数学课",
            "category": "数学",
            "price": Decimal("100.00"),
            "rating": Decimal("4.5"),
            "enrollment_count": 50,
            "tags": None,  # None 值
            "status": "active",
            "room_id": 1,
            "room_name": "测试培训室",
        }

        data = {
            "id": 1,
            "name": "测试培训室",
            "address": "测试地址",
            "status": "active",
            "room_type": "training",
            "min_price": Decimal("50.00"),
            "rating": Decimal("4.0"),
            "classroom_count": 1,
            "class_capacity": "50人",
            "teacher_count": 1,
            "total_students": 10,
            "courses": [course_data],
        }

        resp = TrainingRoomDetailResponse(**data)
        assert resp.courses[0].tags == []

    def test_缺少必填字段时抛出_ValidationError(self):
        """验证缺少必填字段时抛出 ValidationError"""
        from app.schemas.course import TrainingRoomDetailResponse

        # 只传部分字段，缺少 address、status 等必填字段
        with pytest.raises(ValidationError):
            TrainingRoomDetailResponse(id=1, name="测试")

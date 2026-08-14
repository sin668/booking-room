"""TDD 测试：验证 Teacher、Course 模型及 StudyRoom.room_type 字段存在。

此测试先于实现编写，应先失败（RED），再通过实现模型使其通过（GREEN）。
"""

import pytest
from sqlalchemy import inspect

from app.models import Course, StudyRoom, Teacher


class TestTeacherModel:
    """Teacher 模型结构验证。"""

    def test_teacher_tablename(self):
        assert Teacher.__tablename__ == "teachers"

    def test_teacher_has_expected_columns(self):
        mapper = inspect(Teacher)
        column_names = {col.key for col in mapper.columns}
        expected = {
            "id",
            "name",
            "avatar",
            "title",
            "rating",
            "created_at",
            "updated_at",
        }
        assert expected <= column_names, f"缺少列: {expected - column_names}"

    def test_teacher_name_not_nullable(self):
        col = inspect(Teacher).columns["name"]
        assert not col.nullable

    def test_teacher_rating_default_zero(self):
        col = inspect(Teacher).columns["rating"]
        assert col.default is not None or col.server_default is not None


class TestCourseModel:
    """Course 模型结构验证。"""

    def test_course_tablename(self):
        assert Course.__tablename__ == "courses"

    def test_course_has_expected_columns(self):
        mapper = inspect(Course)
        column_names = {col.key for col in mapper.columns}
        expected = {
            "id",
            "room_id",
            "teacher_id",
            "name",
            "cover_image",
            "category",
            "price",
            "rating",
            "enrollment_count",
            "schedule",
            "tags",
            "status",
            "is_hot",
            "sort_order",
            "created_at",
            "updated_at",
        }
        assert expected <= column_names, f"缺少列: {expected - column_names}"

    def test_course_room_id_not_nullable(self):
        col = inspect(Course).columns["room_id"]
        assert not col.nullable

    def test_course_teacher_id_nullable(self):
        col = inspect(Course).columns["teacher_id"]
        assert col.nullable

    def test_course_category_not_nullable(self):
        col = inspect(Course).columns["category"]
        assert not col.nullable

    def test_course_price_not_nullable(self):
        col = inspect(Course).columns["price"]
        assert not col.nullable


class TestStudyRoomRoomType:
    """StudyRoom.room_type 字段验证。"""

    def test_study_room_has_room_type(self):
        mapper = inspect(StudyRoom)
        column_names = {col.key for col in mapper.columns}
        assert "room_type" in column_names, "StudyRoom 缺少 room_type 字段"

    def test_study_room_room_type_default(self):
        col = inspect(StudyRoom).columns["room_type"]
        # default 或 server_default 至少有一个
        assert col.default is not None or col.server_default is not None

    def test_study_room_room_type_not_nullable(self):
        col = inspect(StudyRoom).columns["room_type"]
        assert not col.nullable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

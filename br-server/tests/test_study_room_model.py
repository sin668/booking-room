"""StudyRoom 模型单元测试——验证 rating 字段和 city 关系。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.study_room import StudyRoom


class TestStudyRoomModel:
    """验证 StudyRoom 模型新增的 rating 列与 city 关系。"""

    @pytest.mark.asyncio
    async def test_study_room_has_rating_column(self, db_session: AsyncSession):
        """StudyRoom 实例可以带 rating 字段创建，且默认值为 0。"""
        room = StudyRoom(
            name="测试自习室",
            address="测试地址",
            rating=4.5,
        )
        db_session.add(room)
        await db_session.flush()

        assert room.rating == 4.5

    @pytest.mark.asyncio
    async def test_study_room_rating_default(self, db_session: AsyncSession):
        """rating 字段缺省时默认值为 0.0。"""
        room = StudyRoom(
            name="默认评分自习室",
            address="测试地址",
        )
        db_session.add(room)
        await db_session.flush()

        assert float(room.rating) == 0.0

    @pytest.mark.asyncio
    async def test_study_room_has_city_relationship(self, db_session: AsyncSession):
        """StudyRoom 模型上存在 city 关系，且可正确加载关联的 City。"""
        city = City(name="北京", province="北京市")
        db_session.add(city)
        await db_session.flush()

        room = StudyRoom(
            name="有城市关联的自习室",
            address="北京某地",
            city_id=city.id,
        )
        db_session.add(room)
        await db_session.flush()

        # 刷新以加载 relationship
        await db_session.refresh(room, attribute_names=["city"])
        assert room.city is not None
        assert room.city.name == "北京"

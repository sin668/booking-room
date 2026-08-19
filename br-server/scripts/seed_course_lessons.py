# -*- coding: utf-8 -*-
"""
种子数据脚本：为所有活跃课程生成课时数据。

使用方式：
    cd br-server && conda activate booking-room
    python scripts/seed_course_lessons.py
"""

import asyncio
import random
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, delete

from app.core.database import async_session, engine, Base
from app.models.course import Course
from app.models.course_lesson import CourseLesson


# 课时标题模板
LESSON_TITLE_TEMPLATES = [
    "第{order}讲：课程导论",
    "第{order}讲：核心概念",
    "第{order}讲：基础入门",
    "第{order}讲：实战演练",
    "第{order}讲：案例分析",
    "第{order}讲：进阶技巧",
    "第{order}讲：常见问题解析",
    "第{order}讲：项目实践",
    "第{order}讲：性能优化",
    "第{order}讲：总结与展望",
    "第{order}讲：工具与环境搭建",
    "第{order}讲：高级特性",
]

LESSON_DESCRIPTION_TEMPLATES = [
    "本节课将介绍{course_name}的基本概念和背景知识。",
    "深入学习{course_name}中的关键知识点。",
    "通过实际案例掌握{course_name}的核心技能。",
    "探讨{course_name}的最佳实践和常见陷阱。",
    "动手实操，巩固{course_name}所学内容。",
    None,  # 部分课时不设置描述
]


async def seed_course_lessons() -> None:
    """为所有活跃课程生成课时种子数据。"""

    # 确保表已创建
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 先清理已有课时数据（幂等执行）
        await session.execute(delete(CourseLesson))

        # 查询所有活跃课程
        result = await session.execute(
            select(Course).where(Course.status == "active")
        )
        courses = result.scalars().all()

        if not courses:
            print("⚠️  没有找到 status='active' 的课程，跳过种子数据生成。")
            return

        total_lessons = 0

        for course in courses:
            lesson_count = random.randint(4, 12)
            titles = random.sample(
                LESSON_TITLE_TEMPLATES,
                min(lesson_count, len(LESSON_TITLE_TEMPLATES)),
            )
            # 如果需要的课时数超过模板数，补充通用标题
            while len(titles) < lesson_count:
                titles.append(f"第{len(titles)+1}讲：扩展内容")

            for i, title_template in enumerate(titles):
                title = title_template.format(order=i + 1)
                desc_template = random.choice(LESSON_DESCRIPTION_TEMPLATES)
                description = (
                    desc_template.format(course_name=course.name)
                    if desc_template
                    else None
                )
                lesson = CourseLesson(
                    course_id=course.id,
                    title=title,
                    description=description,
                    duration_minutes=random.randint(30, 90),
                    sort_order=i,
                    is_free_preview=(i == 0),
                )
                session.add(lesson)
                total_lessons += 1

            print(f"✅ 课程「{course.name}」(id={course.id}) 生成 {lesson_count} 个课时")

        await session.commit()
        print(f"\n🎉 共生成 {total_lessons} 个课时，覆盖 {len(courses)} 门课程。")


if __name__ == "__main__":
    asyncio.run(seed_course_lessons())

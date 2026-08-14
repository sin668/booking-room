---
comet_change: training-room-overview
role: technical-design
canonical_spec: openspec
---

# 培训室概况功能 — 技术设计文档

## 1. 概述

本文档是 `training-room-overview` change 的深度技术设计，基于 open 阶段的 proposal.md、specs 和 design.md，细化后端 Service 实现、API Response Schema、前端 detail.vue 条件渲染逻辑、测试策略和 Bug 防护措施。

参见 `openspec/changes/training-room-overview/design.md` 了解高层架构决策。

## 2. 后端 Service 实现细节

### 2.1 `get_training_room_detail(room_id: int)` 方法

位置：`br-server/app/services/training_service.py`

```python
async def get_training_room_detail(self, room_id: int) -> Optional[TrainingRoomDetailResponse]:
    # Step 1: 查询房间，验证 room_type
    room = await self.db.execute(
        select(StudyRoom).where(
            StudyRoom.id == room_id,
            StudyRoom.room_type.in_(['training', 'comprehensive'])
        )
    )
    room_obj = room.scalar_one_or_none()
    if not room_obj:
        return None  # 路由层返回 404

    # Step 2: 查询该房间下 status=active 的课程，LEFT JOIN teachers
    courses_result = await self.db.execute(
        select(Course, Teacher)
        .outerjoin(Teacher, Course.teacher_id == Teacher.id)
        .where(Course.room_id == room_id, Course.status == 'active')
        .order_by(Course.sort_order)
    )
    rows = courses_result.all()

    # Step 3: 组装课程列表 + 去重教师
    courses_data = []
    teachers_map = {}  # teacher_id -> TeacherResponse
    total_students = 0

    for course, teacher in rows:
        teacher_response = None
        if teacher:
            if teacher.id not in teachers_map:
                teachers_map[teacher.id] = TeacherResponse(
                    id=teacher.id, name=teacher.name,
                    avatar=teacher.avatar, title=teacher.title,
                    rating=float(teacher.rating)
                )
            teacher_response = teachers_map[teacher.id]

        tags = course.tags.split(',') if course.tags else []
        courses_data.append(CourseResponse(
            id=course.id, name=course.name,
            cover_image=course.cover_image,
            teacher=teacher_response,
            category=course.category,
            price=float(course.price),
            rating=float(course.rating),
            enrollment_count=course.enrollment_count,
            schedule=course.schedule,
            tags=tags,
            status=course.status,
            room_id=course.room_id,
            room_name=room_obj.name,
        ))
        total_students += course.enrollment_count

    # Step 4: 聚合统计
    classroom_count = len(courses_data)
    teacher_count = len(teachers_map)

    return TrainingRoomDetailResponse(
        id=room_obj.id, name=room_obj.name,
        description=room_obj.description,
        cover_image=room_obj.cover_image,
        address=room_obj.address,
        business_hours=room_obj.business_hours,
        status=room_obj.status,
        room_type=room_obj.room_type,
        min_price=float(room_obj.min_price or 0),
        city_id=room_obj.city_id,
        city_name=room_obj.city.name if room_obj.city else None,
        rating=float(room_obj.rating or 0),
        classroom_count=classroom_count,
        class_capacity="8-12",
        teacher_count=teacher_count,
        total_students=total_students,
        teachers=list(teachers_map.values()),
        courses=courses_data,
    )
```

### 2.2 关键实现要点

- **教师去重**：使用 `teachers_map` 字典按 `teacher_id` 去重，同一教师的多门课程只出现一次
- **LEFT JOIN**：使用 `outerjoin` 确保未关联教师的课程也被查询到（`teacher` 为 None）
- **tags 解析**：`course.tags.split(',') if course.tags else []`，空字符串或 null 返回空数组
- **排序**：按 `Course.sort_order` 排序，确保课程列表顺序一致
- **统计聚合**：`classroom_count` 取课程数（非物理教室数，因为数据库无独立教室实体），`total_students` 取所有课程 `enrollment_count` 之和

## 3. API Response Schema

位置：`br-server/app/schemas/course.py`（复用 training-course-list change 已定义的 TeacherResponse 和 CourseResponse）

```python
class TrainingRoomDetailResponse(BaseModel):
    # 房间基本信息
    id: int
    name: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    address: str
    business_hours: Optional[str] = None
    status: str
    room_type: str
    min_price: float
    city_id: Optional[int] = None
    city_name: Optional[str] = None
    rating: float

    # 教室概况统计
    classroom_count: int          # 培训教室数（= active 课程数）
    class_capacity: str           # 小班容量 "8-12"
    teacher_count: int            # 认证讲师数（去重教师数）
    total_students: int           # 累计学员数（enrollment_count 求和）

    # 名师团队
    teachers: List[TeacherResponse]

    # 课程列表
    courses: List[CourseResponse]
```

## 4. API 路由实现

位置：`br-server/app/api/routes/training.py`

```python
@router.get("/{room_id}")
async def get_training_room_detail(
    room_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = TrainingService(db)
    result = await service.get_training_room_detail(room_id)
    if not result:
        raise HTTPException(status_code=404, detail="培训室不存在或不是培训室类型")
    return result
```

**注意**：路由使用 `@router.get("/{room_id}")` 而非 `@router.get("/{room_id}/")`，不使用尾部斜杠（参考 bug-fixed.md BUG-22）。

## 5. 前端 detail.vue 实现细节

### 5.1 data() 新增

```javascript
data() {
  return {
    // 现有字段...
    trainingData: null,   // 培训室详情数据
    roomType: '',         // 房间类型 study/training/comprehensive
  }
}
```

### 5.2 loadData() 重构

```javascript
async loadData() {
  this.loading = true
  try {
    // Step 1: 获取房间基本信息（含 room_type）
    await this.loadRoom()
    if (!this.room || !this.room.id) return

    this.roomType = this.room.room_type || 'study'

    // Step 2: 根据 room_type 条件调用后续 API
    const tasks = []
    if (this.roomType === 'study' || this.roomType === 'comprehensive') {
      tasks.push(this.loadSeatStats())
    }
    if (this.roomType === 'training' || this.roomType === 'comprehensive') {
      tasks.push(this.loadTrainingDetail())
    }
    await Promise.all(tasks)
  } finally {
    this.loading = false
  }
},

async loadTrainingDetail() {
  try {
    const data = await getTrainingRoomDetail(this.roomId)
    this.trainingData = data || null
  } catch {
    this.trainingData = null
  }
},
```

### 5.3 computed 属性

```javascript
computed: {
  // 现有 computed...

  isStudyRoom() {
    return this.roomType === 'study'
  },
  isTrainingRoom() {
    return this.roomType === 'training'
  },
  isComprehensiveRoom() {
    return this.roomType === 'comprehensive'
  },
  trainingStats() {
    if (!this.trainingData) return null
    return {
      classroom_count: this.trainingData.classroom_count || 0,
      class_capacity: this.trainingData.class_capacity || '8-12',
      teacher_count: this.trainingData.teacher_count || 0,
      total_students: this.trainingData.total_students || 0,
    }
  },
  teachers() {
    return this.trainingData?.teachers || []
  },
  trainingCourses() {
    return this.trainingData?.courses || []
  },
}
```

### 5.4 模板条件渲染结构

```html
<!-- 培训室简介（仅 training/comprehensive） -->
<view v-if="isTrainingRoom || isComprehensiveRoom" class="section animate-in">
  <view class="section-header">
    <text class="section-title">培训室简介</text>
  </view>
  <text class="intro-text">{{ room.description || '暂无简介' }}</text>
</view>

<!-- 环境照片（所有类型，现有逻辑保持） -->

<!-- 座位概况（仅 study/comprehensive） -->
<view v-if="isStudyRoom || isComprehensiveRoom" class="section seat-section">
  <!-- 现有座位概况内容 -->
</view>

<!-- 教室概况（仅 training/comprehensive，替换座位概况位置） -->
<view v-if="isTrainingRoom || isComprehensiveRoom" class="section classroom-section">
  <view class="section-header">
    <text class="section-title">教室概况</text>
  </view>
  <view class="stats-grid">
    <!-- 2x2 网格：培训教室数、小班容量、认证讲师、累计学员 -->
  </view>
</view>

<!-- 名师团队（仅 training/comprehensive） -->
<view v-if="isTrainingRoom || isComprehensiveRoom" class="section">
  <view class="section-header">
    <text class="section-title">名师团队</text>
  </view>
  <scroll-view scroll-x :show-scrollbar="false" class="teacher-scroll">
    <view class="teacher-list">
      <view v-for="teacher in teachers" :key="teacher.id" class="teacher-card">
        <!-- 教师头像、姓名、头衔、评分 -->
      </view>
    </view>
  </scroll-view>
</view>

<!-- 本培训室课程（仅 training/comprehensive） -->
<view v-if="isTrainingRoom || isComprehensiveRoom" class="section">
  <view class="section-header">
    <text class="section-title">本培训室课程</text>
    <text class="section-sub">共{{ trainingCourses.length }}门</text>
  </view>
  <view class="course-list">
    <view v-for="course in trainingCourses" :key="course.id" class="course-card">
      <!-- 课程封面图、名称、状态标签、教师信息、排课时间、价格 -->
    </view>
  </view>
</view>
```

### 5.5 底部操作栏条件渲染

```html
<view class="bottom-bar">
  <!-- 心状关注按钮（所有类型通用） -->
  <view class="fav-btn" @tap="onToggleFav">
    <text :class="['heart-icon', { active: isFav }]">♥</text>
  </view>

  <!-- 自习室：立即预约 -->
  <view v-if="isStudyRoom" class="book-btn" @tap="onBook">
    <text class="book-btn-sub">{{ seatStats.available }} 个座位可选</text>
    <text class="book-btn-text">立即预约</text>
  </view>

  <!-- 培训室：返回课程 -->
  <view v-else-if="isTrainingRoom" class="back-btn" @tap="onBackToCourses">
    <text class="back-btn-text">返回课程</text>
  </view>

  <!-- 综合室：预约自习室 -->
  <view v-else-if="isComprehensiveRoom" class="book-btn" @tap="onBookStudy">
    <text class="book-btn-sub">{{ seatStats.available }} 个座位可选</text>
    <text class="book-btn-text">预约自习室</text>
  </view>
</view>
```

### 5.6 新增方法

```javascript
onBackToCourses() {
  uni.navigateTo({ url: '/pages/training/index' })
},
onBookStudy() {
  uni.navigateTo({ url: '/pages/booking/seat-select?room_id=' + this.roomId })
},
```

## 6. 测试策略

### 6.1 后端测试

在 `br-server/tests/test_training_api.py` 新增以下测试用例：

| 测试场景 | 验证点 |
|---------|--------|
| 正常请求培训室详情 | 响应字段完整性（房间信息、teachers、courses、统计字段） |
| 综合室详情请求 | 响应结构与培训室一致 |
| 请求自习室 room_id | 返回 404 |
| 请求不存在的 room_id | 返回 404 |
| 教师去重 | 多门课程关联同一教师时 teachers 数组去重 |
| 空课程场景 | teachers 和 courses 数组为空 |
| tags 解析 | 逗号分隔字符串正确解析为数组 |
| 无教师课程 | teacher 字段为 null |

### 6.2 前端验证

- `npm run build` 确保无编译错误
- 验证自习室详情页行为与修改前完全一致

## 7. Bug 防护清单

| Bug # | 问题描述 | 防护措施 |
|-------|---------|---------|
| BUG-13 | page_size=100 列表接口 422 | 使用详情接口 `GET /api/v1/training/rooms/{room_id}` |
| BUG-14 | onMounted 从 @dcloudio/uni-app 导入错误 | Vue3 钩子从 `vue` 包导入，uni-app 钩子从 `@dcloudio/uni-app` 导入 |
| BUG-20 | WXML 中 &lt;/&gt; 导致编译错误 | 不使用 HTML 实体，用 Unicode 字符替代 |
| BUG-22 | API 尾部斜杠导致 307/404 | 路由定义 `@router.get("/{room_id}")` 不使用尾部斜杠 |

## 8. 依赖关系

本 change 依赖 `training-course-list` change 的以下后端基础设施：
- `study_rooms` 表的 `room_type` 列（枚举 study/training/comprehensive）
- `teachers` 表（id, name, avatar, title, rating, created_at, updated_at）
- `courses` 表（id, room_id, teacher_id, name, cover_image, category, price, rating, enrollment_count, schedule, tags, status, is_hot, sort_order, created_at, updated_at）
- `TeacherResponse` schema（在 `schemas/teacher.py`）
- `CourseResponse` schema（在 `schemas/course.py`）
- `training_router` 在 `main.py` 中的注册

两个 change 可并行开发代码，但运行时验证需要 `training-course-list` 的数据库迁移已执行。

## 9. 边界条件

| 边界场景 | 处理方式 |
|---------|---------|
| room_type 字段缺失（旧数据） | 默认为 `study`，保持现有自习室行为 |
| 培训室无课程 | teachers 和 courses 为空数组，教室概况统计全为 0 |
| 课程 tags 为 null 或空字符串 | tags 返回空数组 `[]` |
| 课程未关联教师 | teacher 字段为 null |
| 综合室座位 API 失败 | catch 错误，seatStatsData 保持 null，座位概况显示"座位状态加载中" |
| 培训室详情 API 失败 | catch 错误，trainingData 保持 null，培训相关区块显示空状态 |

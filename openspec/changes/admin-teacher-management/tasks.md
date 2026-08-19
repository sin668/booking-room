# Tasks: admin-teacher-management

## 1. br-server 数据模型与迁移
- [x] 1.1 Teacher 模型新增 specialty/teaching_years/education/school/status/teaching_tags/qualifications 字段
- [x] 1.2 新建 TeacherRoom 模型（teacher_rooms 表，唯一约束 + 级联删除），注册到 models/__init__.py
- [x] 1.3 生成 Alembic 迁移（down_revision=c2d3e4f5a6b7）并在测试库执行验证

## 2. br-server 管理端 API
- [x] 2.1 新建 schemas/admin_teacher.py（Create/Update/Detail/List/StatusUpdate）
- [x] 2.2 新建 services/admin_teacher_service.py（分页列表含 course_count、详情、新增、编辑、删除、状态切换，room_type 校验）
- [x] 2.3 重写 routes/admin_teacher.py 为完整 CRUD + require_admin_permission（保持 GET 列表 items 兼容排课下拉）
- [x] 2.4 seed_admin.py 增加老师管理菜单（path 基路径规范）与按钮权限种子

## 3. br-server C 端接口扩展
- [x] 3.1 schemas/teacher.py TeacherDetailResponse 增加新字段与 rooms
- [x] 3.2 teacher_service 返回新字段、所属房间；停用老师返回 None（C 端 404）

## 4. br-server 测试
- [x] 4.1 新增 test_api_admin_teacher.py：列表/详情/新增/编辑/删除（含排课拒绝）/状态/room_type 校验/权限
- [x] 4.2 更新/补充 teacher 详情接口测试（新字段）
- [x] 4.3 全量回归 pytest

## 5. br-admin 老师管理
- [x] 5.1 src/api/teacher/index.ts 类型与 CRUD 封装（GET force: true）
- [x] 5.2 router/modules/training.ts 增加 teachers 列表与 teachers/edit 隐藏路由（hideInMenu）
- [x] 5.3 views/training/teachers/index.vue 列表页（搜索表单 + 表格 + 操作列，复用 tableBuilders/TableAction）
- [x] 5.4 views/training/teachers/edit.vue 新增/编辑页（基本信息/头像/简介/资质认证/教学特色/多选所属房间），页面跳转模式保存返回
- [x] 5.5 核对 naive.ts 组件注册（BUG-23）与构建通过

## 6. br-app 教师简介页
- [x] 6.1 profile.vue 副标题改为 专业方向·教龄·学历 拼接
- [x] 6.2 资质认证/教学特色改读接口数据，空则隐藏区块

## 7. 验证与提交
- [x] 7.1 br-admin build、br-app build（H5）
- [x] 7.2 后端 seed 执行 + 接口冒烟（老师 CRUD、C 端详情）
- [ ] 7.3 提交并推送 GitHub（main）

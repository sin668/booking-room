# Tasks: super-admin-data-readonly

- [x] 1. 后端助手与单测：data_scope.py 新增 readonly_creators / ensure_writable（含座位/预约/评价随属入口）；test_data_scope.py 新增写保护 403、readonly 标志、超管/legacy/本人/存量可写、降级恢复等场景测试
- [x] 2. 内容型五类接入：room/course/activity/coupon/teacher 路由写端点调用 ensure_writable；响应 schema 与列表/详情服务补 readonly 字段（course 含课时排课子资源写保护）
- [x] 3. 随属记录接入：seat（嵌套+扁平）、booking（cancel/confirm）、review（status/reply）写保护；座位/预约/评价响应补 readonly
- [x] 4. 前端基础设施：BasicTable rowClassName 透传（props.ts + types/table.ts）、全局 .readonly-row 置灰样式、8 个 API item 类型补 readonly
- [x] 5. 前端 8 个列表页：room/courses/activity/coupon/teachers/booking/reviews/seats 行置灰与修改类按钮禁用（查看入口保留；座位页新增按钮禁用）
- [x] 6. 回归与验收：全量 pytest 对照 19 基线零回归；br-admin pnpm build；真实环境冒烟（非超管置灰只读 + API 403，超管不受影响）
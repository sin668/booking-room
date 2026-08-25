## 验证报告

### 变更概述
修复 `br-server/app/services/course_booking_service.py` 中 `create_course_booking` 方法 5 处 dict 属性访问错误。

### 验证项

1. **语法检查** — PASS：`ast.parse()` 通过
2. **模块导入** — PASS：`CourseBookingService` 可正常导入
3. **Diff 审查** — PASS：仅修改 1 个文件 5 行，全部为 `course.xxx` → `course["xxx"]` 转换
4. **现有测试** — PASS（无回归）：1 passed, 16 skipped, 7 failed（7 个失败为预存问题，`calculate_price` 签名变更但测试未同步，与本次修复无关）
5. **遗漏检查** — PASS：文件中其余 `course.` 引用均在 `get_course_with_lessons` 方法中，`course` 为 ORM 对象，无需修改

### 结论
修复正确，无回归风险。

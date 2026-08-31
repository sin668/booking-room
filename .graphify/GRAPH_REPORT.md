# Graph Report - .  (2026-08-31)

## Corpus Check
- Large corpus: 1035 files · ~542,152 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 5423 nodes · 11477 edges · 213 communities detected
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 2524 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output
- Edge kinds: contains: 2774 · uses: 2524 · ON_BRANCH: 1280 · MODIFIES: 1243 · calls: 1018 · method: 686 · rationale_for: 619 · PARENT_OF: 408 · imports_from: 324 · inherits: 311 · imports: 283 · re_exports: 7


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 1035 · Candidates: 1469
- Excluded: 0 untracked · 89184 ignored · 0 sensitive · 24 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `0148cfd`
- Compare this hash to `git rev-parse HEAD` before trusting freshness-sensitive graph output.
## God Nodes (most connected - your core abstractions)
1. `StudyRoom` - 246 edges
2. `Settings` - 224 edges
3. `Course` - 165 edges
4. `Booking` - 143 edges
5. `Teacher` - 123 edges
6. `Seat` - 110 edges
7. `UserCoupon` - 99 edges
8. `Coupon` - 96 edges
9. `City` - 92 edges
10. `CourseLesson` - 82 edges

## Surprising Connections (you probably didn't know these)
- `Create a booking with conflict detection.      Note: For MVP, conflict detection` --uses--> `Booking`  [INFERRED]
  br-server/app/services/booking_service.py → br-server/app/models/booking.py
- `List bookings for the current user with pagination.` --uses--> `Booking`  [INFERRED]
  br-server/app/services/booking_service.py → br-server/app/models/booking.py
- `Base exception for booking operations.` --uses--> `Booking`  [INFERRED]
  br-server/app/services/booking_service.py → br-server/app/models/booking.py
- `Get a booking detail. Only own bookings are visible.` --uses--> `Booking`  [INFERRED]
  br-server/app/services/booking_service.py → br-server/app/models/booking.py
- `Cancel own paid future booking and refund the remaining amount to wallet.` --uses--> `Booking`  [INFERRED]
  br-server/app/services/booking_service.py → br-server/app/models/booking.py

## Communities

### Community 0 - "Booking Service Tests"
Cohesion: 0.03
Nodes (117): dev, main, 020ddd3 debug: 延期功能前后端参数传递添加调试日志, 04f0a66 feat: 新增订单状态定时转换任务, 051c8b1 fix: 修复开课日期不显示和过期课时禁用逻辑 - 后端返回lesson_schedules数据, 0605022 fix: 课程编辑页与列表页在原 tab 内互相跳转，不再新开标签页, 0b33239 feat: 统计区域添加连续学习天数显示, 0e90f58 fix: 排课更新后强制刷新列表数据 (+109 more)

### Community 1 - "Teacher Management Tests"
Cohesion: 0.05
Nodes (152): feature/20260814/training-course-list, feature/20260817/course-booking, feature/20260817/course-detail-page, feature/20260817/teacher-profile-page, 008166a chore: Comet build→verify transition — all guard checks passed, 0191aac fix: redirect expired admin sessions to login, 037946c feat: add study record frontend page, 061bda0 feat: 实现 seat-select 页面 viewMode 只读查看模式 (+144 more)

### Community 2 - "Booking Cancellation Tests"
Cohesion: 0.03
Nodes (92): AdminContext, Base, City, Course, 老师与培训室/综合室的多对多关联表。      room_id 仅允许关联 study_rooms 中 room_type 为 training 或 compr, TeacherRoom, Teacher, Admin course management service. (+84 more)

### Community 3 - "Wallet Service Tests"
Cohesion: 0.04
Nodes (61): Booking, Seat, StudyRoom, PaymentProviderUnavailableError, CouponError, CouponNotFoundError, 统一校验卡券适用范围。座位区域由预约查询携带 seat 后单独判断。, Return set of seat_ids that have overlapping confirmed bookings. (+53 more)

### Community 4 - "Booking Payment Tests"
Cohesion: 0.04
Nodes (69): BaseModel, AdminCurrentResponse, AdminLoginRequest, AdminMessageResponse, AdminPasswordUpdate, AdminPermissionItem, AdminProfileUpdate, AdminTokenResponse (+61 more)

### Community 5 - "Booking Payment Tests"
Cohesion: 0.04
Nodes (54): Activity, ActivityCoupon, Coupon, UserCoupon, ActivityCouponClaimError, ActivityCouponClaimResult, ActivityCouponError, ActivityCouponPublishError (+46 more)

### Community 6 - "Token Verification"
Cohesion: 0.03
Nodes (5): ae1887e merge: admin RBAC dynamic settings, c623596 feat: add admin RBAC dynamic settings, columns, setting, add_admin_rbac_tables  Revision ID: b7e4a9c1d2f3 Revises: a8c3f1b2d4e5 Create Da

### Community 7 - "Room Management Tests"
Cohesion: 0.10
Nodes (53): Exception, WalletRepository, Booking direct payment orchestration., Verify a WeChat callback and mark a booking payment as paid once., Query due pending WeChat bookings and advance their payment state., Base exception for booking payment operations., Service for booking WeChat payment creation and callbacks., Create a WeChat JSAPI payment order for a pending booking. (+45 more)

### Community 8 - "Teacher Management Tests"
Cohesion: 0.05
Nodes (26): routes, routes, routes, routes, routes, routes, routes, routes (+18 more)

### Community 9 - "Booking Payment Tests"
Cohesion: 0.04
Nodes (41): 14c7316 Merge branch 'implement-wechat-quick-login-phone-binding' into main, 6daf2cb feat: add username profile settings, a8157af feat: add account security settings, b3ae959 feat: implement wechat quick login, d4aefe4 登录有效期调整为 3 天, change_password(), deactivate_account(), get_account_security() (+33 more)

### Community 10 - "Auth & Login Tests"
Cohesion: 0.04
Nodes (24): 071ac5f chore: add implementation plan for training-room-overview, 0b53f3b 优化UI, 1ab6fd7 polish: refine training page TAB navigation for a more refined look, 2323e70 feat: implement course detail API with TDD, 3590666 Merge branch 'feature/20260814/training-room-overview' into main, 42c7c58 fix: commit missing Alembic migration file for training tables, 4c94688 feat: 为 StudyRoom 添加 rating 列和 city 关系，含迁移, 681b536 feat: add training API module (+16 more)

### Community 11 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (65): 0148cfd feat: br-app课程相关页面仅展示固定班课排课 - training_service全部C端查询(培训室列表热门课程/培训室详情/课程列表/课程详情/相关课程)排课JOIN限定schedule_type=fixed - get_course_with_lessons(课程预约页)排课JOIN限定fixed并按创建时间取最早一条 - 定制课时排课记录不在C端课程页面展示，订单页面不受影响, 2365213 fix: 修复admin取消pending_confirm订单时MissingGreenlet错误 - 移除admin_cancel_booking中不必要的with_for_update()行锁 - WalletTransaction字段改为构造函数直接传参替代setattr, 3486c32 docs: bug-fixed.md 新增 BUG-26 Admin取消待确认订单MissingGreenlet错误, 408d499 fix: admin_confirm_booking统一使用admin_get_booking重新查询构建响应 - 与admin_cancel_booking相同模式避免flush后MissingGreenlet, 5ec9d70 feat: course_schedules新增schedule_type字段 + 1V1定制排课延迟到确认时创建 - Model: CourseSchedule新增schedule_type(fixed/custom)字段 - Migration: 添加schedule_type列(server_default=fixed) - create_course_booking: 1V1定制不再写入排课表，仅将用户选择的日期/时间段存入booking记录 - admin_confirm_booking: 确认1V1定制时才创建schedule_type=custom的排课记录和课时记录 - admin_confirm_booking: 查询固定班课开始日期时过滤schedule_type=fixed, 8bd8340 feat: 1V1私人定制待确认订单流程 + Admin订单列表UI改造 - 后端: 1V1定制创建时设为pending_confirm状态 - 后端: 新增admin确认API(根据时间变更为pending或confirmed) - 后端: pending_confirm订单取消支持全额退款 - 后端: admin列表返回user_nickname替代user_id - Admin: 状态文案更新(已确认→进行中/pending→待开始) - Admin: 新增待确认状态，确认/取消按钮 - Admin: 去掉已确认订单取消按钮，pending订单增加取消按钮 - App: pending_confirm订单显示在待开始TAB - App: 新增pending_confirm状态样式(橙色主题), 8f9eaeb feat: bookings新增time_slots/teacher_id字段+确认订单按预约日期判断状态+排课列表显示类型+确认/取消按钮直接展示 - Booking模型+迁移b9c0d1e2f3a4: 新增time_slots(JSON)和teacher_id，对应course_schedules同名字段 - create_course_booking: 1V1定制保存用户所选时间段(时间槽)及排课授课老师到订单 - admin_confirm_booking: 当前日期>=预约日期→进行中，当前日期<预约日期→待开始 - _create_custom_schedule_on_confirm: 定制排课记录使用订单的time_slots和teacher_id - CourseScheduleResponse新增schedule_type，排课管理列表新增类型列(固定班课/定制课时) - 预约列表确认/取消按钮从更多下拉菜单改为直接展示, 986f1f0 fix: admin_cancel_booking统一使用admin_get_booking重新查询构建响应 - 避免flush后ORM对象状态导致MissingGreenlet错误 (+57 more)

### Community 12 - "SMS & Captcha Tests"
Cohesion: 0.04
Nodes (49): RoomFollow, API tests for current-user followed study rooms., GET without follow_type defaults to 'room'., GET with follow_type=course returns empty list (current phase)., GET with invalid follow_type returns 422., POST with follow_type=course validates against courses table., POST with invalid follow_type returns 422., DELETE with follow_type=course only deletes course follows. (+41 more)

### Community 13 - "Booking System Core"
Cohesion: 0.06
Nodes (47): AdminCouponItem, buildActivityCouponFormItem(), buildActivitySearchSchemas(), buildActivityTableColumns(), buildBookingSearchSchemas(), buildBookingTableColumns(), buildRoomSearchSchemas(), buildRoomTableColumns() (+39 more)

### Community 14 - "Booking Data Models"
Cohesion: 0.03
Nodes (20): 02a1920 fix: resolve menu icons, directory paths, and hidden menu filtering (BUG-19), 2f06520 merge: unified User-AdminUser model with user management CRUD, 9093d5e docs: archive merge-users-admin-users openspec and sync specs, c069a02 feat: unify user access control — remove user_type filtering from auth, Test creating app user defaults user_type to 'app, Test User.roles relationship returns associated AdminRole, Test creating admin user sets user_type='admin, Test same phone can't create two users (+12 more)

### Community 15 - "Auth & Login Tests"
Cohesion: 0.04
Nodes (39): ADMIN_NATIVE_META, AdminPageParams, AdminPageResponse, BasicTableResult, compactQuery(), normalizePageParams(), toBasicTableResult(), BusinessSelectOption (+31 more)

### Community 16 - "Teacher Management Tests"
Cohesion: 0.06
Nodes (36): ActivityAdminResponse, ActivityCouponAdminResponse, ActivityCouponClaimResponse, ActivityCouponClaimUserCouponResponse, ActivityCouponInput, ActivityCouponPublicResponse, ActivityCouponTemplateResponse, ActivityCreate (+28 more)

### Community 17 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (36): { apiUrl, urlPrefix }, mockAdapter, { useMock, loggerMock }, ContentTypeEnum, RequestEnum, ResultEnum, IAsyncRouteState, IScreenLockState (+28 more)

### Community 18 - "Auth Service Layer"
Cohesion: 0.08
Nodes (37): bind_wechat_phone(), bind_wechat_phone_by_sms(), get_me(), login(), logout(), Authenticate or create an app user with a WeChat mini program code., Bind a phone obtained from WeChat phone authorization code., Bind a phone to a WeChat user with SMS fallback verification. (+29 more)

### Community 19 - "Booking System Core"
Cohesion: 0.05
Nodes (27): 02b3b93 feat: add course-detail page with all sections (7.1-7.8), 04745c9 chore: archive course-booking, 0fc7746 chore: add teacher-profile-page OpenSpec artifacts and design doc, 148395b feat(br-app): add course detail navigation from training list page, 3437127 test(task-6): 课程详情+关注完整测试，实现 list course follows, 38a606f chore: archive course-detail-page change, 45e5bef feat: extend Course and Booking models for course booking, 7180f81 fix: resolve alembic migration cycle by assigning unique revision ID e7f8a9b0c1d2 (+19 more)

### Community 20 - "Room Management Tests"
Cohesion: 0.07
Nodes (39): BaseSettings, Return missing mini program login settings without exposing values., Whether WeChat mini program login is enabled and configured., Raise a sanitized error if WeChat mini program login cannot be used., Return the normalized upload storage driver., Return missing OSS setting names without exposing configured values., Raise a sanitized error if upload storage cannot be used., Application settings loaded from environment variables and .env file. (+31 more)

### Community 21 - "SMS & Captcha Tests"
Cohesion: 0.05
Nodes (28): Alova, result, TypeConsole, TypeOrderLarge, TypeSaleroom, TypeVisits, doCustomTimes(), pagination() (+20 more)

### Community 22 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (43): AliyunSMSProvider, Aliyun Dysms API client for sending SMS verification codes., mock_redis(), Unit tests for SMS service (extended coverage)., Second send within 60 s is rejected with 429., The 11th send in one day is rejected with 429., Return a mock async Redis client., Invalid captcha token returns 400. (+35 more)

### Community 23 - "Database Config"
Cohesion: 0.08
Nodes (50): admin_cancel_booking(), admin_confirm_booking(), admin_get_booking(), admin_list_bookings(), BookingAlreadyCancelledError, BookingCancellationNotAllowedError, BookingConflictError, BookingCouponUnavailableError (+42 more)

### Community 24 - "Auth & Login Tests"
Cohesion: 0.04
Nodes (12): 7721d2b feat: 自习室新建/编辑改为页面跳转，列表新增城市/类型列与过滤，支持环境图片与上架状态, 7d4de92 chore: 房间管理模块文案「自习室」统一替换为「学习室」, routes, admin_get_room(), admin_list_rooms(), create_room(), delete_room(), get_study_room() (+4 more)

### Community 25 - "JWT Token Tests"
Cohesion: 0.07
Nodes (32): Base, get_db(), FastAPI dependency that provides an async database session., DeclarativeBase, SystemSetting, UserIdentityVerification, User, _create_access_token() (+24 more)

### Community 26 - "Auth & WeChat Integration"
Cohesion: 0.07
Nodes (24): 0fad7a7 fix: resolve API 307 redirect and 404 caused by trailing slash inconsistency, 2caef8e Merge pull request #2 from sin668/feat/booking-room-list-detail-fix, 3e4b38d docs: archive account security settings spec, 5187776 feat: show wallet balance on booking confirmation, 548e6b2 fix: load profile wallet stats, 549c0fa refactor br-app mobile UI, 597670e Add profile stat navigation links, 7487fee style: soften booking wallet balance (+16 more)

### Community 27 - "Coupon System"
Cohesion: 0.07
Nodes (23): Notification, NotificationPreference, NotificationType, NotificationNotFoundError, NotificationService, _preference_enabled(), _validate_type(), StrEnum (+15 more)

### Community 28 - "Teacher Management"
Cohesion: 0.06
Nodes (23): mock_db(), _mock_keys_result(), _mock_scalar_result(), Unit tests for AuthService., Successful registration returns TokenResponse., Registering with an existing phone raises 409., Registering with invalid SMS code raises 400., When nickname is None, a default '学习者XXXXXX' nickname is generated. (+15 more)

### Community 29 - "Data Models & Schemas"
Cohesion: 0.06
Nodes (29): CaptchaService, Aliyun Captcha 2.0 verification service., Verify a captcha token.          - If no ``ALIYUN_CAPTCHA_SCENE_ID`` is configur, Check whether a captcha token has already been consumed., _percent_encode(), SMS verification code service with rate-limiting., Return a 6-digit random numeric string., Send a verification code to *phone*.          Workflow:         1. Validate capt (+21 more)

### Community 30 - "Miscellaneous Module"
Cohesion: 0.09
Nodes (35): legacy_headers(), test_create_admin_user(), test_create_admin_user_requires_username(), test_create_app_user(), test_create_app_user_invalid_phone_format(), test_create_app_user_requires_phone(), test_create_duplicate_phone_returns_409(), test_create_duplicate_username_returns_409() (+27 more)

### Community 31 - "Auth & Login Tests"
Cohesion: 0.19
Nodes (33): CourseSchedule, 课程排课表。      存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。     从 courses 表迁移出的字段：teacher_id, sc, WalletTransaction, 获取课程详情 + 课时列表 + 定价信息。, BookingAlreadyCancelledError, BookingCancellationNotAllowedError, BookingNotFoundError, cancel_booking() (+25 more)

### Community 32 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (7): 7d72fbb test: add study record service and API tests, TestGetSummary, TestListRecords, _add_booking(), TestCalculateStreakDays, TestGetMonthlySummary, TestListStudyRecords

### Community 33 - "Auth & WeChat Integration"
Cohesion: 0.06
Nodes (19): 1e48f73 fix: 老师详情接口容忍 qualifications 为 NULL（AdminTeacherDetail 校验失败 500）, 7a418d3 tweak: 老师管理后端 — teachers 表扩展 + teacher_rooms 关联 + 管理端 CRUD API + C 端详情扩展与测试, be95476 feat: 老师新增/编辑页发布设置（是否激活）+ C 端老师列表过滤未激活 + 学习室编辑页行距统一, AdminTeacherCreate, AdminTeacherDetail, AdminTeacherListItem, AdminTeacherListResponse, AdminTeacherStatusUpdate (+11 more)

### Community 34 - "Payment & Wallet"
Cohesion: 0.06
Nodes (9): create_course(), get_course_detail(), Admin course management API routes., update_course(), AdminCourseService, 延期某一课时及其后续所有课时。          逻辑：         1. 从 course_lessons 表获取课时列表         2. 解析 t, 从 lesson_schedule JSON 中计算 end_date（最后一个课时日期 + 1 天）。, 根据 start_date 和 time_slots 生成至少 needed 个可用时间槽位。          按日期+时间段排序，循环扩展周次直到生成足够槽 (+1 more)

### Community 35 - "Booking Payment Tests"
Cohesion: 0.08
Nodes (23): PageEnum, DEFAULT_CONFIG, filter(), getConfig(), TreeHelperConfig, useAsyncRoute(), useAsyncRouteStore, ProjectSettingState (+15 more)

### Community 36 - "Booking Domain Service"
Cohesion: 0.09
Nodes (23): AdminMenu, AdminRole, AdminAuthService, MenuSeed, Admin login with neither phone nor username returns 422., Admin login with phone (no username) returns 200., test_admin_login_missing_both_fields(), test_admin_login_with_phone() (+15 more)

### Community 37 - "Booking Service Tests"
Cohesion: 0.12
Nodes (35): ALIGNMENT_POSITIONS, appendBits(), applyMask(), bchRemainder(), bitLength(), chooseVersion(), cloneMatrix(), createCodewords() (+27 more)

### Community 38 - "Course Management"
Cohesion: 0.07
Nodes (8): 8403348 refactor: extract admin page builders, d2114a6 merge: br-admin business refactor, routes, routes, AdminRoleSummary, columns, adminInfo, token

### Community 39 - "Booking Cancellation Tests"
Cohesion: 0.07
Nodes (21): _booking_payment_reconciliation_loop(), _cleanup_unpaid_bookings_job(), lifespan(), Fallback periodic runner for environments without APScheduler., Application lifespan: startup and shutdown events., BookingItem, BookingListParams, BookingListResult (+13 more)

### Community 40 - "Miscellaneous Module"
Cohesion: 0.06
Nodes (24): jwt_service(), _mock_keys_result(), mock_redis(), Unit tests for JWTService., Refresh token contains sub, type=refresh, exp, and jti., Each refresh token gets a unique jti., blacklist_token stores the jti in Redis with correct TTL., Return an AsyncMock whose coroutine resolves to the given list. (+16 more)

### Community 41 - "Coupon Service Layer"
Cohesion: 0.06
Nodes (2): routes, ParentLayout()

### Community 42 - "Teacher Management Tests"
Cohesion: 0.07
Nodes (13): ActivityCouponBase, ActivityCouponFormItem, ActivityCouponItem, ActivityCouponTemplate, ActivityFormParams, ActivityItem, ActivityListParams, ActivityListResult (+5 more)

### Community 43 - "Booking Service Tests"
Cohesion: 0.06
Nodes (15): CourseCreateParams, CourseDetail, CourseItem, CourseListResult, CourseScheduleItem, CourseUpdateParams, LessonCreateParams, LessonItem (+7 more)

### Community 44 - "Coupon Service Tests"
Cohesion: 0.08
Nodes (7): 3302a91 feat: add coupon package booking flow, d14db83 Merge branch 'feature/coupon-package-frontend', AdminCouponCreateParams, AdminCouponListParams, AdminCouponListResult, AdminCouponUpdateParams, add_coupon_models  Revision ID: b3a7c9d2e4f1 Revises: 985785a787d8 Create Date:

### Community 45 - "Deployment Config"
Cohesion: 0.09
Nodes (15): Props, useForm(), EmitType, UseFormActionContext, DATE_TYPE, dateItemType, basicProps, FormActionType (+7 more)

### Community 46 - "Token Verification"
Cohesion: 0.13
Nodes (19): UseFormValuesContext, is(), isArray(), isAsyncFunction(), isBoolean(), isDate(), isDef(), isElement() (+11 more)

### Community 47 - "Booking Verification Service"
Cohesion: 0.06
Nodes (8): Integration tests for admin activity API endpoints., TestAdminAuth, TestAdminCreateActivity, TestAdminDeleteActivity, TestAdminGetActivity, TestAdminListActivities, TestAdminToggleStatus, TestAdminUpdateActivity

### Community 48 - "Booking Domain Service"
Cohesion: 0.17
Nodes (22): _mock_scalar_one_result(), _mock_scalar_result(), _mock_scalars_result(), test_admin_get_statistics_aggregates_totals_and_active_users(), test_admin_list_transactions_joins_users_and_maps_user_fields(), test_confirm_payment_disabled_in_production(), test_create_recharge_order_rejects_unsupported_alipay(), test_create_wechat_recharge_order_returns_payment_params() (+14 more)

### Community 49 - "Auth Service Layer"
Cohesion: 0.08
Nodes (6): 7c70899 feat: add VIP membership and coupon admin, ed78866 Implement wallet recharge flow, create_wallet_table  Revision ID: 28a1f4af90df Revises: b3a7c9d2e4f1 Create Date, update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:, add_membership_level  Revision ID: df6ae550899a Revises: f1a2b3c4d5e6 Create Dat, add_wallet_membership_result  Revision ID: a2b3c4d5e6f7 Revises: df6ae550899a Cr

### Community 50 - "Booking Cancellation Tests"
Cohesion: 0.09
Nodes (13): _make_course(), Unit tests for CourseBookingService., full_package_price 为 None 时不触发优惠。, full_package_price 高于标准价时，discount_amount 为 0。, 空 lesson_ids 应被 Schema 拒绝。, 不存在的 course_id 返回 None。, 构造一个轻量 Course mock 对象。, 固定班课：3 课时 × ¥80 = ¥240。 (+5 more)

### Community 51 - "Booking Cancellation Tests"
Cohesion: 0.13
Nodes (11): AdminAssignRoles, AdminResetPassword, AdminToggleStatus, AdminUserCreate, AdminUserDetail, AdminUserListItem, AdminUserListParams, AdminUserListResponse (+3 more)

### Community 52 - "User & Auth Models"
Cohesion: 0.08
Nodes (8): Integration tests for Course Booking API.  注意：当前测试基础设施使用 SQLite 内存数据库，不支持 Postgr, POST /api/v1/course-bookings。, 无效 lesson_ids 返回 400。, POST /api/v1/course-bookings/{booking_id}/cancel。, GET /api/v1/courses/{id}/lessons。, TestCancelCourseBooking, TestCreateCourseBooking, TestGetCourseLessons

### Community 53 - "Booking Payment Service"
Cohesion: 0.11
Nodes (6): 3baaa8d feat: integrate WeChat wallet payments, b15c9d7 updated .gitignore, b610482 Archive wechat payment integration OpenSpec change, e07a2b2 feat: add wallet transactions frontend, f93686c merge: wallet transactions frontend, add_wechat_payment_fields  Revision ID: a8c3f1b2d4e5 Revises: 7c9d2e4f6a1b Creat

### Community 54 - "Teacher Management Tests"
Cohesion: 0.13
Nodes (11): AppMiddleware, health_check(), Health check endpoint., _json_dumps(), _parse_response(), Build mini program payment params for uni.requestPayment., Query an order by merchant out_trade_no., Verify notification signature, decrypt resource, and validate fields. (+3 more)

### Community 56 - "Booking Verification Tests"
Cohesion: 0.21
Nodes (22): _activity_coupon_to_public_response(), _activity_to_admin_response(), _admin_coupon_to_response(), claim_activity_coupon(), claim_activity_coupon_response(), _count_user_claims(), _coupon_to_response(), create_activity() (+14 more)

### Community 58 - "Coupon Service Layer"
Cohesion: 0.17
Nodes (19): _access_token(), _phone_user(), _temp_wechat_user(), test_bind_phone_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_sms_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_with_sms_to_new_phone(), test_bind_wechat_phone_code_to_new_phone(), test_bound_user_binding_unused_phone_returns_409() (+11 more)

### Community 59 - "Auth & Login Tests"
Cohesion: 0.09
Nodes (23): ChangeEvent, DeepPartial, Element, ElementAttributesProperty, ElementClass, Event, ImportMetaEnv, Indexable (+15 more)

### Community 60 - "Booking Service Tests"
Cohesion: 0.09
Nodes (12): BookingUseCases, Application use case orchestration layer., 3709fe0 docs: localize br-app refactor plan, 645d7d5 refactor: extract booking repository conflict query, 9ea74c1 test: align admin booking detail fixture assertion, bb3b56d refactor: extract verification token rules, bfd21f6 refactor: extract wallet transaction repository, e2a44c1 refactor: add app formatter constants (+4 more)

### Community 61 - "Teacher Management Tests"
Cohesion: 0.24
Nodes (21): NamedTuple, BookingCouponCalculation, _calc_discount(), _calculate_hours(), _calculate_original_price(), _check_scope(), CouponUnavailableError, _ensure_aware() (+13 more)

### Community 62 - "Teacher Management Tests"
Cohesion: 0.19
Nodes (20): AdminCouponCreate, AdminCouponListResponse, AdminCouponResponse, AdminCouponStatusUpdate, AdminCouponUpdate, AdminCouponError, AdminCouponNotFoundError, _clean_coupon_data() (+12 more)

### Community 63 - "Miscellaneous Module"
Cohesion: 0.21
Nodes (22): _booking_now(), _booking_timezone(), _build_booking_summary(), _build_verify_url(), confirm_verification(), _create_legacy_jwt_verification_token(), _create_verification_token(), _decode_compact_verification_token() (+14 more)

### Community 65 - "Backend Service Layer"
Cohesion: 0.26
Nodes (17): _make_booking(), _make_coupon(), _make_room(), _make_seat(), _make_user(), _make_user_coupon(), test_admin_cancel_booking(), test_admin_cancel_booking_already_cancelled() (+9 more)

### Community 67 - "Booking Cancellation Tests"
Cohesion: 0.17
Nodes (14): CouponUnavailableError, CourseBookingError, CourseBookingService, CourseNotFoundError, LessonValidationError, _now_naive(), 价格计算。          从排课表获取价格信息：         - fixed: len(lesson_ids) × schedule.price, 验证优惠券对课程预约的有效性。          返回 (discount_amount, total_price, user_coupon)。 (+6 more)

### Community 68 - "Booking Cancellation Tests"
Cohesion: 0.21
Nodes (7): BookingPaymentAlreadyProcessedError, BookingPaymentError, BookingPaymentNotFoundError, BookingPaymentService, BookingPaymentSignatureError, InvalidBookingPaymentCallbackError, WechatOpenIdRequiredError

### Community 69 - "Booking Payment Tests"
Cohesion: 0.19
Nodes (1): WechatAuthService

### Community 70 - "Miscellaneous Module"
Cohesion: 0.14
Nodes (9): 89f0643 feat: load booking detail seat stats from backend, d4a1403 chore: archive wallet transactions frontend spec, admin_list_seats(), bulk_create_seats(), create_seat(), _get_booked_seat_ids(), get_seat_stats(), list_seats() (+1 more)

### Community 71 - "User Security Tests"
Cohesion: 0.15
Nodes (8): EditRecordRow, renderEditCell(), Instance, key, RetInstance, BasicColumn, BasicTableProps, TableActionType

### Community 72 - "Booking Service Tests"
Cohesion: 0.44
Nodes (19): ExpiredVerificationToken, InvalidVerificationToken, BookingVerificationBookingSummary, BookingVerificationConfirmResponse, BookingVerificationDetailResponse, BookingVerificationTokenRequest, BookingVerificationTokenResponse, VerifiableBookingListResponse (+11 more)

### Community 73 - "Course Management"
Cohesion: 0.11
Nodes (8): 6288c60 feat: add booking wechat payment flow, cleanup_unpaid_bookings(), Cleanup for unpaid booking payment holds., Cancel stale pending WeChat bookings and restore attached coupons., auth_client(), other_auth_client(), seed_room_seat(), add_booking_payment_fields  Adds payment-related fields to bookings table: - pay

### Community 74 - "Booking System Core"
Cohesion: 0.13
Nodes (14): applyWechatAppId(), DEFAULT_DEV_OUTPUT_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_SERVER_ENV_PATH, fs, parseEnvFile(), path, resolveOutputDirFromArgs() (+6 more)

### Community 75 - "Token Verification"
Cohesion: 0.11
Nodes (1): admin_client()

### Community 76 - "Miscellaneous Module"
Cohesion: 0.11
Nodes (15): 培训课程相关 Schema 导入与功能测试  验证以下 schema 能正确导入和使用： - TeacherResponse, TeacherBrief, Ho, StudyRoomResponse 包含 room_type 字段, RoomCreate 包含 room_type 字段，默认值 study, RoomUpdate 包含 room_type 字段，默认 None, RoomAdminResponse 包含 room_type 字段, TeacherResponse 可正确导入并实例化, course.py 中所有 schema 可正确导入, CourseResponse.parse_tags 正确解析逗号分隔字符串 (+7 more)

### Community 77 - "Auth & WeChat Integration"
Cohesion: 0.12
Nodes (3): 00cde52 Implement dynamic booking verification QR flow, 39024d3 fix: stabilize booking verification QR flow, 7143168 Archive personal QR OpenSpec change

### Community 78 - "Integration Tests"
Cohesion: 0.16
Nodes (14): ClickOutside, DocumentHandler, FlushList, nodeList, addClass(), getBoundingClientRect(), getViewportOffset(), hasClass() (+6 more)

### Community 79 - "Notification System"
Cohesion: 0.15
Nodes (17): Enum, PaymentMethod, PaymentStatus, BookingAdminListResponse, BookingAdminResponse, BookingCreate, BookingListResponse, BookingResponse (+9 more)

### Community 80 - "Course Management"
Cohesion: 0.18
Nodes (4): _coupon(), _seed_activity_coupon(), TestActivityCouponAPI, TestActivityCouponService

### Community 81 - "Teacher & Course Models"
Cohesion: 0.19
Nodes (2): _payload(), TestAdminTeacherApi

### Community 83 - "RBAC Service Layer"
Cohesion: 0.23
Nodes (5): hash_id_card(), is_valid_id_card(), mask_id_card(), mask_phone(), UserSecurityService

### Community 84 - "Booking Cancellation Tests"
Cohesion: 0.12
Nodes (2): admin_client(), unauth_client()

### Community 85 - "Booking Verification Tests"
Cohesion: 0.12
Nodes (1): TestCreateBooking

### Community 86 - "Booking Service Tests"
Cohesion: 0.15
Nodes (7): COURSE_WEEKDAY_NAMES, formatAmount(), formatHourCount(), formatHourDuration(), formatMoney(), formatRoomMinPrice(), toFiniteNumber()

### Community 87 - "Booking Service Tests"
Cohesion: 0.21
Nodes (16): del(), doRefreshToken(), get(), getRefreshToken(), getToken(), patch(), pendingRequests, post() (+8 more)

### Community 88 - "Booking Service Tests"
Cohesion: 0.17
Nodes (11): 316d285 feat: add study record schemas, 5ce3f55 Merge branch 'worktree-learning-record-impl' into main, 83ccd35 feat: add study record backend (schema, service, routes), CalendarMark, StudyRecordItem, StudyRecordListResponse, StudyRecordSummaryResponse, _build_record_item() (+3 more)

### Community 89 - "Coupon System"
Cohesion: 0.16
Nodes (8): useModal(), BasicProps, ModalMethods, ModalProps, RegisterFn, UseModalReturnType, isProdMode(), getDynamicProps()

### Community 90 - "Database Config"
Cohesion: 0.17
Nodes (10): Banner, list_active_banners(), Return all active banners ordered by sort_order ascending., Unit tests for banner_service module., Seed banners for tests., Only active banners are returned., Results are ordered by sort_order ascending., Empty DB returns empty list. (+2 more)

### Community 92 - "Auth & Login Tests"
Cohesion: 0.16
Nodes (11): asyncImportRoute(), generateDynamicRoutes(), generateRoutes(), LayoutMap, constantRouterIcon, AppRouteRecordRaw, Component, IModuleType (+3 more)

### Community 94 - "Room & Seat Management"
Cohesion: 0.13
Nodes (14): AdminWalletStatisticsResponse, AdminWalletTransactionListResponse, AdminWalletTransactionResponse, BalanceResponse, PaymentParams, PromoCodeRequest, PromoCodeResponse, RechargeOrderResponse (+6 more)

### Community 95 - "Room Management Tests"
Cohesion: 0.24
Nodes (1): TestCancelBooking

### Community 96 - "Database Seed Data"
Cohesion: 0.13
Nodes (2): Integration tests for file upload API endpoints., TestUploadAPI

### Community 98 - "Booking Service Tests"
Cohesion: 0.27
Nodes (13): appRoot, assert, fs, loadModule(), main(), path, testAccountSecurity(), testAccountSecurityApi() (+5 more)

### Community 99 - "Teacher Management"
Cohesion: 0.30
Nodes (1): AdminMenuService

### Community 100 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (13): _apply_menu_seed(), _ensure_role_menus(), _ensure_user_role(), _get_or_create_admin(), _get_or_create_app_role(), _get_or_create_menu(), _get_or_create_role(), main() (+5 more)

### Community 101 - "Teacher & Course Models"
Cohesion: 0.15
Nodes (7): AdminTeacherCreateParams, AdminTeacherDetail, AdminTeacherItem, AdminTeacherListResult, AdminTeacherUpdateParams, QualificationItem, TeacherRoomBrief

### Community 102 - "Teacher Management Tests"
Cohesion: 0.14
Nodes (8): Tests for API dependencies., Invalid token returns 401., No admin token returns 401., Wrong admin token returns 401., No credentials (no Authorization header) returns 401., Valid access token returns the user ID., TestGetCurrentAdmin, TestGetCurrentUserId

### Community 104 - "Coupon Service Tests"
Cohesion: 0.18
Nodes (8): debounce, ElType, HTMLElement, permission, ElType, HTMLElement, throttle, usePermission()

### Community 105 - "Miscellaneous Module"
Cohesion: 0.21
Nodes (7): DesignSettingState, useDesignSetting(), useDesignSettingStore, setupRouter(), pinia, setupStore(), store

### Community 106 - "Room & Seat Management"
Cohesion: 0.15
Nodes (8): Unit tests for study_room_service module., Seed study rooms for tests., Only open rooms are returned., Pagination works correctly., Page size is capped at MAX_PAGE_SIZE (50)., Empty DB returns zero total and empty items., seed_study_rooms(), TestListStudyRooms

### Community 107 - "Auth & WeChat Integration"
Cohesion: 0.23
Nodes (3): _make_user(), TestProcessVipUpgrade, TestVIPScopeFilter

### Community 108 - "Integration Tests"
Cohesion: 0.24
Nodes (4): ComponentProps, componentMap, EventEnum, ComponentType

### Community 110 - "Room & Seat Service"
Cohesion: 0.30
Nodes (10): _course_count_map(), create_teacher(), delete_teacher(), get_teacher_detail(), list_teachers(), _load_rooms_for_teachers(), _sync_teacher_rooms(), _tags_to_db() (+2 more)

### Community 111 - "Miscellaneous Module"
Cohesion: 0.17
Nodes (6): Delete a refresh token reference from Redis., Delete every stored refresh token for a user., Check whether a refresh token is still valid (present in Redis)., Rotate a refresh token: create a new one, store it, revoke the old one., Create a long-lived refresh token with a unique jti.          Payload contains:, Store a refresh token reference in Redis.          Key: ``refresh:{user_id}:{jti

### Community 114 - "Booking Cancellation Tests"
Cohesion: 0.29
Nodes (9): _create_user(), test_change_password_rejects_bad_old_password_or_mismatch(), test_change_password_updates_hash_and_revokes_refresh_tokens(), test_deactivate_account_blocks_risks(), test_deactivate_account_sets_deleted_without_removing_user(), test_security_summary_masks_sensitive_fields(), test_security_summary_returns_deleted_unbound_unverified_state(), test_submit_identity_rejects_invalid_or_different_verified() (+1 more)

### Community 117 - "Miscellaneous Module"
Cohesion: 0.20
Nodes (9): get_current_admin(), get_current_admin_context(), get_current_user_id(), get_optional_current_user_id(), Shared API dependencies., Compatibility entrypoint for legacy admin route dependencies., Extract and validate the current user ID from the access token., 有登录凭证时解析用户 ID，无凭证时返回 None。 (+1 more)

### Community 118 - "Coupon System"
Cohesion: 0.29
Nodes (10): 0072a7a 时区Bug fixed, 0f28968 Bug fixed, 5c47a3c archive coupon package frontend openspec change, c66da47 updated bug-fixed.md, _china_now_naive(), _get_or_create_demo_user(), seed_all(), seed_coupons() (+2 more)

### Community 119 - "Miscellaneous Module"
Cohesion: 0.25
Nodes (7): screenEnum, screenMap, sizeEnum, CreateCallbackParams, RemoveEventFn, useEventListener(), UseEventParams

### Community 120 - "Booking Payment Service"
Cohesion: 0.29
Nodes (7): _build_wechat_client(), create_booking(), get_payment_status(), _notify_failure(), pay_pending_booking_route(), _payment_service(), wechat_notify()

### Community 121 - "Wallet Service Layer"
Cohesion: 0.35
Nodes (10): _build_wechat_client(), confirm_recharge(), create_recharge(), get_balance(), get_recharge_order(), list_transactions(), _notify_failure(), redeem_promo_code() (+2 more)

### Community 122 - "User & Auth Models"
Cohesion: 0.40
Nodes (1): AdminSettingService

### Community 124 - "Miscellaneous Module"
Cohesion: 0.33
Nodes (3): _coupon_data(), _create_coupon(), TestAdminCouponService

### Community 125 - "Admin Coupon Tests"
Cohesion: 0.22
Nodes (2): _payload(), TestAdminCouponApi

### Community 126 - "Admin Coupon Tests"
Cohesion: 0.18
Nodes (6): TrainingRoomDetailResponse schema 测试, 验证嵌套 CourseResponse 的 tags 为 None 时解析为空列表, 验证缺少必填字段时抛出 ValidationError, 验证 teachers 和 courses 字段默认值为空列表, 验证嵌套的 CourseResponse 中 tags 字段可以正确解析逗号分隔字符串, TestTrainingRoomDetailResponse

### Community 127 - "Teacher Management Tests"
Cohesion: 0.22
Nodes (3): test_first_wechat_login_creates_phone_null_user_and_caches_session_key(), test_repeat_wechat_login_reuses_bound_user(), _token_sub()

### Community 128 - "Seat Management Tests"
Cohesion: 0.18
Nodes (10): get_course_detail(), _get_first_schedule_for_courses(), get_training_room_detail(), list_courses(), list_training_rooms(), 返回培训室详情，包含课程列表和教师团队。      仅 room_type 为 training 或 comprehensive 的房间有效。, 返回分页课程列表，附带教室名和教师信息。      单条查询：JOIN StudyRoom + CourseSchedule + Teacher。, 返回课程详情，含教师、教室、课时和相关课程。      3 步查询，避免 N+1：     Step 1: courses + LEFT JOIN course (+2 more)

### Community 130 - "Auth & Login Tests"
Cohesion: 0.27
Nodes (6): 3252e57 实现预约取消退款, booking_now(), booking_start_datetime(), calculate_cancellation_policy(), CancellationPolicyResult, add booking cancellation audit fields  Revision ID: b8c9d0e1f2a3 Revises: a7b8c9

### Community 131 - "Token Verification"
Cohesion: 0.20
Nodes (4): TransactionLike, Protocol, Persist an upload object and return the public result., StorageAdapter

### Community 133 - "HTML Sanitizer"
Cohesion: 0.24
Nodes (2): HTMLParser, _RichTextSanitizer

### Community 134 - "User Management"
Cohesion: 0.27
Nodes (6): setupCustomComponents(), setupDirectives(), setupGlobalMethods(), naive, setupNaive(), setupNaiveDiscreteApi()

### Community 136 - "Room & Seat Models"
Cohesion: 0.33
Nodes (1): AdminRoleService

### Community 138 - "Wallet Service Layer"
Cohesion: 0.20
Nodes (1): TestSeatAPI

### Community 139 - "Booking Service Tests"
Cohesion: 0.36
Nodes (8): _create_user(), test_get_current_user_profile_returns_username_fields(), test_update_nickname_does_not_require_username_cooldown(), test_update_profile_rejects_protected_fields(), test_update_username_rejects_cooldown(), test_update_username_rejects_duplicate(), test_update_username_rejects_invalid_format(), test_update_username_success_sets_cooldown_timestamp()

### Community 140 - "Booking Cancellation Tests"
Cohesion: 0.20
Nodes (3): 测试 GET /api/v1/training/courses/{course_id} 路由。, 相关课程超过 6 门时，只返回 6 门，排除当前课程。, TestCourseDetailRoute

### Community 141 - "User Profile Tests"
Cohesion: 0.20
Nodes (3): 只返回 room_type 为 training 或 comprehensive 且 status=open 的房间。, 非热门课程不出现在 hot_courses 中。, TestListTrainingRooms

### Community 143 - "Auth & Login Tests"
Cohesion: 0.20
Nodes (9): GlobConfig, GlobEnvConfig, IBodySetting, ICrumbsSetting, IHeaderSetting, IMenuSetting, IMultiTabsSetting, LocalConfig (+1 more)

### Community 144 - "Deployment Config"
Cohesion: 0.20
Nodes (9): ComponentElRef, ComponentRef, ElRef, EmitType, Fn, LabelValueOptions, PromiseFn, RefType (+1 more)

### Community 145 - "Miscellaneous Module"
Cohesion: 0.28
Nodes (3): adminRequest(), confirmVerification(), inspectVerificationToken()

### Community 147 - "Deployment Config"
Cohesion: 0.36
Nodes (8): 3544ddd fix: 修复待开始订单课时列表不显示 - 添加lesson_schedules fallback逻辑, 3bd4e67 fix: 修复订单待开始状态显示和试听课时后端免费计费, 4ffdfd4 fix: 修复待开始订单课时列表fallback条件 - 仅保留list_bookings核心修复，回退前端改动, 8021fb4 fix: 修复订单待开始Tab过滤和课时展开显示逻辑, c768067 modify course-booking, d2c36b6 fix: 修复订单课时列表只显示该订单预约的课时而非全部课时, e27ba0c fix: 修复课程预约订单状态显示为已完成问题 - 排除课程预约自动完成标记并增加进行中状态, e46d76d fix: 修复待开始订单课时列表不显示 - 修复fallback条件和前端数据回退

### Community 148 - "Miscellaneous Module"
Cohesion: 0.31
Nodes (4): useTimeoutFn(), useTimeoutRef(), useBreakpoint(), useDesignSetting()

### Community 149 - "Miscellaneous Module"
Cohesion: 0.22
Nodes (7): COURSE_CATEGORY_LABELS, COURSE_CATEGORY_OPTIONS, COURSE_STATUS_TAGS, BusinessTagConfig, EDUCATION_OPTIONS, ROOM_TYPE_LABELS, TEACHER_STATUS_TAGS

### Community 150 - "Teacher Management"
Cohesion: 0.25
Nodes (7): AdminMenuBase, AdminMenuCreate, AdminMenuNode, AdminMenuRoute, AdminMenuRouteMeta, AdminMenuUpdate, ComponentOption

### Community 151 - "Miscellaneous Module"
Cohesion: 0.22
Nodes (8): exportMatch, fs, getCallMatch, paramMatch, path, source, trainingApiPath, urlMatch

### Community 152 - "RBAC Data Models"
Cohesion: 0.39
Nodes (7): followRoom(), getFollowedRooms(), isRoomFollowed(), normalizeRoom(), setFollowedRooms(), syncFollowedRooms(), unfollowRoom()

### Community 153 - "Token Verification"
Cohesion: 0.22
Nodes (4): BasicSettings, EmailSettings, nativeMeta, SystemSettings

### Community 154 - "Room & Seat Management"
Cohesion: 0.22
Nodes (1): TestAvailableCouponsForBooking

### Community 155 - "JWT Token Tests"
Cohesion: 0.22
Nodes (5): get_current_user_id returns the user UUID from a valid access token., get_current_user_id raises 401 for a blacklisted token., get_current_user_id raises 401 when token type is not 'access'., get_current_user_id raises 401 for an expired token., TestGetCurrentUserId

### Community 156 - "Integration Tests"
Cohesion: 0.33
Nodes (5): getAppEnvConfig(), getCommonStoragePrefix(), getEnv(), getStorageShortName(), warn()

### Community 157 - "Deployment Config"
Cohesion: 0.29
Nodes (6): Run migrations in 'offline' mode.      Configures the context with just a URL an, Run migrations in 'online' mode with async engine., Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online()

### Community 158 - "Database Migrations"
Cohesion: 0.25
Nodes (2): CountTo, withInstall()

### Community 159 - "Miscellaneous Module"
Cohesion: 0.39
Nodes (5): create_coupon(), delete_coupon(), _service_error(), toggle_coupon_status(), update_coupon()

### Community 161 - "Miscellaneous Module"
Cohesion: 0.36
Nodes (5): create_teacher(), get_teacher_detail(), Admin teacher management API routes., toggle_teacher_status(), update_teacher()

### Community 162 - "Coupon Service Layer"
Cohesion: 0.32
Nodes (3): list_notifications(), mark_all_notifications_read(), _parse_notification_type()

### Community 163 - "Room & Seat Management"
Cohesion: 0.29
Nodes (7): AdminRoleBase, AdminRoleCreate, AdminRoleListResponse, AdminRoleMenusResponse, AdminRoleMenuUpdate, AdminRoleResponse, AdminRoleUpdate

### Community 164 - "Teacher Management"
Cohesion: 0.32
Nodes (6): assertContains(), assertMatches(), fs, path, read(), root

### Community 165 - "User Management"
Cohesion: 0.29
Nodes (7): appRoot, assert, fs, loadModule(), main(), path, vm

### Community 166 - "Notification System"
Cohesion: 0.25
Nodes (7): failures, fs, path, profilePath, requiredLinks, source, statsCardMatch

### Community 167 - "RBAC Data Models"
Cohesion: 0.46
Nodes (7): followCourse(), getFollowedCourses(), isCourseFollowed(), normalizeCourse(), setFollowedCourses(), syncFollowedCourses(), unfollowCourse()

### Community 169 - "Room & Seat Models"
Cohesion: 0.43
Nodes (6): _policy(), test_exact_24_hours_charges_20_percent(), test_exact_2_hours_charges_50_percent(), test_exact_48_hours_charges_10_percent(), test_non_round_amount_keeps_penalty_and_refund_balanced(), test_over_48_hours_full_refund()

### Community 170 - "Teacher & Course Models"
Cohesion: 0.25
Nodes (5): 验证 StudyRoom 模型新增的 rating 列与 city 关系。, StudyRoom 实例可以带 rating 字段创建，且默认值为 0。, rating 字段缺省时默认值为 0.0。, StudyRoom 模型上存在 city 关系，且可正确加载关联的 City。, TestStudyRoomModel

### Community 175 - "Miscellaneous Module"
Cohesion: 0.52
Nodes (5): createUploadError(), normalizeErrorMessage(), parseUploadResponse(), uploadImage(), uploadOnce()

### Community 176 - "Teacher Management"
Cohesion: 0.33
Nodes (6): close_redis(), get_redis(), init_redis(), Initialize and return the singleton Redis connection., Close the Redis connection., FastAPI dependency that provides an async Redis connection.

### Community 178 - "Booking Cancellation Tests"
Cohesion: 0.57
Nodes (6): base64url_encode(), CompactVerificationPayload, create_compact_verification_token(), decode_compact_verification_token(), ensure_utc(), sign_compact_token()

### Community 180 - "Project Documentation"
Cohesion: 0.52
Nodes (6): followTeacher(), getFollowedTeachers(), isTeacherFollowed(), normalizeTeacher(), setFollowedTeachers(), unfollowTeacher()

### Community 184 - "Payment & Wallet"
Cohesion: 0.29
Nodes (4): GET /me without auth returns 401., GET /me with valid auth returns user info., GET /me with auth but user not in DB returns 404., TestGetMeAuth

### Community 185 - "Redis Connection"
Cohesion: 0.29
Nodes (4): verify_token returns payload for a valid token., verify_token raises HTTPException 401 for an expired token., verify_token raises HTTPException 401 for a token with wrong secret., TestVerifyToken

### Community 186 - "Payment & Wallet"
Cohesion: 0.29
Nodes (4): store_refresh_token stores with correct key and TTL., revoke_refresh_token deletes the key from Redis., is_refresh_token_valid checks Redis existence., TestRefreshTokenStorage

### Community 187 - "Token Verification"
Cohesion: 0.29
Nodes (1): TestCourseModel

### Community 191 - "Admin RBAC System"
Cohesion: 0.33
Nodes (3): FastAPI Depends-compatible callable.          Decodes the token, checks blacklis, Decode and return the token payload.          Raises HTTPException 401 if the to, Check whether a token (by jti) is in the Redis blacklist.

### Community 195 - "Wallet Service Layer"
Cohesion: 0.33
Nodes (2): Integration tests for city APIs., TestCityAPI

### Community 196 - "Miscellaneous Module"
Cohesion: 0.33
Nodes (2): Unit tests for the City model., TestCityModel

### Community 200 - "Community 200"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 201 - "Community 201"
Cohesion: 0.40
Nodes (3): copy, ElType, HTMLElement

### Community 202 - "Community 202"
Cohesion: 0.60
Nodes (3): can_cancel_paid_booking(), has_booking_started(), should_mark_booking_completed()

### Community 203 - "Community 203"
Cohesion: 0.50
Nodes (3): PermissionsEnum, ActionItem, PopConfirm

### Community 204 - "Community 204"
Cohesion: 0.60
Nodes (4): AvailableCouponForBookingResponse, AvailableCouponsForBookingListResponse, CouponBaseResponse, CouponResponse

### Community 205 - "Community 205"
Cohesion: 0.60
Nodes (3): createPaymentStatusError(), getPaymentStatus(), pollPaymentStatus()

### Community 206 - "Community 206"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 207 - "Community 207"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 208 - "Community 208"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 209 - "Community 209"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_component_options_and_invalid_component(), test_dynamic_routes_exclude_buttons_and_disabled_nodes(), test_menu_tree_crud_and_delete_child_conflict()

### Community 210 - "Community 210"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_email_test_requires_complete_config(), test_settings_read_masks_smtp_password(), test_update_email_without_password_preserves_existing_secret()

### Community 211 - "Community 211"
Cohesion: 0.40
Nodes (2): StudyRoom.room_type 字段验证。, TestStudyRoomRoomType

### Community 212 - "Community 212"
Cohesion: 0.40
Nodes (1): TestTeacherModel

### Community 213 - "Community 213"
Cohesion: 0.40
Nodes (3): NOTIFICATION_TYPE_CONFIGS, NOTIFICATION_TYPE_MAP, NOTIFICATION_TYPES

### Community 214 - "Community 214"
Cohesion: 0.50
Nodes (3): _generate_username(), add_username_updated_at  Adds users.username_updated_at and backfills existing u, upgrade()

### Community 217 - "Community 217"
Cohesion: 0.67
Nodes (3): 023eb00 feat: add GET /api/v1/training/rooms/{room_id} route, 80e3f09 chore: checkoff Task 4 in plan, 9fd4cb8 test: add 8 training room detail API test scenarios (4.1-4.8)

### Community 218 - "Community 218"
Cohesion: 0.50
Nodes (3): BOOKING_STATUS_LABELS, BOOKING_TABS, SEAT_ZONE_LABELS

### Community 219 - "Community 219"
Cohesion: 0.50
Nodes (3): draggable, ElType, HTMLElement

### Community 220 - "Community 220"
Cohesion: 0.83
Nodes (2): setLoading(), useAsync()

### Community 221 - "Community 221"
Cohesion: 0.50
Nodes (1): key

### Community 222 - "Community 222"
Cohesion: 0.50
Nodes (1): useCityStore

### Community 223 - "Community 223"
Cohesion: 0.83
Nodes (3): upload_admin_image(), _upload_image(), upload_user_image()

### Community 226 - "Community 226"
Cohesion: 0.83
Nodes (3): legacy_headers(), test_role_crud_duplicate_and_assigned_delete_conflict(), test_role_menu_assignment_updates_auth_permissions()

### Community 228 - "Community 228"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17

### Community 229 - "Community 229"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:

### Community 230 - "Community 230"
Cohesion: 0.50
Nodes (1): create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create

### Community 231 - "Community 231"
Cohesion: 0.50
Nodes (1): create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat

### Community 232 - "Community 232"
Cohesion: 0.50
Nodes (1): booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:

### Community 233 - "Community 233"
Cohesion: 0.50
Nodes (1): create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea

### Community 234 - "Community 234"
Cohesion: 0.50
Nodes (1): add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf

### Community 235 - "Community 235"
Cohesion: 0.50
Nodes (1): add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c

### Community 236 - "Community 236"
Cohesion: 0.50
Nodes (1): add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create

### Community 237 - "Community 237"
Cohesion: 0.50
Nodes (1): add room follows  Revision ID: c9d0e1f2a3b4 Revises: b8c9d0e1f2a3 Create Date: 2

### Community 238 - "Community 238"
Cohesion: 0.50
Nodes (1): add_activity_coupon_campaign  Revision ID: f1a2b3c4d5e6 Revises: d0e1f2a3b4c5 Cr

### Community 239 - "Community 239"
Cohesion: 0.50
Nodes (1): create_schedule_HotCourseItem  Revision ID: fccf087f0f34 Revises: e3f4a5b6c7d8 C

### Community 240 - "Community 240"
Cohesion: 0.50
Nodes (1): create_course_table  Revision ID: c84abd1322d4 Revises: c4d5e6f7a8b9 Create Date

### Community 241 - "Community 241"
Cohesion: 0.50
Nodes (1): add teacher bio and student_count  Revision ID: e7f8a9b0c1d2 Revises: c84abd1322

### Community 242 - "Community 242"
Cohesion: 0.50
Nodes (1): add full_custom_price to courses  Revision ID: 5d8e53290b12 Revises: a1b2c3d4e5f

### Community 243 - "Community 243"
Cohesion: 0.50
Nodes (1): create course_schedules table and migrate fields from courses  Revision ID: b1c2

### Community 244 - "Community 244"
Cohesion: 0.50
Nodes (1): add time_slots and teacher_id to bookings  Revision ID: b9c0d1e2f3a4 Revises: e8

### Community 245 - "Community 245"
Cohesion: 0.67
Nodes (1): __APP_INFO__

### Community 246 - "Community 246"
Cohesion: 0.67
Nodes (1): WindowSizeOptions

### Community 248 - "Community 248"
Cohesion: 0.67
Nodes (1): Battery

### Community 249 - "Community 249"
Cohesion: 0.67
Nodes (2): CourseResponse, 将逗号分隔字符串解析为列表，None 或空字符串返回空列表

### Community 250 - "Community 250"
Cohesion: 0.67
Nodes (2): get_active_cities(), Return active cities ordered by sort_order ascending.

### Community 251 - "Community 251"
Cohesion: 0.67
Nodes (2): appThemeList, setting

### Community 254 - "Community 254"
Cohesion: 0.67
Nodes (1): Tests for admin wallet API routes.

### Community 255 - "Community 255"
Cohesion: 0.67
Nodes (1): TestStudyRoomAPI

### Community 260 - "Community 260"
Cohesion: 1.00
Nodes (1): BasicProps

### Community 262 - "Community 262"
Cohesion: 1.00
Nodes (1): directive

### Community 263 - "Community 263"
Cohesion: 1.00
Nodes (1): RoleEnum

### Community 269 - "Community 269"
Cohesion: 1.00
Nodes (1): animates

### Community 271 - "Community 271"
Cohesion: 1.00
Nodes (1): DynamicProps

### Community 273 - "Community 273"
Cohesion: 1.00
Nodes (1): params

## Knowledge Gaps
- **439 isolated node(s):** `返回当前 Asia/Shanghai 时区的 naive datetime。`, `查询课程详情 + 课时列表 + 排课信息。          仅关联固定班课（schedule_type=fixed）排课，定制课时记录不在 C 端展示。`, `价格计算。          从排课表获取价格信息：         - fixed: len(lesson_ids) × schedule.price`, `验证优惠券对课程预约的有效性。          返回 (discount_amount, total_price, user_coupon)。`, `创建课程预约（完整流程）。          1. 验证课程存在且 status='active'         2. 验证 lesson_ids 均属于该课` (+434 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Coupon Service Layer`** (2 nodes): `routes`, `ParentLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Payment Tests`** (1 nodes): `WechatAuthService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Token Verification`** (1 nodes): `admin_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher & Course Models`** (2 nodes): `_payload()`, `TestAdminTeacherApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Cancellation Tests`** (2 nodes): `admin_client()`, `unauth_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Verification Tests`** (1 nodes): `TestCreateBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Room Management Tests`** (1 nodes): `TestCancelBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Database Seed Data`** (2 nodes): `Integration tests for file upload API endpoints.`, `TestUploadAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher Management`** (1 nodes): `AdminMenuService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `User & Auth Models`** (1 nodes): `AdminSettingService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Admin Coupon Tests`** (2 nodes): `_payload()`, `TestAdminCouponApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HTML Sanitizer`** (2 nodes): `HTMLParser`, `_RichTextSanitizer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Room & Seat Models`** (1 nodes): `AdminRoleService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Wallet Service Layer`** (1 nodes): `TestSeatAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Room & Seat Management`** (1 nodes): `TestAvailableCouponsForBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Database Migrations`** (2 nodes): `CountTo`, `withInstall()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Token Verification`** (1 nodes): `TestCourseModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Wallet Service Layer`** (2 nodes): `Integration tests for city APIs.`, `TestCityAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (2 nodes): `Unit tests for the City model.`, `TestCityModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 211`** (2 nodes): `StudyRoom.room_type 字段验证。`, `TestStudyRoomRoomType`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 212`** (1 nodes): `TestTeacherModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 220`** (2 nodes): `setLoading()`, `useAsync()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 221`** (1 nodes): `key`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 222`** (1 nodes): `useCityStore`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 228`** (1 nodes): `create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (1 nodes): `create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 230`** (1 nodes): `create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 231`** (1 nodes): `create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 232`** (1 nodes): `booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 233`** (1 nodes): `create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 234`** (1 nodes): `add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 235`** (1 nodes): `add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 236`** (1 nodes): `add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 237`** (1 nodes): `add room follows  Revision ID: c9d0e1f2a3b4 Revises: b8c9d0e1f2a3 Create Date: 2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 238`** (1 nodes): `add_activity_coupon_campaign  Revision ID: f1a2b3c4d5e6 Revises: d0e1f2a3b4c5 Cr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 239`** (1 nodes): `create_schedule_HotCourseItem  Revision ID: fccf087f0f34 Revises: e3f4a5b6c7d8 C`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 240`** (1 nodes): `create_course_table  Revision ID: c84abd1322d4 Revises: c4d5e6f7a8b9 Create Date`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 241`** (1 nodes): `add teacher bio and student_count  Revision ID: e7f8a9b0c1d2 Revises: c84abd1322`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 242`** (1 nodes): `add full_custom_price to courses  Revision ID: 5d8e53290b12 Revises: a1b2c3d4e5f`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 243`** (1 nodes): `create course_schedules table and migrate fields from courses  Revision ID: b1c2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 244`** (1 nodes): `add time_slots and teacher_id to bookings  Revision ID: b9c0d1e2f3a4 Revises: e8`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 245`** (1 nodes): `__APP_INFO__`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 246`** (1 nodes): `WindowSizeOptions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 248`** (1 nodes): `Battery`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 249`** (2 nodes): `CourseResponse`, `将逗号分隔字符串解析为列表，None 或空字符串返回空列表`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 250`** (2 nodes): `get_active_cities()`, `Return active cities ordered by sort_order ascending.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 251`** (2 nodes): `appThemeList`, `setting`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 254`** (1 nodes): `Tests for admin wallet API routes.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 255`** (1 nodes): `TestStudyRoomAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 260`** (1 nodes): `BasicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 262`** (1 nodes): `directive`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 263`** (1 nodes): `RoleEnum`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 269`** (1 nodes): `animates`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 271`** (1 nodes): `DynamicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 273`** (1 nodes): `params`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Room Management Tests` to `Booking Payment Tests`, `Booking Domain Service`, `Auth Service Layer`, `Data Models & Schemas`, `Miscellaneous Module`, `Admin RBAC System`, `Auth & Login Tests`, `Teacher Management Tests`, `Token Verification`, `Booking Payment Tests`, `RBAC Service Layer`, `Room Management Tests`, `Booking Payment Tests`, `Teacher Management Tests`, `Teacher Management`, `Miscellaneous Module`, `Redis Connection`, `Payment & Wallet`, `JWT Token Tests`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `StudyRoom` connect `Wallet Service Tests` to `Auth & Login Tests`, `Booking Cancellation Tests`, `JWT Token Tests`, `Payment & Wallet`, `Booking Cancellation Tests`, `Room Management Tests`, `Auth & Login Tests`, `Auth & Login Tests`, `Booking Service Tests`, `Teacher & Course Models`, `Room Management Tests`, `Booking Verification Tests`, `Booking Payment Tests`, `User & Auth Models`, `Auth & WeChat Integration`, `Community 255`, `SMS & Captcha Tests`, `Wallet Service Layer`, `Auth & Login Tests`, `Room & Seat Management`, `Booking Cancellation Tests`, `Booking Cancellation Tests`, `Teacher & Course Models`, `Room & Seat Management`, `User Profile Tests`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `Base` connect `JWT Token Tests` to `Deployment Config`, `Booking Payment Tests`, `Booking Domain Service`, `Database Config`, `Wallet Service Tests`, `Notification System`, `Booking Cancellation Tests`, `Auth & Login Tests`, `Auth & Login Tests`, `Coupon System`, `SMS & Captcha Tests`, `Booking Cancellation Tests`, `Payment & Wallet`, `Teacher Management Tests`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 244 inferred relationships involving `StudyRoom` (e.g. with `Base` and `City`) actually correct?**
  _`StudyRoom` has 244 INFERRED edges - model-reasoned connections that need verification._
- **Are the 212 inferred relationships involving `Settings` (e.g. with `AdminAuthService` and `AuthService`) actually correct?**
  _`Settings` has 212 INFERRED edges - model-reasoned connections that need verification._
- **What connects `返回当前 Asia/Shanghai 时区的 naive datetime。`, `查询课程详情 + 课时列表 + 排课信息。          仅关联固定班课（schedule_type=fixed）排课，定制课时记录不在 C 端展示。`, `价格计算。          从排课表获取价格信息：         - fixed: len(lesson_ids) × schedule.price` to the rest of the system?**
  _439 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Booking Service Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.02699578403372773 - nodes in this community are weakly interconnected._
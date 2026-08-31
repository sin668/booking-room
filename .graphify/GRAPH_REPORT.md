# Graph Report - .  (2026-08-31)

## Corpus Check
- Large corpus: 1034 files · ~541,756 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 5362 nodes · 11311 edges · 206 communities detected
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 2485 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output
- Edge kinds: contains: 2754 · uses: 2485 · ON_BRANCH: 1278 · MODIFIES: 1200 · calls: 1000 · method: 680 · rationale_for: 589 · PARENT_OF: 406 · imports_from: 324 · inherits: 305 · imports: 283 · re_exports: 7


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 1034 · Candidates: 1467
- Excluded: 0 untracked · 89174 ignored · 0 sensitive · 24 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `408d499`
- Compare this hash to `git rev-parse HEAD` before trusting freshness-sensitive graph output.
## God Nodes (most connected - your core abstractions)
1. `StudyRoom` - 246 edges
2. `Settings` - 224 edges
3. `Course` - 165 edges
4. `Booking` - 125 edges
5. `Teacher` - 123 edges
6. `Seat` - 110 edges
7. `UserCoupon` - 99 edges
8. `Coupon` - 96 edges
9. `City` - 92 edges
10. `CourseLesson` - 82 edges

## Surprising Connections (you probably didn't know these)
- `Run migrations in 'offline' mode.      Configures the context with just a URL an` --uses--> `Base`  [INFERRED]
  br-server/alembic/env.py → br-server/app/core/database.py
- `Run migrations in 'online' mode with async engine.` --uses--> `Base`  [INFERRED]
  br-server/alembic/env.py → br-server/app/core/database.py
- `Run migrations in 'online' mode.` --uses--> `Base`  [INFERRED]
  br-server/alembic/env.py → br-server/app/core/database.py
- `课程排课表。      存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。     从 courses 表迁移出的字段：teacher_id, sc` --uses--> `Base`  [INFERRED]
  br-server/app/models/course_schedule.py → br-server/app/core/database.py
- `老师与培训室/综合室的多对多关联表。      room_id 仅允许关联 study_rooms 中 room_type 为 training 或 compr` --uses--> `Base`  [INFERRED]
  br-server/app/models/teacher_room.py → br-server/app/core/database.py

## Communities

### Community 0 - "Booking Service Tests"
Cohesion: 0.05
Nodes (143): feature/20260814/training-course-list, feature/20260817/course-booking, feature/20260817/course-detail-page, feature/20260817/teacher-profile-page, 008166a chore: Comet build→verify transition — all guard checks passed, 0191aac fix: redirect expired admin sessions to login, 037946c feat: add study record frontend page, 061bda0 feat: 实现 seat-select 页面 viewMode 只读查看模式 (+135 more)

### Community 1 - "Teacher Management Tests"
Cohesion: 0.02
Nodes (87): City, 老师与培训室/综合室的多对多关联表。      room_id 仅允许关联 study_rooms 中 room_type 为 training 或 compr, TeacherRoom, Teacher, 删除老师。返回 "ok"；不存在返回 "not_found"；存在排课返回 "has_schedules"。, 按老师统计关联课程数（去重 course_id）。, 校验房间存在且 room_type 为培训室或综合室。, get_active_cities() (+79 more)

### Community 2 - "Booking Cancellation Tests"
Cohesion: 0.04
Nodes (124): dev, main, 020ddd3 debug: 延期功能前后端参数传递添加调试日志, 04745c9 chore: archive course-booking, 04f0a66 feat: 新增订单状态定时转换任务, 051c8b1 fix: 修复开课日期不显示和过期课时禁用逻辑 - 后端返回lesson_schedules数据, 0605022 fix: 课程编辑页与列表页在原 tab 内互相跳转，不再新开标签页, 0b33239 feat: 统计区域添加连续学习天数显示 (+116 more)

### Community 3 - "Wallet Service Tests"
Cohesion: 0.04
Nodes (55): Seat, StudyRoom, PaymentProviderUnavailableError, Return set of seat_ids that have overlapping confirmed bookings., Seed seat data for existing study rooms., Generate seats for a study room. Returns number of seats created., Seed seats for all rooms. Returns total seats created., seed_all_rooms() (+47 more)

### Community 4 - "Booking Payment Tests"
Cohesion: 0.09
Nodes (77): Base, BookingCompletionInput, Booking, CourseLesson, CourseSchedule, 课程排课表。      存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。     从 courses 表迁移出的字段：teacher_id, sc, WalletTransaction, BookingRepository (+69 more)

### Community 5 - "Booking Payment Tests"
Cohesion: 0.03
Nodes (11): get_current_admin(), Shared API dependencies., Compatibility entrypoint for legacy admin route dependencies., ae1887e merge: admin RBAC dynamic settings, c623596 feat: add admin RBAC dynamic settings, columns, upload_admin_image(), _upload_image() (+3 more)

### Community 6 - "Token Verification"
Cohesion: 0.04
Nodes (54): Activity, ActivityCoupon, Coupon, UserCoupon, ActivityCouponClaimError, ActivityCouponClaimResult, ActivityCouponError, ActivityCouponPublishError (+46 more)

### Community 7 - "Room Management Tests"
Cohesion: 0.04
Nodes (68): BaseModel, AdminCurrentResponse, AdminLoginRequest, AdminMessageResponse, AdminPasswordUpdate, AdminPermissionItem, AdminProfileUpdate, AdminTokenResponse (+60 more)

### Community 8 - "Teacher Management Tests"
Cohesion: 0.04
Nodes (27): CountTo, routes, routes, routes, routes, routes, routes, routes (+19 more)

### Community 9 - "Booking Payment Tests"
Cohesion: 0.04
Nodes (55): AdminContext, Course, RoomFollow, 管理端老师管理 API 测试。  覆盖：列表分页/筛选、详情、新增、编辑、删除（含排课拒绝）、状态切换、 room_type 校验、权限控制。, 发布设置：新增时可指定 status，编辑时可通过 PUT 修改 status。, C 端培训室详情的教师团队与课程讲师过滤未激活老师。, qualifications/teaching_tags 为空时入库为 NULL，详情接口应返回 200 且容忍为空列表。, API tests for current-user followed study rooms. (+47 more)

### Community 10 - "Auth & Login Tests"
Cohesion: 0.10
Nodes (53): Exception, WalletRepository, Booking direct payment orchestration., Verify a WeChat callback and mark a booking payment as paid once., Query due pending WeChat bookings and advance their payment state., Base exception for booking payment operations., Service for booking WeChat payment creation and callbacks., Create a WeChat JSAPI payment order for a pending booking. (+45 more)

### Community 11 - "Auth & Login Tests"
Cohesion: 0.04
Nodes (41): 14c7316 Merge branch 'implement-wechat-quick-login-phone-binding' into main, 6daf2cb feat: add username profile settings, a8157af feat: add account security settings, b3ae959 feat: implement wechat quick login, d4aefe4 登录有效期调整为 3 天, change_password(), deactivate_account(), get_account_security() (+33 more)

### Community 12 - "SMS & Captcha Tests"
Cohesion: 0.03
Nodes (23): 02a1920 fix: resolve menu icons, directory paths, and hidden menu filtering (BUG-19), 2f06520 merge: unified User-AdminUser model with user management CRUD, 9093d5e docs: archive merge-users-admin-users openspec and sync specs, c069a02 feat: unify user access control — remove user_type filtering from auth, legacy_headers(), test_role_crud_duplicate_and_assigned_delete_conflict(), test_role_menu_assignment_updates_auth_permissions(), Test creating app user defaults user_type to 'app (+15 more)

### Community 13 - "Booking System Core"
Cohesion: 0.06
Nodes (46): AdminCouponItem, buildActivityCouponFormItem(), buildActivitySearchSchemas(), buildActivityTableColumns(), buildBookingSearchSchemas(), buildBookingTableColumns(), buildRoomSearchSchemas(), buildRoomTableColumns() (+38 more)

### Community 14 - "Booking Data Models"
Cohesion: 0.04
Nodes (28): 02b3b93 feat: add course-detail page with all sections (7.1-7.8), 0fc7746 chore: add teacher-profile-page OpenSpec artifacts and design doc, 148395b feat(br-app): add course detail navigation from training list page, 2323e70 feat: implement course detail API with TDD, 3437127 test(task-6): 课程详情+关注完整测试，实现 list course follows, 38a606f chore: archive course-detail-page change, 45e5bef feat: extend Course and Booking models for course booking, 7fc110c fix: 修复课程详情API访问已迁移字段的错误 (+20 more)

### Community 15 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (36): ActivityAdminResponse, ActivityCouponAdminResponse, ActivityCouponClaimResponse, ActivityCouponClaimUserCouponResponse, ActivityCouponInput, ActivityCouponPublicResponse, ActivityCouponTemplateResponse, ActivityCreate (+28 more)

### Community 16 - "Teacher Management Tests"
Cohesion: 0.06
Nodes (36): { apiUrl, urlPrefix }, mockAdapter, { useMock, loggerMock }, ContentTypeEnum, RequestEnum, ResultEnum, IAsyncRouteState, IScreenLockState (+28 more)

### Community 17 - "Auth & Login Tests"
Cohesion: 0.08
Nodes (37): bind_wechat_phone(), bind_wechat_phone_by_sms(), get_me(), login(), logout(), Authenticate or create an app user with a WeChat mini program code., Bind a phone obtained from WeChat phone authorization code., Bind a phone to a WeChat user with SMS fallback verification. (+29 more)

### Community 18 - "Auth Service Layer"
Cohesion: 0.07
Nodes (39): BaseSettings, Return missing mini program login settings without exposing values., Whether WeChat mini program login is enabled and configured., Raise a sanitized error if WeChat mini program login cannot be used., Return the normalized upload storage driver., Return missing OSS setting names without exposing configured values., Raise a sanitized error if upload storage cannot be used., Application settings loaded from environment variables and .env file. (+31 more)

### Community 19 - "Booking System Core"
Cohesion: 0.05
Nodes (28): Alova, result, TypeConsole, TypeOrderLarge, TypeSaleroom, TypeVisits, doCustomTimes(), pagination() (+20 more)

### Community 20 - "Room Management Tests"
Cohesion: 0.06
Nodes (43): AliyunSMSProvider, Aliyun Dysms API client for sending SMS verification codes., mock_redis(), Unit tests for SMS service (extended coverage)., Second send within 60 s is rejected with 429., The 11th send in one day is rejected with 429., Return a mock async Redis client., Invalid captcha token returns 400. (+35 more)

### Community 21 - "SMS & Captcha Tests"
Cohesion: 0.08
Nodes (50): admin_cancel_booking(), admin_confirm_booking(), admin_get_booking(), admin_list_bookings(), BookingAlreadyCancelledError, BookingCancellationNotAllowedError, BookingConflictError, BookingCouponUnavailableError (+42 more)

### Community 22 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (26): 023eb00 feat: add GET /api/v1/training/rooms/{room_id} route, 071ac5f chore: add implementation plan for training-room-overview, 2fe2097 feat: add get_training_room_detail to training_service (TDD green phase), 3590666 Merge branch 'feature/20260814/training-room-overview' into main, 4150deb test: add failing tests for get_training_room_detail (TDD red phase), 42c7c58 fix: commit missing Alembic migration file for training tables, 4c94688 feat: 为 StudyRoom 添加 rating 列和 city 关系，含迁移, 4ecad22 chore: add training-course-list OpenSpec artifacts, design doc, and implementation plan (+18 more)

### Community 23 - "Database Config"
Cohesion: 0.14
Nodes (47): base64url_encode(), CompactVerificationPayload, create_compact_verification_token(), decode_compact_verification_token(), ensure_utc(), ExpiredVerificationToken, InvalidVerificationToken, sign_compact_token() (+39 more)

### Community 24 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (7): 8403348 refactor: extract admin page builders, d2114a6 merge: br-admin business refactor, routes, routes, columns, adminInfo, token

### Community 25 - "JWT Token Tests"
Cohesion: 0.07
Nodes (32): Base, get_db(), FastAPI dependency that provides an async database session., DeclarativeBase, SystemSetting, UserIdentityVerification, User, _create_access_token() (+24 more)

### Community 26 - "Auth & WeChat Integration"
Cohesion: 0.05
Nodes (28): ADMIN_NATIVE_META, AdminPageParams, AdminPageResponse, BasicTableResult, compactQuery(), normalizePageParams(), toBasicTableResult(), AdminLoginParams (+20 more)

### Community 27 - "Coupon System"
Cohesion: 0.07
Nodes (23): Notification, NotificationPreference, NotificationType, NotificationNotFoundError, NotificationService, _preference_enabled(), _validate_type(), StrEnum (+15 more)

### Community 28 - "Teacher Management"
Cohesion: 0.08
Nodes (37): legacy_headers(), seed_users(), test_create_admin_user(), test_create_admin_user_requires_username(), test_create_app_user(), test_create_app_user_invalid_phone_format(), test_create_app_user_requires_phone(), test_create_duplicate_phone_returns_409() (+29 more)

### Community 29 - "Data Models & Schemas"
Cohesion: 0.06
Nodes (23): mock_db(), _mock_keys_result(), _mock_scalar_result(), Unit tests for AuthService., Successful registration returns TokenResponse., Registering with an existing phone raises 409., Registering with invalid SMS code raises 400., When nickname is None, a default '学习者XXXXXX' nickname is generated. (+15 more)

### Community 30 - "Miscellaneous Module"
Cohesion: 0.06
Nodes (29): CaptchaService, Aliyun Captcha 2.0 verification service., Verify a captcha token.          - If no ``ALIYUN_CAPTCHA_SCENE_ID`` is configur, Check whether a captcha token has already been consumed., _percent_encode(), SMS verification code service with rate-limiting., Return a 6-digit random numeric string., Send a verification code to *phone*.          Workflow:         1. Validate capt (+21 more)

### Community 31 - "Auth & Login Tests"
Cohesion: 0.08
Nodes (27): get_current_admin_context(), get_current_user_id(), get_optional_current_user_id(), Extract and validate the current user ID from the access token., 有登录凭证时解析用户 ID，无凭证时返回 None。, Resolve the current administrator from Bearer or legacy admin token., AdminMenu, AdminRole (+19 more)

### Community 32 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (7): 7d72fbb test: add study record service and API tests, TestGetSummary, TestListRecords, _add_booking(), TestCalculateStreakDays, TestGetMonthlySummary, TestListStudyRecords

### Community 33 - "Auth & WeChat Integration"
Cohesion: 0.06
Nodes (19): 1e48f73 fix: 老师详情接口容忍 qualifications 为 NULL（AdminTeacherDetail 校验失败 500）, 7a418d3 tweak: 老师管理后端 — teachers 表扩展 + teacher_rooms 关联 + 管理端 CRUD API + C 端详情扩展与测试, be95476 feat: 老师新增/编辑页发布设置（是否激活）+ C 端老师列表过滤未激活 + 学习室编辑页行距统一, AdminTeacherCreate, AdminTeacherDetail, AdminTeacherListItem, AdminTeacherListResponse, AdminTeacherStatusUpdate (+11 more)

### Community 34 - "Payment & Wallet"
Cohesion: 0.06
Nodes (21): _booking_payment_reconciliation_loop(), _cleanup_unpaid_bookings_job(), lifespan(), Fallback periodic runner for environments without APScheduler., Application lifespan: startup and shutdown events., BookingItem, BookingListParams, BookingListResult (+13 more)

### Community 35 - "Booking Payment Tests"
Cohesion: 0.08
Nodes (23): PageEnum, DEFAULT_CONFIG, filter(), getConfig(), TreeHelperConfig, useAsyncRoute(), useAsyncRouteStore, ProjectSettingState (+15 more)

### Community 36 - "Booking Domain Service"
Cohesion: 0.06
Nodes (12): 7721d2b feat: 自习室新建/编辑改为页面跳转，列表新增城市/类型列与过滤，支持环境图片与上架状态, 7d4de92 chore: 房间管理模块文案「自习室」统一替换为「学习室」, routes, admin_get_room(), admin_list_rooms(), create_room(), delete_room(), get_study_room() (+4 more)

### Community 37 - "Booking Service Tests"
Cohesion: 0.06
Nodes (24): jwt_service(), _mock_keys_result(), mock_redis(), Unit tests for JWTService., Refresh token contains sub, type=refresh, exp, and jti., Each refresh token gets a unique jti., blacklist_token stores the jti in Redis with correct TTL., Return an AsyncMock whose coroutine resolves to the given list. (+16 more)

### Community 38 - "Course Management"
Cohesion: 0.11
Nodes (20): 2caef8e Merge pull request #2 from sin668/feat/booking-room-list-detail-fix, 5187776 feat: show wallet balance on booking confirmation, 548e6b2 fix: load profile wallet stats, 549c0fa refactor br-app mobile UI, 597670e Add profile stat navigation links, 7487fee style: soften booking wallet balance, 794936b Add persisted study room follows, 887d314 refactor: share payment polling logic (+12 more)

### Community 39 - "Booking Cancellation Tests"
Cohesion: 0.06
Nodes (2): routes, ParentLayout()

### Community 40 - "Miscellaneous Module"
Cohesion: 0.07
Nodes (13): ActivityCouponBase, ActivityCouponFormItem, ActivityCouponItem, ActivityCouponTemplate, ActivityFormParams, ActivityItem, ActivityListParams, ActivityListResult (+5 more)

### Community 41 - "Coupon Service Layer"
Cohesion: 0.08
Nodes (6): 4df870a fix: 课程编辑页路由使用 hideInMenu 替代 hidden 以匹配动态路由合并逻辑, 55e7654 feat: 实现课程编辑后台页面及课时CRUD功能, cbcedef fix: 修复课程列表删除按钮颜色值错误导致的渲染崩溃, f8f8716 fix: 修复培训课程菜单图标不显示和课程列表为空的问题, fc88d29 feat: 培训课程列表新增排课弹窗功能, routes

### Community 42 - "Teacher Management Tests"
Cohesion: 0.08
Nodes (7): 3302a91 feat: add coupon package booking flow, d14db83 Merge branch 'feature/coupon-package-frontend', AdminCouponCreateParams, AdminCouponListParams, AdminCouponListResult, AdminCouponUpdateParams, add_coupon_models  Revision ID: b3a7c9d2e4f1 Revises: 985785a787d8 Create Date:

### Community 43 - "Booking Service Tests"
Cohesion: 0.07
Nodes (15): CourseCreateParams, CourseDetail, CourseItem, CourseListResult, CourseScheduleItem, CourseUpdateParams, LessonCreateParams, LessonItem (+7 more)

### Community 44 - "Coupon Service Tests"
Cohesion: 0.09
Nodes (15): Props, useForm(), EmitType, UseFormActionContext, DATE_TYPE, dateItemType, basicProps, FormActionType (+7 more)

### Community 45 - "Deployment Config"
Cohesion: 0.13
Nodes (19): UseFormValuesContext, is(), isArray(), isAsyncFunction(), isBoolean(), isDate(), isDef(), isElement() (+11 more)

### Community 46 - "Token Verification"
Cohesion: 0.06
Nodes (8): Integration tests for admin activity API endpoints., TestAdminAuth, TestAdminCreateActivity, TestAdminDeleteActivity, TestAdminGetActivity, TestAdminListActivities, TestAdminToggleStatus, TestAdminUpdateActivity

### Community 47 - "Booking Verification Service"
Cohesion: 0.17
Nodes (22): _mock_scalar_one_result(), _mock_scalar_result(), _mock_scalars_result(), test_admin_get_statistics_aggregates_totals_and_active_users(), test_admin_list_transactions_joins_users_and_maps_user_fields(), test_confirm_payment_disabled_in_production(), test_create_recharge_order_rejects_unsupported_alipay(), test_create_wechat_recharge_order_returns_payment_params() (+14 more)

### Community 48 - "Booking Domain Service"
Cohesion: 0.08
Nodes (6): 7c70899 feat: add VIP membership and coupon admin, ed78866 Implement wallet recharge flow, create_wallet_table  Revision ID: 28a1f4af90df Revises: b3a7c9d2e4f1 Create Date, update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:, add_membership_level  Revision ID: df6ae550899a Revises: f1a2b3c4d5e6 Create Dat, add_wallet_membership_result  Revision ID: a2b3c4d5e6f7 Revises: df6ae550899a Cr

### Community 49 - "Auth Service Layer"
Cohesion: 0.09
Nodes (13): _make_course(), Unit tests for CourseBookingService., full_package_price 为 None 时不触发优惠。, full_package_price 高于标准价时，discount_amount 为 0。, 空 lesson_ids 应被 Schema 拒绝。, 不存在的 course_id 返回 None。, 构造一个轻量 Course mock 对象。, 固定班课：3 课时 × ¥80 = ¥240。 (+5 more)

### Community 50 - "Booking Cancellation Tests"
Cohesion: 0.13
Nodes (11): AdminAssignRoles, AdminResetPassword, AdminToggleStatus, AdminUserCreate, AdminUserDetail, AdminUserListItem, AdminUserListParams, AdminUserListResponse (+3 more)

### Community 51 - "Booking Cancellation Tests"
Cohesion: 0.15
Nodes (25): ALIGNMENT_POSITIONS, appendBits(), applyMask(), chooseVersion(), cloneMatrix(), createCodewords(), createDataCodewords(), createQrSvgDataUrl() (+17 more)

### Community 52 - "User & Auth Models"
Cohesion: 0.22
Nodes (23): NamedTuple, BookingCouponCalculation, _calc_discount(), _calculate_hours(), _calculate_original_price(), _check_scope(), CouponError, CouponNotFoundError (+15 more)

### Community 53 - "Booking Payment Service"
Cohesion: 0.08
Nodes (8): Integration tests for Course Booking API.  注意：当前测试基础设施使用 SQLite 内存数据库，不支持 Postgr, POST /api/v1/course-bookings。, 无效 lesson_ids 返回 400。, POST /api/v1/course-bookings/{booking_id}/cancel。, GET /api/v1/courses/{id}/lessons。, TestCancelCourseBooking, TestCreateCourseBooking, TestGetCourseLessons

### Community 54 - "Teacher Management Tests"
Cohesion: 0.11
Nodes (6): 3baaa8d feat: integrate WeChat wallet payments, b15c9d7 updated .gitignore, b610482 Archive wechat payment integration OpenSpec change, e07a2b2 feat: add wallet transactions frontend, f93686c merge: wallet transactions frontend, add_wechat_payment_fields  Revision ID: a8c3f1b2d4e5 Revises: 7c9d2e4f6a1b Creat

### Community 55 - "Miscellaneous Module"
Cohesion: 0.13
Nodes (11): AppMiddleware, health_check(), Health check endpoint., _json_dumps(), _parse_response(), Build mini program payment params for uni.requestPayment., Query an order by merchant out_trade_no., Verify notification signature, decrypt resource, and validate fields. (+3 more)

### Community 57 - "Booking Data Models"
Cohesion: 0.21
Nodes (22): _activity_coupon_to_public_response(), _activity_to_admin_response(), _admin_coupon_to_response(), claim_activity_coupon(), claim_activity_coupon_response(), _count_user_claims(), _coupon_to_response(), create_activity() (+14 more)

### Community 59 - "Auth & Login Tests"
Cohesion: 0.17
Nodes (19): _access_token(), _phone_user(), _temp_wechat_user(), test_bind_phone_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_sms_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_with_sms_to_new_phone(), test_bind_wechat_phone_code_to_new_phone(), test_bound_user_binding_unused_phone_returns_409() (+11 more)

### Community 60 - "Booking Service Tests"
Cohesion: 0.09
Nodes (23): ChangeEvent, DeepPartial, Element, ElementAttributesProperty, ElementClass, Event, ImportMetaEnv, Indexable (+15 more)

### Community 61 - "Teacher Management Tests"
Cohesion: 0.09
Nodes (12): BookingUseCases, Application use case orchestration layer., 3709fe0 docs: localize br-app refactor plan, 645d7d5 refactor: extract booking repository conflict query, 9ea74c1 test: align admin booking detail fixture assertion, bb3b56d refactor: extract verification token rules, bfd21f6 refactor: extract wallet transaction repository, e2a44c1 refactor: add app formatter constants (+4 more)

### Community 62 - "Teacher Management Tests"
Cohesion: 0.10
Nodes (6): 0b53f3b 优化UI, 1ab6fd7 polish: refine training page TAB navigation for a more refined look, 836a7bb chore: archive training-room-overview change and sync delta specs to main specs, 8e4fbeb chore: archive training-room-overview change & add course-detail-page proposal, 9157d84 polish: align training course list UI with study room booking page, d84d0ce feat: 培训室概况页课程列表UI优化 - 后端: HotCourseItem 添加 schedule/tags 字段, TrainingRoomResponse 添加 rating - 后端: training_service 传递 schedule/tags 到热门课程 - 前端: training/index.vue 培训室名称可点击跳转到概况页 - 前端: 课程项添加时钟图标+培训时间+热销/新课/名师标签 - 前端: booking/detail.vue 课程列表同步优化UI样式

### Community 64 - "Deployment Config"
Cohesion: 0.19
Nodes (20): AdminCouponCreate, AdminCouponListResponse, AdminCouponResponse, AdminCouponStatusUpdate, AdminCouponUpdate, AdminCouponError, AdminCouponNotFoundError, _clean_coupon_data() (+12 more)

### Community 65 - "Backend Service Layer"
Cohesion: 0.11
Nodes (5): AdminCourseService, 延期某一课时及其后续所有课时。          逻辑：         1. 从 course_lessons 表获取课时列表         2. 解析 t, 从 lesson_schedule JSON 中计算 end_date（最后一个课时日期 + 1 天）。, 根据 start_date 和 time_slots 生成至少 needed 个可用时间槽位。          按日期+时间段排序，循环扩展周次直到生成足够槽, 将 CourseSchedule 模型转换为 CourseScheduleResponse。

### Community 67 - "Booking Cancellation Tests"
Cohesion: 0.26
Nodes (17): _make_booking(), _make_coupon(), _make_room(), _make_seat(), _make_user(), _make_user_coupon(), test_admin_cancel_booking(), test_admin_cancel_booking_already_cancelled() (+9 more)

### Community 69 - "Booking Payment Tests"
Cohesion: 0.21
Nodes (7): BookingPaymentAlreadyProcessedError, BookingPaymentError, BookingPaymentNotFoundError, BookingPaymentService, BookingPaymentSignatureError, InvalidBookingPaymentCallbackError, WechatOpenIdRequiredError

### Community 70 - "Miscellaneous Module"
Cohesion: 0.19
Nodes (1): WechatAuthService

### Community 71 - "User Security Tests"
Cohesion: 0.14
Nodes (9): 89f0643 feat: load booking detail seat stats from backend, d4a1403 chore: archive wallet transactions frontend spec, admin_list_seats(), bulk_create_seats(), create_seat(), _get_booked_seat_ids(), get_seat_stats(), list_seats() (+1 more)

### Community 72 - "Booking Service Tests"
Cohesion: 0.15
Nodes (8): EditRecordRow, renderEditCell(), Instance, key, RetInstance, BasicColumn, BasicTableProps, TableActionType

### Community 73 - "Course Management"
Cohesion: 0.11
Nodes (12): BusinessSelectOption, useAdminBusiness(), useAdminBusinessStore, CityItem, getRoomList(), RoomFormParams, RoomItem, RoomListParams (+4 more)

### Community 74 - "Booking System Core"
Cohesion: 0.11
Nodes (8): 6288c60 feat: add booking wechat payment flow, cleanup_unpaid_bookings(), Cleanup for unpaid booking payment holds., Cancel stale pending WeChat bookings and restore attached coupons., auth_client(), other_auth_client(), seed_room_seat(), add_booking_payment_fields  Adds payment-related fields to bookings table: - pay

### Community 75 - "Token Verification"
Cohesion: 0.13
Nodes (14): applyWechatAppId(), DEFAULT_DEV_OUTPUT_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_SERVER_ENV_PATH, fs, parseEnvFile(), path, resolveOutputDirFromArgs() (+6 more)

### Community 76 - "Miscellaneous Module"
Cohesion: 0.11
Nodes (1): admin_client()

### Community 77 - "Auth & WeChat Integration"
Cohesion: 0.11
Nodes (15): 培训课程相关 Schema 导入与功能测试  验证以下 schema 能正确导入和使用： - TeacherResponse, TeacherBrief, Ho, StudyRoomResponse 包含 room_type 字段, RoomCreate 包含 room_type 字段，默认值 study, RoomUpdate 包含 room_type 字段，默认 None, RoomAdminResponse 包含 room_type 字段, TeacherResponse 可正确导入并实例化, course.py 中所有 schema 可正确导入, CourseResponse.parse_tags 正确解析逗号分隔字符串 (+7 more)

### Community 78 - "Integration Tests"
Cohesion: 0.11
Nodes (5): Integration tests for training room and course APIs., Insert training rooms, teachers, and courses into the test database., seed_training_data(), TestCoursesAPI, TestTrainingRoomsAPI

### Community 79 - "Notification System"
Cohesion: 0.12
Nodes (3): 00cde52 Implement dynamic booking verification QR flow, 39024d3 fix: stabilize booking verification QR flow, 7143168 Archive personal QR OpenSpec change

### Community 80 - "Course Management"
Cohesion: 0.16
Nodes (14): ClickOutside, DocumentHandler, FlushList, nodeList, addClass(), getBoundingClientRect(), getViewportOffset(), hasClass() (+6 more)

### Community 81 - "Teacher & Course Models"
Cohesion: 0.15
Nodes (17): Enum, PaymentMethod, PaymentStatus, BookingAdminListResponse, BookingAdminResponse, BookingCreate, BookingListResponse, BookingResponse (+9 more)

### Community 82 - "Room & Seat Management"
Cohesion: 0.18
Nodes (4): _coupon(), _seed_activity_coupon(), TestActivityCouponAPI, TestActivityCouponService

### Community 83 - "RBAC Service Layer"
Cohesion: 0.19
Nodes (2): _payload(), TestAdminTeacherApi

### Community 85 - "Booking Verification Tests"
Cohesion: 0.23
Nodes (5): hash_id_card(), is_valid_id_card(), mask_id_card(), mask_phone(), UserSecurityService

### Community 86 - "Booking Service Tests"
Cohesion: 0.12
Nodes (2): admin_client(), unauth_client()

### Community 87 - "Booking Service Tests"
Cohesion: 0.12
Nodes (1): TestCreateBooking

### Community 88 - "Booking Service Tests"
Cohesion: 0.15
Nodes (7): COURSE_WEEKDAY_NAMES, formatAmount(), formatHourCount(), formatHourDuration(), formatMoney(), formatRoomMinPrice(), toFiniteNumber()

### Community 89 - "Coupon System"
Cohesion: 0.21
Nodes (16): del(), doRefreshToken(), get(), getRefreshToken(), getToken(), patch(), pendingRequests, post() (+8 more)

### Community 90 - "Database Config"
Cohesion: 0.17
Nodes (11): 316d285 feat: add study record schemas, 5ce3f55 Merge branch 'worktree-learning-record-impl' into main, 83ccd35 feat: add study record backend (schema, service, routes), CalendarMark, StudyRecordItem, StudyRecordListResponse, StudyRecordSummaryResponse, _build_record_item() (+3 more)

### Community 91 - "Room & Seat Management"
Cohesion: 0.16
Nodes (8): useModal(), BasicProps, ModalMethods, ModalProps, RegisterFn, UseModalReturnType, isProdMode(), getDynamicProps()

### Community 92 - "Auth & Login Tests"
Cohesion: 0.17
Nodes (10): Banner, list_active_banners(), Return all active banners ordered by sort_order ascending., Unit tests for banner_service module., Seed banners for tests., Only active banners are returned., Results are ordered by sort_order ascending., Empty DB returns empty list. (+2 more)

### Community 94 - "Room & Seat Management"
Cohesion: 0.16
Nodes (11): asyncImportRoute(), generateDynamicRoutes(), generateRoutes(), LayoutMap, constantRouterIcon, AppRouteRecordRaw, Component, IModuleType (+3 more)

### Community 95 - "Room Management Tests"
Cohesion: 0.14
Nodes (4): create_course(), get_course_detail(), Admin course management API routes., update_course()

### Community 96 - "Database Seed Data"
Cohesion: 0.13
Nodes (8): SeatBulkParams, SeatBulkResult, SeatBulkZoneConfig, SeatFormParams, SeatItem, SeatListParams, SeatStatusParams, SeatUpdateParams

### Community 98 - "Booking Service Tests"
Cohesion: 0.13
Nodes (14): AdminWalletStatisticsResponse, AdminWalletTransactionListResponse, AdminWalletTransactionResponse, BalanceResponse, PaymentParams, PromoCodeRequest, PromoCodeResponse, RechargeOrderResponse (+6 more)

### Community 99 - "Teacher Management"
Cohesion: 0.24
Nodes (1): TestCancelBooking

### Community 100 - "Miscellaneous Module"
Cohesion: 0.13
Nodes (2): Integration tests for file upload API endpoints., TestUploadAPI

### Community 102 - "Teacher Management Tests"
Cohesion: 0.27
Nodes (13): appRoot, assert, fs, loadModule(), main(), path, testAccountSecurity(), testAccountSecurityApi() (+5 more)

### Community 103 - "Data Model Tests"
Cohesion: 0.30
Nodes (1): AdminMenuService

### Community 104 - "Coupon Service Tests"
Cohesion: 0.29
Nodes (13): _apply_menu_seed(), _ensure_role_menus(), _ensure_user_role(), _get_or_create_admin(), _get_or_create_app_role(), _get_or_create_menu(), _get_or_create_role(), main() (+5 more)

### Community 105 - "Miscellaneous Module"
Cohesion: 0.14
Nodes (8): Tests for API dependencies., Invalid token returns 401., No admin token returns 401., Wrong admin token returns 401., No credentials (no Authorization header) returns 401., Valid access token returns the user ID., TestGetCurrentAdmin, TestGetCurrentUserId

### Community 107 - "Auth & WeChat Integration"
Cohesion: 0.19
Nodes (8): 7979a96 Complete admin wallet backend, 90b89ef docs: document admin wallet finance api, 9e3fd4a feat: 注册 admin_wallet 路由到 main.py, a67a5e8 fix: 修正交易列表路由路径为 /transactions, fb3958c feat: 新增管理端钱包路由（含 CSV 导出）, _admin_wallet_base_conditions(), export_transactions(), Tests for admin wallet API routes.

### Community 108 - "Integration Tests"
Cohesion: 0.18
Nodes (8): debounce, ElType, HTMLElement, permission, ElType, HTMLElement, throttle, usePermission()

### Community 109 - "Teacher Service Layer"
Cohesion: 0.21
Nodes (7): DesignSettingState, useDesignSetting(), useDesignSettingStore, setupRouter(), pinia, setupStore(), store

### Community 110 - "Room & Seat Service"
Cohesion: 0.23
Nodes (3): _make_user(), TestProcessVipUpgrade, TestVIPScopeFilter

### Community 111 - "Miscellaneous Module"
Cohesion: 0.24
Nodes (4): ComponentProps, componentMap, EventEnum, ComponentType

### Community 113 - "Auth & Login Tests"
Cohesion: 0.30
Nodes (10): _course_count_map(), create_teacher(), delete_teacher(), get_teacher_detail(), list_teachers(), _load_rooms_for_teachers(), _sync_teacher_rooms(), _tags_to_db() (+2 more)

### Community 114 - "Booking Cancellation Tests"
Cohesion: 0.17
Nodes (6): Delete a refresh token reference from Redis., Delete every stored refresh token for a user., Check whether a refresh token is still valid (present in Redis)., Rotate a refresh token: create a new one, store it, revoke the old one., Create a long-lived refresh token with a unique jti.          Payload contains:, Store a refresh token reference in Redis.          Key: ``refresh:{user_id}:{jti

### Community 117 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (9): _create_user(), test_change_password_rejects_bad_old_password_or_mismatch(), test_change_password_updates_hash_and_revokes_refresh_tokens(), test_deactivate_account_blocks_risks(), test_deactivate_account_sets_deleted_without_removing_user(), test_security_summary_masks_sensitive_fields(), test_security_summary_returns_deleted_unbound_unverified_state(), test_submit_identity_rejects_invalid_or_different_verified() (+1 more)

### Community 120 - "Booking Payment Service"
Cohesion: 0.18
Nodes (1): routes

### Community 121 - "Wallet Service Layer"
Cohesion: 0.29
Nodes (10): 0072a7a 时区Bug fixed, 0f28968 Bug fixed, 5c47a3c archive coupon package frontend openspec change, c66da47 updated bug-fixed.md, _china_now_naive(), _get_or_create_demo_user(), seed_all(), seed_coupons() (+2 more)

### Community 122 - "User & Auth Models"
Cohesion: 0.25
Nodes (7): screenEnum, screenMap, sizeEnum, CreateCallbackParams, RemoveEventFn, useEventListener(), UseEventParams

### Community 123 - "RBAC Service Layer"
Cohesion: 0.29
Nodes (7): _build_wechat_client(), create_booking(), get_payment_status(), _notify_failure(), pay_pending_booking_route(), _payment_service(), wechat_notify()

### Community 124 - "Miscellaneous Module"
Cohesion: 0.35
Nodes (10): _build_wechat_client(), confirm_recharge(), create_recharge(), get_balance(), get_recharge_order(), list_transactions(), _notify_failure(), redeem_promo_code() (+2 more)

### Community 125 - "Admin Coupon Tests"
Cohesion: 0.40
Nodes (1): AdminSettingService

### Community 127 - "Teacher Management Tests"
Cohesion: 0.33
Nodes (3): _coupon_data(), _create_coupon(), TestAdminCouponService

### Community 128 - "Seat Management Tests"
Cohesion: 0.22
Nodes (2): _payload(), TestAdminCouponApi

### Community 129 - "Teacher Management Tests"
Cohesion: 0.18
Nodes (5): 测试 training_service.get_course_detail()。, 正常返回课程详情，含教师、教室、课时和相关课程。, 无教师的课程，teacher 字段为 None。, 无同分类课程时，related_courses 为空列表。, TestGetCourseDetailService

### Community 130 - "Auth & Login Tests"
Cohesion: 0.18
Nodes (6): TrainingRoomDetailResponse schema 测试, 验证嵌套 CourseResponse 的 tags 为 None 时解析为空列表, 验证缺少必填字段时抛出 ValidationError, 验证 teachers 和 courses 字段默认值为空列表, 验证嵌套的 CourseResponse 中 tags 字段可以正确解析逗号分隔字符串, TestTrainingRoomDetailResponse

### Community 131 - "Token Verification"
Cohesion: 0.22
Nodes (3): test_first_wechat_login_creates_phone_null_user_and_caches_session_key(), test_repeat_wechat_login_reuses_bound_user(), _token_sub()

### Community 133 - "HTML Sanitizer"
Cohesion: 0.27
Nodes (6): 3252e57 实现预约取消退款, booking_now(), booking_start_datetime(), calculate_cancellation_policy(), CancellationPolicyResult, add booking cancellation audit fields  Revision ID: b8c9d0e1f2a3 Revises: a7b8c9

### Community 134 - "User Management"
Cohesion: 0.20
Nodes (4): TransactionLike, Protocol, Persist an upload object and return the public result., StorageAdapter

### Community 136 - "Room & Seat Models"
Cohesion: 0.24
Nodes (2): HTMLParser, _RichTextSanitizer

### Community 137 - "Booking Payment Service"
Cohesion: 0.27
Nodes (6): setupCustomComponents(), setupDirectives(), setupGlobalMethods(), naive, setupNaive(), setupNaiveDiscreteApi()

### Community 139 - "Booking Service Tests"
Cohesion: 0.33
Nodes (1): AdminRoleService

### Community 141 - "User Profile Tests"
Cohesion: 0.20
Nodes (1): TestSeatAPI

### Community 142 - "Teacher Management Tests"
Cohesion: 0.36
Nodes (8): _create_user(), test_get_current_user_profile_returns_username_fields(), test_update_nickname_does_not_require_username_cooldown(), test_update_profile_rejects_protected_fields(), test_update_username_rejects_cooldown(), test_update_username_rejects_duplicate(), test_update_username_rejects_invalid_format(), test_update_username_success_sets_cooldown_timestamp()

### Community 143 - "Auth & Login Tests"
Cohesion: 0.20
Nodes (3): 测试 GET /api/v1/training/courses/{course_id} 路由。, 相关课程超过 6 门时，只返回 6 门，排除当前课程。, TestCourseDetailRoute

### Community 145 - "Miscellaneous Module"
Cohesion: 0.20
Nodes (9): GlobConfig, GlobEnvConfig, IBodySetting, ICrumbsSetting, IHeaderSetting, IMenuSetting, IMultiTabsSetting, LocalConfig (+1 more)

### Community 146 - "Project Documentation"
Cohesion: 0.20
Nodes (9): ComponentElRef, ComponentRef, ElRef, EmitType, Fn, LabelValueOptions, PromiseFn, RefType (+1 more)

### Community 147 - "Deployment Config"
Cohesion: 0.29
Nodes (10): bchRemainder(), bitLength(), drawAlignment(), drawFinder(), drawFormatInfo(), drawFunctionPatterns(), drawVersionInfo(), FORMAT_COORDS_2() (+2 more)

### Community 148 - "Miscellaneous Module"
Cohesion: 0.28
Nodes (3): adminRequest(), confirmVerification(), inspectVerificationToken()

### Community 150 - "Teacher Management"
Cohesion: 0.22
Nodes (3): 0fad7a7 fix: resolve API 307 redirect and 404 caused by trailing slash inconsistency, bc0df21 docs: archive coupon management admin spec, df8ff83 fix: improve activity coupon selection

### Community 151 - "Miscellaneous Module"
Cohesion: 0.31
Nodes (4): useTimeoutFn(), useTimeoutRef(), useBreakpoint(), useDesignSetting()

### Community 152 - "RBAC Data Models"
Cohesion: 0.22
Nodes (7): COURSE_CATEGORY_LABELS, COURSE_CATEGORY_OPTIONS, COURSE_STATUS_TAGS, BusinessTagConfig, EDUCATION_OPTIONS, ROOM_TYPE_LABELS, TEACHER_STATUS_TAGS

### Community 153 - "Token Verification"
Cohesion: 0.25
Nodes (7): AdminMenuBase, AdminMenuCreate, AdminMenuNode, AdminMenuRoute, AdminMenuRouteMeta, AdminMenuUpdate, ComponentOption

### Community 154 - "Room & Seat Management"
Cohesion: 0.22
Nodes (8): exportMatch, fs, getCallMatch, paramMatch, path, source, trainingApiPath, urlMatch

### Community 155 - "JWT Token Tests"
Cohesion: 0.39
Nodes (7): followRoom(), getFollowedRooms(), isRoomFollowed(), normalizeRoom(), setFollowedRooms(), syncFollowedRooms(), unfollowRoom()

### Community 156 - "Integration Tests"
Cohesion: 0.22
Nodes (4): BasicSettings, EmailSettings, nativeMeta, SystemSettings

### Community 157 - "Deployment Config"
Cohesion: 0.22
Nodes (1): TestAvailableCouponsForBooking

### Community 158 - "Database Migrations"
Cohesion: 0.22
Nodes (5): get_current_user_id returns the user UUID from a valid access token., get_current_user_id raises 401 for a blacklisted token., get_current_user_id raises 401 when token type is not 'access'., get_current_user_id raises 401 for an expired token., TestGetCurrentUserId

### Community 159 - "Miscellaneous Module"
Cohesion: 0.33
Nodes (5): getAppEnvConfig(), getCommonStoragePrefix(), getEnv(), getStorageShortName(), warn()

### Community 160 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (6): Run migrations in 'offline' mode.      Configures the context with just a URL an, Run migrations in 'online' mode with async engine., Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online()

### Community 161 - "Miscellaneous Module"
Cohesion: 0.39
Nodes (5): create_coupon(), delete_coupon(), _service_error(), toggle_coupon_status(), update_coupon()

### Community 163 - "Room & Seat Management"
Cohesion: 0.36
Nodes (5): create_teacher(), get_teacher_detail(), Admin teacher management API routes., toggle_teacher_status(), update_teacher()

### Community 164 - "Teacher Management"
Cohesion: 0.32
Nodes (3): list_notifications(), mark_all_notifications_read(), _parse_notification_type()

### Community 165 - "User Management"
Cohesion: 0.29
Nodes (7): AdminRoleBase, AdminRoleCreate, AdminRoleListResponse, AdminRoleMenusResponse, AdminRoleMenuUpdate, AdminRoleResponse, AdminRoleUpdate

### Community 166 - "Notification System"
Cohesion: 0.32
Nodes (6): assertContains(), assertMatches(), fs, path, read(), root

### Community 167 - "RBAC Data Models"
Cohesion: 0.29
Nodes (7): appRoot, assert, fs, loadModule(), main(), path, vm

### Community 168 - "Data Models & Schemas"
Cohesion: 0.25
Nodes (7): failures, fs, path, profilePath, requiredLinks, source, statsCardMatch

### Community 169 - "Room & Seat Models"
Cohesion: 0.46
Nodes (7): followCourse(), getFollowedCourses(), isCourseFollowed(), normalizeCourse(), setFollowedCourses(), syncFollowedCourses(), unfollowCourse()

### Community 171 - "Token Verification"
Cohesion: 0.43
Nodes (6): _policy(), test_exact_24_hours_charges_20_percent(), test_exact_2_hours_charges_50_percent(), test_exact_48_hours_charges_10_percent(), test_non_round_amount_keeps_penalty_and_refund_balanced(), test_over_48_hours_full_refund()

### Community 176 - "Teacher Management"
Cohesion: 0.52
Nodes (5): createUploadError(), normalizeErrorMessage(), parseUploadResponse(), uploadImage(), uploadOnce()

### Community 177 - "Auth & Login Tests"
Cohesion: 0.33
Nodes (6): close_redis(), get_redis(), init_redis(), Initialize and return the singleton Redis connection., Close the Redis connection., FastAPI dependency that provides an async Redis connection.

### Community 180 - "Project Documentation"
Cohesion: 0.52
Nodes (6): followTeacher(), getFollowedTeachers(), isTeacherFollowed(), normalizeTeacher(), setFollowedTeachers(), unfollowTeacher()

### Community 183 - "Auth & WeChat Integration"
Cohesion: 0.29
Nodes (4): GET /me without auth returns 401., GET /me with valid auth returns user info., GET /me with auth but user not in DB returns 404., TestGetMeAuth

### Community 184 - "Payment & Wallet"
Cohesion: 0.29
Nodes (4): Tests for the Booking model., Test that required fields are enforced., TestBookingDefaults, TestBookingRequiredFields

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

### Community 194 - "Database Seed Data"
Cohesion: 0.33
Nodes (2): Integration tests for city APIs., TestCityAPI

### Community 195 - "Wallet Service Layer"
Cohesion: 0.33
Nodes (2): Unit tests for the City model., TestCityModel

### Community 199 - "Booking Service Tests"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 200 - "Community 200"
Cohesion: 0.40
Nodes (3): copy, ElType, HTMLElement

### Community 201 - "Community 201"
Cohesion: 0.60
Nodes (3): can_cancel_paid_booking(), has_booking_started(), should_mark_booking_completed()

### Community 202 - "Community 202"
Cohesion: 0.50
Nodes (3): PermissionsEnum, ActionItem, PopConfirm

### Community 203 - "Community 203"
Cohesion: 0.60
Nodes (4): AvailableCouponForBookingResponse, AvailableCouponsForBookingListResponse, CouponBaseResponse, CouponResponse

### Community 204 - "Community 204"
Cohesion: 0.60
Nodes (3): createPaymentStatusError(), getPaymentStatus(), pollPaymentStatus()

### Community 205 - "Community 205"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 206 - "Community 206"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 207 - "Community 207"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 208 - "Community 208"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_component_options_and_invalid_component(), test_dynamic_routes_exclude_buttons_and_disabled_nodes(), test_menu_tree_crud_and_delete_child_conflict()

### Community 209 - "Community 209"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_email_test_requires_complete_config(), test_settings_read_masks_smtp_password(), test_update_email_without_password_preserves_existing_secret()

### Community 210 - "Community 210"
Cohesion: 0.40
Nodes (2): StudyRoom.room_type 字段验证。, TestStudyRoomRoomType

### Community 211 - "Community 211"
Cohesion: 0.40
Nodes (1): TestTeacherModel

### Community 212 - "Community 212"
Cohesion: 0.40
Nodes (3): NOTIFICATION_TYPE_CONFIGS, NOTIFICATION_TYPE_MAP, NOTIFICATION_TYPES

### Community 213 - "Community 213"
Cohesion: 0.50
Nodes (3): _generate_username(), add_username_updated_at  Adds users.username_updated_at and backfills existing u, upgrade()

### Community 215 - "Community 215"
Cohesion: 0.50
Nodes (3): BOOKING_STATUS_LABELS, BOOKING_TABS, SEAT_ZONE_LABELS

### Community 216 - "Community 216"
Cohesion: 0.50
Nodes (3): draggable, ElType, HTMLElement

### Community 217 - "Community 217"
Cohesion: 0.83
Nodes (2): setLoading(), useAsync()

### Community 218 - "Community 218"
Cohesion: 0.50
Nodes (1): key

### Community 219 - "Community 219"
Cohesion: 0.50
Nodes (1): useCityStore

### Community 222 - "Community 222"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17

### Community 223 - "Community 223"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:

### Community 224 - "Community 224"
Cohesion: 0.50
Nodes (1): create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create

### Community 225 - "Community 225"
Cohesion: 0.50
Nodes (1): create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat

### Community 226 - "Community 226"
Cohesion: 0.50
Nodes (1): booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:

### Community 227 - "Community 227"
Cohesion: 0.50
Nodes (1): create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea

### Community 228 - "Community 228"
Cohesion: 0.50
Nodes (1): add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf

### Community 229 - "Community 229"
Cohesion: 0.50
Nodes (1): add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c

### Community 230 - "Community 230"
Cohesion: 0.50
Nodes (1): add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create

### Community 231 - "Community 231"
Cohesion: 0.50
Nodes (1): add room follows  Revision ID: c9d0e1f2a3b4 Revises: b8c9d0e1f2a3 Create Date: 2

### Community 232 - "Community 232"
Cohesion: 0.50
Nodes (1): add_activity_coupon_campaign  Revision ID: f1a2b3c4d5e6 Revises: d0e1f2a3b4c5 Cr

### Community 233 - "Community 233"
Cohesion: 0.50
Nodes (1): create_schedule_HotCourseItem  Revision ID: fccf087f0f34 Revises: e3f4a5b6c7d8 C

### Community 234 - "Community 234"
Cohesion: 0.50
Nodes (1): create_course_table  Revision ID: c84abd1322d4 Revises: c4d5e6f7a8b9 Create Date

### Community 235 - "Community 235"
Cohesion: 0.50
Nodes (1): add teacher bio and student_count  Revision ID: e7f8a9b0c1d2 Revises: c84abd1322

### Community 236 - "Community 236"
Cohesion: 0.50
Nodes (1): add full_custom_price to courses  Revision ID: 5d8e53290b12 Revises: a1b2c3d4e5f

### Community 237 - "Community 237"
Cohesion: 0.50
Nodes (1): create course_schedules table and migrate fields from courses  Revision ID: b1c2

### Community 238 - "Community 238"
Cohesion: 0.67
Nodes (1): __APP_INFO__

### Community 239 - "Community 239"
Cohesion: 0.67
Nodes (1): WindowSizeOptions

### Community 241 - "Community 241"
Cohesion: 0.67
Nodes (1): Battery

### Community 242 - "Community 242"
Cohesion: 0.67
Nodes (2): CourseResponse, 将逗号分隔字符串解析为列表，None 或空字符串返回空列表

### Community 243 - "Community 243"
Cohesion: 0.67
Nodes (2): appThemeList, setting

### Community 250 - "Community 250"
Cohesion: 1.00
Nodes (1): BasicProps

### Community 252 - "Community 252"
Cohesion: 1.00
Nodes (1): directive

### Community 253 - "Community 253"
Cohesion: 1.00
Nodes (1): RoleEnum

### Community 259 - "Community 259"
Cohesion: 1.00
Nodes (1): animates

### Community 261 - "Community 261"
Cohesion: 1.00
Nodes (1): DynamicProps

### Community 263 - "Community 263"
Cohesion: 1.00
Nodes (1): params

## Knowledge Gaps
- **427 isolated node(s):** `Base exception for booking operations.`, `Create a booking with conflict detection.      Note: For MVP, conflict detection`, `List bookings for the current user with pagination.`, `Get a booking detail. Only own bookings are visible.`, `Cancel own paid future booking and refund the remaining amount to wallet.` (+422 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Booking Cancellation Tests`** (2 nodes): `routes`, `ParentLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (1 nodes): `WechatAuthService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (1 nodes): `admin_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `RBAC Service Layer`** (2 nodes): `_payload()`, `TestAdminTeacherApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (2 nodes): `admin_client()`, `unauth_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (1 nodes): `TestCreateBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher Management`** (1 nodes): `TestCancelBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (2 nodes): `Integration tests for file upload API endpoints.`, `TestUploadAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Data Model Tests`** (1 nodes): `AdminMenuService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Payment Service`** (1 nodes): `routes`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Admin Coupon Tests`** (1 nodes): `AdminSettingService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Seat Management Tests`** (2 nodes): `_payload()`, `TestAdminCouponApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Room & Seat Models`** (2 nodes): `HTMLParser`, `_RichTextSanitizer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (1 nodes): `AdminRoleService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `User Profile Tests`** (1 nodes): `TestSeatAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Deployment Config`** (1 nodes): `TestAvailableCouponsForBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Token Verification`** (1 nodes): `TestCourseModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Database Seed Data`** (2 nodes): `Integration tests for city APIs.`, `TestCityAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Wallet Service Layer`** (2 nodes): `Unit tests for the City model.`, `TestCityModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 210`** (2 nodes): `StudyRoom.room_type 字段验证。`, `TestStudyRoomRoomType`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 211`** (1 nodes): `TestTeacherModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 217`** (2 nodes): `setLoading()`, `useAsync()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 218`** (1 nodes): `key`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 219`** (1 nodes): `useCityStore`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 222`** (1 nodes): `create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 223`** (1 nodes): `create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 224`** (1 nodes): `create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 225`** (1 nodes): `create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 226`** (1 nodes): `booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 227`** (1 nodes): `create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 228`** (1 nodes): `add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (1 nodes): `add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 230`** (1 nodes): `add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 231`** (1 nodes): `add room follows  Revision ID: c9d0e1f2a3b4 Revises: b8c9d0e1f2a3 Create Date: 2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 232`** (1 nodes): `add_activity_coupon_campaign  Revision ID: f1a2b3c4d5e6 Revises: d0e1f2a3b4c5 Cr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 233`** (1 nodes): `create_schedule_HotCourseItem  Revision ID: fccf087f0f34 Revises: e3f4a5b6c7d8 C`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 234`** (1 nodes): `create_course_table  Revision ID: c84abd1322d4 Revises: c4d5e6f7a8b9 Create Date`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 235`** (1 nodes): `add teacher bio and student_count  Revision ID: e7f8a9b0c1d2 Revises: c84abd1322`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 236`** (1 nodes): `add full_custom_price to courses  Revision ID: 5d8e53290b12 Revises: a1b2c3d4e5f`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 237`** (1 nodes): `create course_schedules table and migrate fields from courses  Revision ID: b1c2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 238`** (1 nodes): `__APP_INFO__`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 239`** (1 nodes): `WindowSizeOptions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 241`** (1 nodes): `Battery`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 242`** (2 nodes): `CourseResponse`, `将逗号分隔字符串解析为列表，None 或空字符串返回空列表`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 243`** (2 nodes): `appThemeList`, `setting`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 250`** (1 nodes): `BasicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 252`** (1 nodes): `directive`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 253`** (1 nodes): `RoleEnum`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 259`** (1 nodes): `animates`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 261`** (1 nodes): `DynamicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 263`** (1 nodes): `params`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Auth Service Layer` to `Auth & Login Tests`, `Auth & Login Tests`, `Auth & Login Tests`, `Miscellaneous Module`, `Booking Cancellation Tests`, `Admin RBAC System`, `Room Management Tests`, `Auth & Login Tests`, `User Management`, `Token Verification`, `Booking Verification Tests`, `Auth & Login Tests`, `Miscellaneous Module`, `Miscellaneous Module`, `Data Models & Schemas`, `Booking Service Tests`, `Redis Connection`, `Payment & Wallet`, `Database Migrations`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `StudyRoom` connect `Wallet Service Tests` to `Auth & Login Tests`, `Booking Payment Tests`, `JWT Token Tests`, `Teacher Management Tests`, `Backend Service Layer`, `Booking Payment Tests`, `Auth & Login Tests`, `Database Config`, `Booking Payment Tests`, `RBAC Service Layer`, `Teacher Management`, `Booking Service Tests`, `Token Verification`, `Booking Payment Service`, `User Profile Tests`, `Auth & Login Tests`, `Deployment Config`, `Auth Service Layer`, `Teacher Management Tests`, `Auth & Login Tests`, `Integration Tests`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `Base` connect `JWT Token Tests` to `Miscellaneous Module`, `Token Verification`, `Auth & Login Tests`, `Auth & Login Tests`, `Booking Payment Tests`, `Teacher & Course Models`, `Teacher Management Tests`, `Booking Payment Tests`, `Coupon System`, `Wallet Service Tests`, `Payment & Wallet`, `Auth & WeChat Integration`, `Miscellaneous Module`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 244 inferred relationships involving `StudyRoom` (e.g. with `Base` and `City`) actually correct?**
  _`StudyRoom` has 244 INFERRED edges - model-reasoned connections that need verification._
- **Are the 212 inferred relationships involving `Settings` (e.g. with `AdminAuthService` and `AuthService`) actually correct?**
  _`Settings` has 212 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Base exception for booking operations.`, `Create a booking with conflict detection.      Note: For MVP, conflict detection`, `List bookings for the current user with pagination.` to the rest of the system?**
  _427 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Booking Service Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.04876926616057051 - nodes in this community are weakly interconnected._
# Graph Report - .  (2026-09-01)

## Corpus Check
- Large corpus: 1048 files · ~557,872 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 5674 nodes · 12444 edges · 223 communities detected
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 3042 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output
- Edge kinds: uses: 3042 · contains: 2819 · MODIFIES: 1336 · ON_BRANCH: 1304 · calls: 1101 · rationale_for: 785 · method: 699 · PARENT_OF: 432 · imports_from: 324 · inherits: 312 · imports: 283 · re_exports: 7


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 1048 · Candidates: 1510
- Excluded: 2 untracked · 89302 ignored · 0 sensitive · 24 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `1554905`
- Compare this hash to `git rev-parse HEAD` before trusting freshness-sensitive graph output.
## God Nodes (most connected - your core abstractions)
1. `StudyRoom` - 246 edges
2. `Settings` - 224 edges
3. `Booking` - 167 edges
4. `Course` - 165 edges
5. `Teacher` - 123 edges
6. `Seat` - 110 edges
7. `UserCoupon` - 99 edges
8. `CourseSchedule` - 97 edges
9. `Coupon` - 96 edges
10. `City` - 92 edges

## Surprising Connections (you probably didn't know these)
- `全套优惠：12 课时，price=80, full_package_price=860         → original_price=960（标准价）, d` --uses--> `CourseBookingService`  [INFERRED]
  br-server/tests/test_course_booking_service.py → br-server/app/services/course_booking_service.py
- `部分选择不触发全套优惠：10/12 课时         → original_price=800, discount_amount=0。` --uses--> `CourseBookingService`  [INFERRED]
  br-server/tests/test_course_booking_service.py → br-server/app/services/course_booking_service.py
- `full_package_price 高于标准价时，discount_amount 为 0。` --uses--> `CourseBookingService`  [INFERRED]
  br-server/tests/test_course_booking_service.py → br-server/app/services/course_booking_service.py
- `1V1 定制全套用 full_custom_price（而非 full_package_price），         基准单价用 custom_price。` --uses--> `CourseBookingService`  [INFERRED]
  br-server/tests/test_course_booking_service.py → br-server/app/services/course_booking_service.py
- `固定班课全套含免费试听课时：选择全部 12 课时（含 1 节试听），         计费课时 11，仍应触发全套优惠（回归订单 94 场景）。` --uses--> `CourseBookingService`  [INFERRED]
  br-server/tests/test_course_booking_service.py → br-server/app/services/course_booking_service.py

## Communities

### Community 0 - "Booking Service Tests"
Cohesion: 0.02
Nodes (132): AdminContext, City, Course, RoomFollow, TeacherRoom, Teacher, 删除老师。返回 "ok"；不存在返回 "not_found"；存在排课返回 "has_schedules"。, 按老师统计关联课程数（去重 course_id）。 (+124 more)

### Community 1 - "Teacher Management Tests"
Cohesion: 0.06
Nodes (132): feature/20260814/training-course-list, feature/20260817/course-booking, feature/20260817/course-detail-page, feature/20260817/teacher-profile-page, 008166a chore: Comet build→verify transition — all guard checks passed, 0191aac fix: redirect expired admin sessions to login, 061bda0 feat: 实现 seat-select 页面 viewMode 只读查看模式, 06c38d2 fix: 优化管理端钱包流水展示 (+124 more)

### Community 2 - "Booking Cancellation Tests"
Cohesion: 0.04
Nodes (93): Base, BookingCompletionInput, Activity, ActivityCoupon, Booking, Coupon, UserCoupon, Seat (+85 more)

### Community 3 - "Wallet Service Tests"
Cohesion: 0.03
Nodes (97): main, 00b5289 fix: 课程预约待开始订单取消时仅删除 custom 排课，fixed 固定班课排课保留, 020ddd3 debug: 延期功能前后端参数传递添加调试日志, 04f0a66 feat: 新增订单状态定时转换任务, 051c8b1 fix: 修复开课日期不显示和过期课时禁用逻辑 - 后端返回lesson_schedules数据, 0b33239 feat: 统计区域添加连续学习天数显示, 1017dbc revert: 回退后端list_bookings fallback条件改动，保留前端getLessonList处理, 101ff7f feat: 统一学习记录卡片布局 - 课程记录对齐座位记录样式 (+89 more)

### Community 4 - "Booking Payment Tests"
Cohesion: 0.03
Nodes (75): bind_wechat_phone(), bind_wechat_phone_by_sms(), get_me(), login(), logout(), Authenticate or create an app user with a WeChat mini program code., Bind a phone obtained from WeChat phone authorization code., Bind a phone to a WeChat user with SMS fallback verification. (+67 more)

### Community 5 - "Booking Payment Tests"
Cohesion: 0.03
Nodes (12): ae1887e merge: admin RBAC dynamic settings, c623596 feat: add admin RBAC dynamic settings, columns, upload_admin_image(), _upload_image(), upload_user_image(), setting, legacy_headers() (+4 more)

### Community 6 - "Token Verification"
Cohesion: 0.09
Nodes (81): 0148cfd feat: br-app课程相关页面仅展示固定班课排课 - training_service全部C端查询(培训室列表热门课程/培训室详情/课程列表/课程详情/相关课程)排课JOIN限定schedule_type=fixed - get_course_with_lessons(课程预约页)排课JOIN限定fixed并按创建时间取最早一条 - 定制课时排课记录不在C端课程页面展示，订单页面不受影响, 2365213 fix: 修复admin取消pending_confirm订单时MissingGreenlet错误 - 移除admin_cancel_booking中不必要的with_for_update()行锁 - WalletTransaction字段改为构造函数直接传参替代setattr, 3486c32 docs: bug-fixed.md 新增 BUG-26 Admin取消待确认订单MissingGreenlet错误, 408d499 fix: admin_confirm_booking统一使用admin_get_booking重新查询构建响应 - 与admin_cancel_booking相同模式避免flush后MissingGreenlet, 51f0f68 fix: 1V1定制订单开课日期改取bookings.date预约日期, 5ec9d70 feat: course_schedules新增schedule_type字段 + 1V1定制排课延迟到确认时创建 - Model: CourseSchedule新增schedule_type(fixed/custom)字段 - Migration: 添加schedule_type列(server_default=fixed) - create_course_booking: 1V1定制不再写入排课表，仅将用户选择的日期/时间段存入booking记录 - admin_confirm_booking: 确认1V1定制时才创建schedule_type=custom的排课记录和课时记录 - admin_confirm_booking: 查询固定班课开始日期时过滤schedule_type=fixed, 73e5b2a fix: 1V1定制订单time_slots保存为[{weekday,time_slot}]对象格式 + 确认时排课类型确认为custom - create_course_booking: booking.time_slots按排课表格式保存，weekday从所选开课日期推算 - _create_custom_schedule_on_confirm: 兼容旧字符串数组格式并补全weekday重建，排课记录schedule_type=custom - 存量数据已修正：bookings 77/78 及 course_schedules 25 的time_slots转为对象格式 - 端到端验证：创建待确认订单→确认→生成custom排课记录，time_slots格式与固定班课一致, 8bd8340 feat: 1V1私人定制待确认订单流程 + Admin订单列表UI改造 - 后端: 1V1定制创建时设为pending_confirm状态 - 后端: 新增admin确认API(根据时间变更为pending或confirmed) - 后端: pending_confirm订单取消支持全额退款 - 后端: admin列表返回user_nickname替代user_id - Admin: 状态文案更新(已确认→进行中/pending→待开始) - Admin: 新增待确认状态，确认/取消按钮 - Admin: 去掉已确认订单取消按钮，pending订单增加取消按钮 - App: pending_confirm订单显示在待开始TAB - App: 新增pending_confirm状态样式(橙色主题) (+73 more)

### Community 7 - "Room Management Tests"
Cohesion: 0.05
Nodes (74): admin_cancel_booking(), admin_confirm_booking(), admin_get_booking(), admin_list_bookings(), BookingAlreadyCancelledError, BookingCancellationNotAllowedError, BookingConflictError, BookingCouponUnavailableError (+66 more)

### Community 8 - "Teacher Management Tests"
Cohesion: 0.08
Nodes (71): CourseLesson, CourseSchedule, 课程排课表。      存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。     从 courses 表迁移出的字段：teacher_id, sc, WalletTransaction, 获取课程详情 + 课时列表 + 定价信息。, 获取课程详情，包含所有排课记录和教师信息。, BookingPaymentService, Service for booking WeChat payment creation and callbacks. (+63 more)

### Community 9 - "Booking Payment Tests"
Cohesion: 0.04
Nodes (28): CountTo, routes, routes, routes, routes, routes, routes, routes (+20 more)

### Community 10 - "Auth & Login Tests"
Cohesion: 0.04
Nodes (51): { apiUrl, urlPrefix }, mockAdapter, { useMock, loggerMock }, AdminPageResponse, toBasicTableResult(), ContentTypeEnum, RequestEnum, ResultEnum (+43 more)

### Community 11 - "Auth & Login Tests"
Cohesion: 0.04
Nodes (66): BaseModel, AdminCurrentResponse, AdminLoginRequest, AdminMessageResponse, AdminPasswordUpdate, AdminPermissionItem, AdminProfileUpdate, AdminTokenResponse (+58 more)

### Community 12 - "SMS & Captcha Tests"
Cohesion: 0.04
Nodes (56): dev, 0605022 fix: 课程编辑页与列表页在原 tab 内互相跳转，不再新开标签页, 0e90f58 fix: 排课更新后强制刷新列表数据, 0e940af feat(course): 所有课程页统一格式化上课时间并新增开课时间行, 107108e tweak: 课程上课时间统一格式化并在培训室详情显示（截断+悬停提示）, 182fcdd chore: checkoff Task 9 in plan, 1a07999 chore: archive admin-teacher-management, 1f81b4d feat: add roomType conditional API loading in detail.vue (+48 more)

### Community 13 - "Booking System Core"
Cohesion: 0.05
Nodes (54): AdminCouponItem, COURSE_CATEGORY_LABELS, COURSE_CATEGORY_OPTIONS, COURSE_STATUS_TAGS, buildActivityCouponFormItem(), buildActivitySearchSchemas(), buildActivityTableColumns(), buildBookingSearchSchemas() (+46 more)

### Community 14 - "Booking Data Models"
Cohesion: 0.04
Nodes (29): 0fc7746 chore: add teacher-profile-page OpenSpec artifacts and design doc, 206bd75 chore: check off Task 1 (models + migration) complete, 2323e70 feat: implement course detail API with TDD, 24f5ae5 tweak: 老师管理前端 — br-admin 老师列表/新增/编辑页（多选所属房间）+ br-app 教师简介页接入库表数据, 3437127 test(task-6): 课程详情+关注完整测试，实现 list course follows, 3590666 Merge branch 'feature/20260814/training-room-overview' into main, 4c94688 feat: 为 StudyRoom 添加 rating 列和 city 关系，含迁移, 4d1a7b8 fix: handle None seat in booking response to fix SeatBrief validation error (+21 more)

### Community 15 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (40): TransactionLike, Protocol, ActivityAdminResponse, ActivityCouponAdminResponse, ActivityCouponClaimResponse, ActivityCouponClaimUserCouponResponse, ActivityCouponInput, ActivityCouponPublicResponse (+32 more)

### Community 16 - "Teacher Management Tests"
Cohesion: 0.04
Nodes (14): 14c7316 Merge branch 'implement-wechat-quick-login-phone-binding' into main, 6daf2cb feat: add username profile settings, a8157af feat: add account security settings, b3ae959 feat: implement wechat quick login, Authentication business logic service., # TODO: implement invitation relationship logic, # TODO: integrate CaptchaService when captcha is enabled, JWT token utilities for authentication and token management. (+6 more)

### Community 17 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (45): BaseSettings, Raise a sanitized error if WeChat Pay cannot be used., Return missing mini program login settings without exposing values., Return missing mini program login settings without exposing values., Whether WeChat mini program login is enabled and configured., Whether WeChat mini program login is enabled and configured., Raise a sanitized error if WeChat mini program login cannot be used., Raise a sanitized error if WeChat mini program login cannot be used. (+37 more)

### Community 18 - "Auth Service Layer"
Cohesion: 0.05
Nodes (43): Base, get_db(), FastAPI dependency that provides an async database session., DeclarativeBase, Enum, PaymentMethod, PaymentStatus, 老师与培训室/综合室的多对多关联表。      room_id 仅允许关联 study_rooms 中 room_type 为 training 或 compr (+35 more)

### Community 19 - "Booking System Core"
Cohesion: 0.04
Nodes (31): Alova, BookingItem, BookingListParams, BookingListResult, ADMIN_NATIVE_META, AdminPageParams, BasicTableResult, compactQuery() (+23 more)

### Community 20 - "Room Management Tests"
Cohesion: 0.05
Nodes (12): 3ec39c1 fix: resolve undefined `actions` reference in booking list page, 6d4d4c1 docs: mark all order-admin-management tasks as completed, 6ffecfa Merge branch 'main' of github.com:sin668/booking-room into main, 8403348 refactor: extract admin page builders, d2114a6 merge: br-admin business refactor, eeafd80 Merge pull request #1 from sin668/worktree-order-admin-management, routes, routes (+4 more)

### Community 21 - "SMS & Captcha Tests"
Cohesion: 0.04
Nodes (11): 02a1920 fix: resolve menu icons, directory paths, and hidden menu filtering (BUG-19), 2f06520 merge: unified User-AdminUser model with user management CRUD, 9093d5e docs: archive merge-users-admin-users openspec and sync specs, c069a02 feat: unify user access control — remove user_type filtering from auth, legacy_headers(), test_role_crud_duplicate_and_assigned_delete_conflict(), test_role_menu_assignment_updates_auth_permissions(), merge_users_phase1_extend  Extend users table with admin-user fields and rename (+3 more)

### Community 22 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (34): PageEnum, DEFAULT_CONFIG, filter(), getConfig(), TreeHelperConfig, useAsyncRoute(), useAsyncRouteStore, ProjectSettingState (+26 more)

### Community 23 - "Database Config"
Cohesion: 0.07
Nodes (45): AliyunSMSProvider, SMS verification code service with rate-limiting., Aliyun Dysms API client for sending SMS verification codes., SMSService, mock_redis(), Unit tests for SMS service (extended coverage)., Second send within 60 s is rejected with 429., The 11th send in one day is rejected with 429. (+37 more)

### Community 24 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (27): result, TypeConsole, TypeOrderLarge, TypeSaleroom, TypeVisits, doCustomTimes(), pagination(), requestParams (+19 more)

### Community 25 - "JWT Token Tests"
Cohesion: 0.07
Nodes (23): Notification, NotificationPreference, NotificationType, NotificationNotFoundError, NotificationService, _preference_enabled(), _validate_type(), StrEnum (+15 more)

### Community 26 - "Auth & WeChat Integration"
Cohesion: 0.07
Nodes (32): AdminMenu, AdminRole, AdminAuthService, MenuSeed, Admin login with neither phone nor username returns 422., Admin login with phone (no username) returns 200., test_admin_login_missing_both_fields(), test_admin_login_with_phone() (+24 more)

### Community 27 - "Coupon System"
Cohesion: 0.08
Nodes (38): legacy_headers(), seed_users(), test_create_admin_user(), test_create_admin_user_requires_username(), test_create_app_user(), test_create_app_user_invalid_phone_format(), test_create_app_user_requires_phone(), test_create_duplicate_phone_returns_409() (+30 more)

### Community 28 - "Teacher Management"
Cohesion: 0.06
Nodes (23): mock_db(), _mock_keys_result(), _mock_scalar_result(), Unit tests for AuthService., Successful registration returns TokenResponse., Registering with an existing phone raises 409., Registering with invalid SMS code raises 400., When nickname is None, a default '学习者XXXXXX' nickname is generated. (+15 more)

### Community 29 - "Data Models & Schemas"
Cohesion: 0.05
Nodes (12): 7721d2b feat: 自习室新建/编辑改为页面跳转，列表新增城市/类型列与过滤，支持环境图片与上架状态, 7d4de92 chore: 房间管理模块文案「自习室」统一替换为「学习室」, routes, admin_get_room(), admin_list_rooms(), create_room(), delete_room(), get_study_room() (+4 more)

### Community 30 - "Miscellaneous Module"
Cohesion: 0.06
Nodes (28): CaptchaService, Aliyun Captcha 2.0 verification service., Verify a captcha token.          - If no ``ALIYUN_CAPTCHA_SCENE_ID`` is configur, Check whether a captcha token has already been consumed., _percent_encode(), Return a 6-digit random numeric string., Send a verification code to *phone*.          Workflow:         1. Validate capt, Verify an SMS code.          - If the code matches, the key is deleted (one-time (+20 more)

### Community 31 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (7): 7d72fbb test: add study record service and API tests, TestGetSummary, TestListRecords, _add_booking(), TestCalculateStreakDays, TestGetMonthlySummary, TestListStudyRecords

### Community 32 - "Auth & Login Tests"
Cohesion: 0.08
Nodes (28): _make_course(), _make_schedule(), full_package_price 为 None 时不触发优惠。, 全套优惠：12 课时，price=80, full_package_price=860         → original_price=960（标准价）, d, 部分选择不触发全套优惠：10/12 课时         → original_price=800, discount_amount=0。, full_package_price 高于标准价时，discount_amount 为 0。, 部分选择不触发全套优惠：10/12 课时         → original_price=800, discount_amount=0。, full_package_price 为 None 时不触发优惠。 (+20 more)

### Community 33 - "Auth & WeChat Integration"
Cohesion: 0.10
Nodes (20): change_password(), deactivate_account(), get_account_security(), get_me(), Get the current authenticated user's info., Update the current authenticated user's safe profile fields., Get current user's account security summary., Change current user's password after validating the old password. (+12 more)

### Community 34 - "Payment & Wallet"
Cohesion: 0.05
Nodes (12): df06846 Implement city selection frontend, e95d205 Archive city-selection-frontend OpenSpec change, ef18031 Archive wallet-recharge-frontend change and sync specs, useCityStore, CityResponse, get_active_cities(), Return active cities ordered by sort_order ascending., Integration tests for city APIs. (+4 more)

### Community 35 - "Booking Payment Tests"
Cohesion: 0.15
Nodes (26): Exception, WalletRepository, Service for booking WeChat payment creation and callbacks., InvalidPromoCodeError, OrderAlreadyProcessedError, OrderNotFoundError, PaymentSignatureError, Get user's current balance and total recharged amount. (+18 more)

### Community 36 - "Booking Domain Service"
Cohesion: 0.08
Nodes (15): AdminCourseService, 获取课程详情，包含所有排课记录和教师信息。, 延期某一课时及其后续所有课时。          逻辑：         1. 从 course_lessons 表获取课时列表         2. 解析 t, 延期某一课时及其后续所有课时。          延期逻辑（时间顺延）：         1. 第 N 讲的上课时间变为第 N+1 讲原来的上课时间, 从 lesson_schedule JSON 中计算 end_date（最后一个课时日期 + 1 天）。, 根据 start_date 和 time_slots 生成至少 needed 个可用时间槽位。          按日期+时间段排序，循环扩展周次直到生成足够槽, 将 CourseSchedule 模型转换为 CourseScheduleResponse。, 根据 start_date + time_slots + course_lessons 生成 lesson_schedules 记录。          如果 (+7 more)

### Community 37 - "Booking Service Tests"
Cohesion: 0.12
Nodes (35): ALIGNMENT_POSITIONS, appendBits(), applyMask(), bchRemainder(), bitLength(), chooseVersion(), cloneMatrix(), createCodewords() (+27 more)

### Community 38 - "Course Management"
Cohesion: 0.13
Nodes (24): HTMLParser, _activity_coupon_to_public_response(), _activity_to_admin_response(), _admin_coupon_to_response(), claim_activity_coupon(), claim_activity_coupon_response(), _count_user_claims(), _coupon_to_response() (+16 more)

### Community 39 - "Booking Cancellation Tests"
Cohesion: 0.06
Nodes (15): CourseCreateParams, CourseDetail, CourseItem, CourseListResult, CourseScheduleItem, CourseUpdateParams, LessonCreateParams, LessonItem (+7 more)

### Community 40 - "Miscellaneous Module"
Cohesion: 0.09
Nodes (19): BusinessSelectOption, useAdminBusiness(), useAdminBusinessStore, DesignSettingState, useDesignSetting(), useDesignSettingStore, setupCustomComponents(), setupGlobalMethods() (+11 more)

### Community 41 - "Coupon Service Layer"
Cohesion: 0.20
Nodes (27): _make_booking(), _make_coupon(), _make_course_booking(), _make_course_data(), _make_room(), _make_seat(), _make_user(), _make_user_coupon() (+19 more)

### Community 42 - "Teacher Management Tests"
Cohesion: 0.09
Nodes (15): 04745c9 chore: archive course-booking, 3af03bb fix: consolidate CORS and trailing-slash into single ASGI middleware, 45e5bef feat: extend Course and Booking models for course booking, 7180f81 fix: resolve alembic migration cycle by assigning unique revision ID e7f8a9b0c1d2, 85b99a1 feat: extend order list for course bookings and add course detail entry, ab174bc feat: add course booking API routes and extend booking list, b1018ae feat: add course booking page with full UI and payment flow, ba4f771 chore: mark all tasks complete in course-booking tasks.md (+7 more)

### Community 43 - "Booking Service Tests"
Cohesion: 0.11
Nodes (14): 2caef8e Merge pull request #2 from sin668/feat/booking-room-list-detail-fix, 4b89b76 update .gitignore, 549c0fa refactor br-app mobile UI, 7853710 refine: update tasks.md with precise file paths and codebase patterns, 794936b Add persisted study room follows, 887d314 refactor: share payment polling logic, 950b25d refactor: extract followed room service, a4aedb5 refactor: use shared app formatters (+6 more)

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
Cohesion: 0.09
Nodes (20): 3baaa8d feat: integrate WeChat wallet payments, b15c9d7 updated .gitignore, b610482 Archive wechat payment integration OpenSpec change, e07a2b2 feat: add wallet transactions frontend, ed78866 Implement wallet recharge flow, f93686c merge: wallet transactions frontend, AdminWalletStatisticsResponse, AdminWalletTransactionListResponse (+12 more)

### Community 48 - "Booking Domain Service"
Cohesion: 0.17
Nodes (22): _mock_scalar_one_result(), _mock_scalar_result(), _mock_scalars_result(), test_admin_get_statistics_aggregates_totals_and_active_users(), test_admin_list_transactions_joins_users_and_maps_user_fields(), test_confirm_payment_disabled_in_production(), test_create_recharge_order_rejects_unsupported_alipay(), test_create_wechat_recharge_order_returns_payment_params() (+14 more)

### Community 49 - "Auth Service Layer"
Cohesion: 0.12
Nodes (15): AppMiddleware, health_check(), Health check endpoint., _json_dumps(), _parse_response(), WeChat Pay API v3 client for JSAPI wallet recharges., Build mini program payment params for uni.requestPayment., Query an order by merchant out_trade_no. (+7 more)

### Community 50 - "Booking Cancellation Tests"
Cohesion: 0.13
Nodes (17): BookingPaymentAlreadyProcessedError, BookingPaymentError, BookingPaymentNotFoundError, BookingPaymentSignatureError, InvalidBookingPaymentCallbackError, Booking direct payment orchestration., Verify a WeChat callback and mark a booking payment as paid once., Verify a WeChat callback and mark a booking payment as paid once. (+9 more)

### Community 51 - "Booking Cancellation Tests"
Cohesion: 0.09
Nodes (9): 071ac5f chore: add implementation plan for training-room-overview, 0b53f3b 优化UI, 1ab6fd7 polish: refine training page TAB navigation for a more refined look, 53c230a chore: add implementation plan and design doc for course-detail-page, 836a7bb chore: archive training-room-overview change and sync delta specs to main specs, 8e4fbeb chore: archive training-room-overview change & add course-detail-page proposal, 9157d84 polish: align training course list UI with study room booking page, d84d0ce feat: 培训室概况页课程列表UI优化 - 后端: HotCourseItem 添加 schedule/tags 字段, TrainingRoomResponse 添加 rating - 后端: training_service 传递 schedule/tags 到热门课程 - 前端: training/index.vue 培训室名称可点击跳转到概况页 - 前端: 课程项添加时钟图标+培训时间+热销/新课/名师标签 - 前端: booking/detail.vue 课程列表同步优化UI样式 (+1 more)

### Community 52 - "User & Auth Models"
Cohesion: 0.13
Nodes (11): AdminAssignRoles, AdminResetPassword, AdminToggleStatus, AdminUserCreate, AdminUserDetail, AdminUserListItem, AdminUserListParams, AdminUserListResponse (+3 more)

### Community 53 - "Booking Payment Service"
Cohesion: 0.09
Nodes (13): ActivityCouponBase, ActivityCouponFormItem, ActivityCouponItem, ActivityCouponTemplate, ActivityFormParams, ActivityItem, ActivityListParams, ActivityListResult (+5 more)

### Community 54 - "Teacher Management Tests"
Cohesion: 0.08
Nodes (2): routes, ParentLayout()

### Community 55 - "Miscellaneous Module"
Cohesion: 0.40
Nodes (23): AdminCourseCreate, AdminCourseDetailResponse, AdminCourseItem, AdminCourseListResponse, AdminCourseUpdate, AdminLessonCreate, AdminLessonItem, AdminLessonUpdate (+15 more)

### Community 58 - "Coupon Service Layer"
Cohesion: 0.17
Nodes (19): _access_token(), _phone_user(), _temp_wechat_user(), test_bind_phone_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_sms_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_with_sms_to_new_phone(), test_bind_wechat_phone_code_to_new_phone(), test_bound_user_binding_unused_phone_returns_409() (+11 more)

### Community 59 - "Auth & Login Tests"
Cohesion: 0.09
Nodes (23): ChangeEvent, DeepPartial, Element, ElementAttributesProperty, ElementClass, Event, ImportMetaEnv, Indexable (+15 more)

### Community 60 - "Booking Service Tests"
Cohesion: 0.09
Nodes (15): copy, ElType, HTMLElement, debounce, ElType, HTMLElement, draggable, ElType (+7 more)

### Community 61 - "Teacher Management Tests"
Cohesion: 0.10
Nodes (8): useModal(), BasicProps, ModalMethods, ModalProps, RegisterFn, UseModalReturnType, isProdMode(), getDynamicProps()

### Community 62 - "Teacher Management Tests"
Cohesion: 0.21
Nodes (22): _booking_now(), _booking_timezone(), _build_booking_summary(), _build_verify_url(), confirm_verification(), _create_legacy_jwt_verification_token(), _create_verification_token(), _decode_compact_verification_token() (+14 more)

### Community 63 - "Miscellaneous Module"
Cohesion: 0.12
Nodes (7): 3302a91 feat: add coupon package booking flow, d14db83 Merge branch 'feature/coupon-package-frontend', d4aefe4 登录有效期调整为 3 天, auth_client(), other_auth_client(), seed_room_seat(), add_coupon_models  Revision ID: b3a7c9d2e4f1 Revises: 985785a787d8 Create Date:

### Community 65 - "Backend Service Layer"
Cohesion: 0.12
Nodes (14): _create_refresh_token(), _make_real_token_response(), Successful login returns 200 with TokenResponse., Login with username (no phone) returns 200., Login with neither phone nor username returns 422., Refresh with cookie token returns new TokenResponse., Refresh with body token (no cookie) returns new TokenResponse., Refresh with no token returns 401. (+6 more)

### Community 67 - "Booking Cancellation Tests"
Cohesion: 0.12
Nodes (11): 037946c feat: add study record frontend page, 155ef06 Ignore local worktrees, 1f38399 Merge branch 'worktree-learning-record-frontend-t5-7' into main, 3fdaf66 Update study record page and ignore agents file, 48d24c9 docs: archive learning record openspec change, 6e7ed1f feat: add study record API layer, 8a261c4 Refine booking verification implementation tasks, 9ba2419 fix: format month param as YYYY-MM string and fix pagination race (+3 more)

### Community 68 - "Booking Cancellation Tests"
Cohesion: 0.18
Nodes (19): AdminRoleSummary, AccountDeactivationResponse, AccountSecuritySummary, ChangePasswordRequest, ChangePasswordResponse, DeactivationRiskReason, IdentityVerificationRequest, IdentityVerificationResponse (+11 more)

### Community 69 - "Booking Payment Tests"
Cohesion: 0.10
Nodes (21): admin_cancel_booking(), admin_get_booking(), admin_list_bookings(), _build_admin_booking_response(), _cleanup_course_booking_schedule(), 删除订单专属排课记录及其课时记录。      仅删除定制排课（schedule_type='custom'）；固定班课（'fixed'）排课为课程共享资源，, Cancel any booking with the same refund settlement as user cancellation.      待开, List all bookings (admin view) with pagination and optional filters. (+13 more)

### Community 70 - "Miscellaneous Module"
Cohesion: 0.19
Nodes (1): WechatAuthService

### Community 71 - "User Security Tests"
Cohesion: 0.10
Nodes (13): API tests for current-user followed study rooms., GET without follow_type defaults to 'room'., GET with follow_type=course returns empty list (current phase)., GET with invalid follow_type returns 422., POST with follow_type=course validates against courses table., POST with invalid follow_type returns 422., DELETE with follow_type=course only deletes course follows., test_follow_room_with_course_type() (+5 more)

### Community 72 - "Booking Service Tests"
Cohesion: 0.14
Nodes (9): 89f0643 feat: load booking detail seat stats from backend, d4a1403 chore: archive wallet transactions frontend spec, admin_list_seats(), bulk_create_seats(), create_seat(), _get_booked_seat_ids(), get_seat_stats(), list_seats() (+1 more)

### Community 73 - "Course Management"
Cohesion: 0.15
Nodes (8): EditRecordRow, renderEditCell(), Instance, key, RetInstance, BasicColumn, BasicTableProps, TableActionType

### Community 74 - "Booking System Core"
Cohesion: 0.44
Nodes (19): ExpiredVerificationToken, InvalidVerificationToken, BookingVerificationBookingSummary, BookingVerificationConfirmResponse, BookingVerificationDetailResponse, BookingVerificationTokenRequest, BookingVerificationTokenResponse, VerifiableBookingListResponse (+11 more)

### Community 75 - "Token Verification"
Cohesion: 0.14
Nodes (17): AppMiddleware, _booking_payment_reconciliation_loop(), _cleanup_unpaid_bookings_job(), health_check(), lifespan(), _order_status_check_job(), _order_status_check_loop(), _parse_schedule_status_check_time() (+9 more)

### Community 76 - "Miscellaneous Module"
Cohesion: 0.28
Nodes (18): _calc_discount(), _calculate_hours(), _calculate_original_price(), _check_scope(), _ensure_aware(), _get_coupon_status(), _has_booking_history(), list_available_coupons_for_booking() (+10 more)

### Community 77 - "Auth & WeChat Integration"
Cohesion: 0.25
Nodes (17): AdminCouponListResponse, AdminCouponResponse, AdminCouponError, AdminCouponNotFoundError, _clean_coupon_data(), create_coupon(), delete_coupon(), _get_coupon_model() (+9 more)

### Community 78 - "Integration Tests"
Cohesion: 0.13
Nodes (14): applyWechatAppId(), DEFAULT_DEV_OUTPUT_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_SERVER_ENV_PATH, fs, parseEnvFile(), path, resolveOutputDirFromArgs() (+6 more)

### Community 79 - "Notification System"
Cohesion: 0.11
Nodes (10): Keyword search filters by title and description., Keyword search with no matches returns empty., Filter is_active=True returns only active activities., Filter is_active=False returns only inactive activities., Keyword and is_active filter combined., Empty DB returns zero total and empty items., Default pagination returns page 1 with all items., Custom page_size limits items per page. (+2 more)

### Community 80 - "Course Management"
Cohesion: 0.11
Nodes (1): admin_client()

### Community 81 - "Teacher & Course Models"
Cohesion: 0.11
Nodes (15): 培训课程相关 Schema 导入与功能测试  验证以下 schema 能正确导入和使用： - TeacherResponse, TeacherBrief, Ho, StudyRoomResponse 包含 room_type 字段, RoomCreate 包含 room_type 字段，默认值 study, RoomUpdate 包含 room_type 字段，默认 None, RoomAdminResponse 包含 room_type 字段, TeacherResponse 可正确导入并实例化, course.py 中所有 schema 可正确导入, CourseResponse.parse_tags 正确解析逗号分隔字符串 (+7 more)

### Community 82 - "Room & Seat Management"
Cohesion: 0.12
Nodes (3): 00cde52 Implement dynamic booking verification QR flow, 39024d3 fix: stabilize booking verification QR flow, 7143168 Archive personal QR OpenSpec change

### Community 83 - "RBAC Service Layer"
Cohesion: 0.12
Nodes (12): 1e48f73 fix: 老师详情接口容忍 qualifications 为 NULL（AdminTeacherDetail 校验失败 500）, be95476 feat: 老师新增/编辑页发布设置（是否激活）+ C 端老师列表过滤未激活 + 学习室编辑页行距统一, AdminTeacherCreate, AdminTeacherDetail, AdminTeacherListItem, AdminTeacherListResponse, AdminTeacherStatusUpdate, AdminTeacherUpdate (+4 more)

### Community 84 - "Booking Cancellation Tests"
Cohesion: 0.17
Nodes (10): useTimeoutFn(), useTimeoutRef(), screenEnum, screenMap, sizeEnum, CreateCallbackParams, useBreakpoint(), RemoveEventFn (+2 more)

### Community 85 - "Booking Verification Tests"
Cohesion: 0.16
Nodes (14): ClickOutside, DocumentHandler, FlushList, nodeList, addClass(), getBoundingClientRect(), getViewportOffset(), hasClass() (+6 more)

### Community 86 - "Booking Service Tests"
Cohesion: 0.18
Nodes (4): _coupon(), _seed_activity_coupon(), TestActivityCouponAPI, TestActivityCouponService

### Community 87 - "Booking Service Tests"
Cohesion: 0.19
Nodes (2): _payload(), TestAdminTeacherApi

### Community 89 - "Coupon System"
Cohesion: 0.12
Nodes (3): 7c70899 feat: add VIP membership and coupon admin, add_membership_level  Revision ID: df6ae550899a Revises: f1a2b3c4d5e6 Create Dat, add_wallet_membership_result  Revision ID: a2b3c4d5e6f7 Revises: df6ae550899a Cr

### Community 90 - "Database Config"
Cohesion: 0.18
Nodes (13): NamedTuple, admin_get_statistics(), admin_list_transactions(), _admin_wallet_base_conditions(), _now_for_coupon_db(), Wallet recharge and balance management service., Return a page of user-owned wallet transactions., 检测并执行 VIP 升级和赠券。返回 VipUpgradeResult。 (+5 more)

### Community 91 - "Room & Seat Management"
Cohesion: 0.12
Nodes (17): check_and_update_order_statuses(), _mark_completed_schedules(), _process_course_booking(), _process_seat_booking(), 处理培训课程预约订单      状态转换：     - pending + today >= 第一课时日期 → confirmed，高亮当前课时     - c, 处理培训课程预约订单      状态转换：     - pending + today >= 开课日期 → confirmed，高亮当前课时（开课日期统一取第一, 处理培训课程预约订单      状态转换：     - pending + today >= 第一课时日期 → confirmed，高亮当前课时     - c, 更新课时高亮      找到当前应该高亮的课时：当前日期所在课时，     即最后一个 lesson_date <= today 的课时（当前日期落在该课时的时 (+9 more)

### Community 92 - "Auth & Login Tests"
Cohesion: 0.12
Nodes (2): admin_client(), unauth_client()

### Community 93 - "Coupon System"
Cohesion: 0.12
Nodes (1): TestCreateBooking

### Community 94 - "Room & Seat Management"
Cohesion: 0.15
Nodes (7): COURSE_WEEKDAY_NAMES, formatAmount(), formatHourCount(), formatHourDuration(), formatMoney(), formatRoomMinPrice(), toFiniteNumber()

### Community 95 - "Room Management Tests"
Cohesion: 0.21
Nodes (16): del(), doRefreshToken(), get(), getRefreshToken(), getToken(), patch(), pendingRequests, post() (+8 more)

### Community 96 - "Database Seed Data"
Cohesion: 0.17
Nodes (11): 316d285 feat: add study record schemas, 5ce3f55 Merge branch 'worktree-learning-record-impl' into main, 83ccd35 feat: add study record backend (schema, service, routes), CalendarMark, StudyRecordItem, StudyRecordListResponse, StudyRecordSummaryResponse, _build_record_item() (+3 more)

### Community 97 - "Teacher Management"
Cohesion: 0.17
Nodes (10): Banner, list_active_banners(), Return all active banners ordered by sort_order ascending., Unit tests for banner_service module., Seed banners for tests., Only active banners are returned., Results are ordered by sort_order ascending., Empty DB returns empty list. (+2 more)

### Community 99 - "Teacher Management"
Cohesion: 0.14
Nodes (4): create_course(), get_course_detail(), Admin course management API routes., update_course()

### Community 101 - "Teacher & Course Models"
Cohesion: 0.24
Nodes (1): TestCancelBooking

### Community 102 - "Teacher Management Tests"
Cohesion: 0.13
Nodes (2): Integration tests for file upload API endpoints., TestUploadAPI

### Community 103 - "Data Model Tests"
Cohesion: 0.21
Nodes (14): _make_base_data(), _make_custom_booking(), 订单状态定时任务（课程订单）回归测试。  背景：同一课程下固定班课排课与定制排课可能引用相同 lesson_id（不同日期）， 旧代码按 course_id +, 到达开课日期后正常转为 confirmed 并高亮第一课时。, 到达开课日期后正常转为 confirmed 并高亮第一课时。, 开课日期口径：定制订单与固定班课一致，以第一课时日期为准而非 bookings.date。      bookings.date 早于第一课时日期时，未到首课时, 定制订单未到开课日期时不得被误转 confirmed（订单 98 事故回归）。      同课程固定班课排课含相同 lesson_id 且已开课，订单通过 sc, 定制订单未到开课日期时不得被误转 confirmed（订单 98 事故回归）。      同课程固定班课排课含相同 lesson_id 且已开课，订单通过 sc (+6 more)

### Community 105 - "Miscellaneous Module"
Cohesion: 0.27
Nodes (13): appRoot, assert, fs, loadModule(), main(), path, testAccountSecurity(), testAccountSecurityApi() (+5 more)

### Community 106 - "Room & Seat Management"
Cohesion: 0.30
Nodes (1): AdminMenuService

### Community 107 - "Auth & WeChat Integration"
Cohesion: 0.29
Nodes (13): _apply_menu_seed(), _ensure_role_menus(), _ensure_user_role(), _get_or_create_admin(), _get_or_create_app_role(), _get_or_create_menu(), _get_or_create_role(), main() (+5 more)

### Community 108 - "Integration Tests"
Cohesion: 0.26
Nodes (4): InvalidPaymentCallbackError, PaymentProviderUnavailableError, Verify a WeChat Pay callback and credit the wallet exactly once., WalletService

### Community 110 - "Room & Seat Service"
Cohesion: 0.15
Nodes (8): Unit tests for study_room_service module., Seed study rooms for tests., Only open rooms are returned., Pagination works correctly., Page size is capped at MAX_PAGE_SIZE (50)., Empty DB returns zero total and empty items., seed_study_rooms(), TestListStudyRooms

### Community 111 - "Miscellaneous Module"
Cohesion: 0.23
Nodes (3): _make_user(), TestProcessVipUpgrade, TestVIPScopeFilter

### Community 112 - "Teacher Management"
Cohesion: 0.24
Nodes (4): ComponentProps, componentMap, EventEnum, ComponentType

### Community 113 - "Auth & Login Tests"
Cohesion: 0.35
Nodes (2): SystemSetting, AdminSettingService

### Community 115 - "Auth & Login Tests"
Cohesion: 0.30
Nodes (10): _course_count_map(), create_teacher(), delete_teacher(), get_teacher_detail(), list_teachers(), _load_rooms_for_teachers(), _sync_teacher_rooms(), _tags_to_db() (+2 more)

### Community 116 - "Token Verification"
Cohesion: 0.27
Nodes (7): useGlobSetting(), useLocalSetting(), getAppEnvConfig(), getCommonStoragePrefix(), getEnv(), getStorageShortName(), warn()

### Community 119 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (9): _create_user(), test_change_password_rejects_bad_old_password_or_mismatch(), test_change_password_updates_hash_and_revokes_refresh_tokens(), test_deactivate_account_blocks_risks(), test_deactivate_account_sets_deleted_without_removing_user(), test_security_summary_masks_sensitive_fields(), test_security_summary_returns_deleted_unbound_unverified_state(), test_submit_identity_rejects_invalid_or_different_verified() (+1 more)

### Community 121 - "Wallet Service Layer"
Cohesion: 0.17
Nodes (1): TestAvailableCouponsForBooking

### Community 123 - "RBAC Service Layer"
Cohesion: 0.20
Nodes (9): get_current_admin(), get_current_admin_context(), get_current_user_id(), get_optional_current_user_id(), Shared API dependencies., Compatibility entrypoint for legacy admin route dependencies., Extract and validate the current user ID from the access token., 有登录凭证时解析用户 ID，无凭证时返回 None。 (+1 more)

### Community 124 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (10): 0072a7a 时区Bug fixed, 0f28968 Bug fixed, 5c47a3c archive coupon package frontend openspec change, c66da47 updated bug-fixed.md, _china_now_naive(), _get_or_create_demo_user(), seed_all(), seed_coupons() (+2 more)

### Community 125 - "Admin Coupon Tests"
Cohesion: 0.18
Nodes (4): AdminCouponCreateParams, AdminCouponListParams, AdminCouponListResult, AdminCouponUpdateParams

### Community 126 - "Admin Coupon Tests"
Cohesion: 0.29
Nodes (7): _build_wechat_client(), create_booking(), get_payment_status(), _notify_failure(), pay_pending_booking_route(), _payment_service(), wechat_notify()

### Community 127 - "Teacher Management Tests"
Cohesion: 0.35
Nodes (10): _build_wechat_client(), confirm_recharge(), create_recharge(), get_balance(), get_recharge_order(), list_transactions(), _notify_failure(), redeem_promo_code() (+2 more)

### Community 129 - "Teacher Management Tests"
Cohesion: 0.33
Nodes (3): _coupon_data(), _create_coupon(), TestAdminCouponService

### Community 130 - "Auth & Login Tests"
Cohesion: 0.22
Nodes (2): _payload(), TestAdminCouponApi

### Community 131 - "Token Verification"
Cohesion: 0.18
Nodes (6): Tests for the Seat model., Test that zone accepts valid values., Test that required fields are enforced., TestSeatDefaults, TestSeatRequiredFields, TestSeatZone

### Community 132 - "Miscellaneous Module"
Cohesion: 0.18
Nodes (6): TrainingRoomDetailResponse schema 测试, 验证嵌套 CourseResponse 的 tags 为 None 时解析为空列表, 验证缺少必填字段时抛出 ValidationError, 验证 teachers 和 courses 字段默认值为空列表, 验证嵌套的 CourseResponse 中 tags 字段可以正确解析逗号分隔字符串, TestTrainingRoomDetailResponse

### Community 133 - "HTML Sanitizer"
Cohesion: 0.18
Nodes (10): get_course_detail(), _get_first_schedule_for_courses(), get_training_room_detail(), list_courses(), list_training_rooms(), 返回培训室详情，包含课程列表和教师团队。      仅 room_type 为 training 或 comprehensive 的房间有效。, 返回分页课程列表，附带教室名和教师信息。      单条查询：JOIN StudyRoom + CourseSchedule + Teacher。, 返回课程详情，含教师、教室、课时和相关课程。      3 步查询，避免 N+1：     Step 1: courses + LEFT JOIN course (+2 more)

### Community 135 - "Miscellaneous Module"
Cohesion: 0.22
Nodes (7): 023eb00 feat: add GET /api/v1/training/rooms/{room_id} route, 2fe2097 feat: add get_training_room_detail to training_service (TDD green phase), 4150deb test: add failing tests for get_training_room_detail (TDD red phase), 7b04f07 chore: checkoff Task 3 in plan, 80e3f09 chore: checkoff Task 4 in plan, 9fd4cb8 test: add 8 training room detail API test scenarios (4.1-4.8), c0baf60 chore: checkoff Task 2 in plan

### Community 136 - "Room & Seat Models"
Cohesion: 0.20
Nodes (7): 02b3b93 feat: add course-detail page with all sections (7.1-7.8), 148395b feat(br-app): add course detail navigation from training list page, 38a606f chore: archive course-detail-page change, 7ff33ae Complete course-detail-page change, 84887cb fix: resolve Alembic migration revision ID conflict and fix inactive course test, c2f96bd fix: add course_lessons table to migration & align frontend field names, add_course_description_and_room_follow_type  Revision ID: c4d5e6f7a8b9 Revises:

### Community 138 - "Wallet Service Layer"
Cohesion: 0.27
Nodes (9): check_and_update_order_statuses(), _process_course_booking(), _process_seat_booking(), 订单状态定时转换服务  定时检查并更新所有已支付的待开始/进行中订单状态： - 自习室座位预约：pending → confirmed（当前时间 >= 开始时间, 处理培训课程预约订单      状态转换：     - pending + today >= 开课日期 → confirmed，高亮当前课时（1V1 定制订单开, 更新课时高亮      找到当前应该高亮的课时：当前日期所在课时，     即最后一个 lesson_date <= today 的课时（当前日期落在该课时的时, 定时检查并更新所有已支付的待开始/进行中订单状态。      返回: {"seat_started": N, "seat_completed": N, "cou, 处理自习室座位预约订单      状态转换：     - pending + now >= date+start_time → confirmed（进行中） (+1 more)

### Community 140 - "Booking Cancellation Tests"
Cohesion: 0.33
Nodes (1): AdminRoleService

### Community 141 - "User Profile Tests"
Cohesion: 0.20
Nodes (6): Query due pending WeChat bookings and advance their payment state., Query due pending WeChat bookings and advance their payment state., Query due pending WeChat bookings and advance their payment state., Create a WeChat JSAPI payment order for a pending booking., Create a WeChat JSAPI payment order for a pending booking., Create a WeChat JSAPI payment order for a pending booking.

### Community 143 - "Auth & Login Tests"
Cohesion: 0.20
Nodes (1): TestSeatAPI

### Community 144 - "Deployment Config"
Cohesion: 0.36
Nodes (8): _create_user(), test_get_current_user_profile_returns_username_fields(), test_update_nickname_does_not_require_username_cooldown(), test_update_profile_rejects_protected_fields(), test_update_username_rejects_cooldown(), test_update_username_rejects_duplicate(), test_update_username_rejects_invalid_format(), test_update_username_success_sets_cooldown_timestamp()

### Community 146 - "Project Documentation"
Cohesion: 0.20
Nodes (9): GlobConfig, GlobEnvConfig, IBodySetting, ICrumbsSetting, IHeaderSetting, IMenuSetting, IMultiTabsSetting, LocalConfig (+1 more)

### Community 147 - "Deployment Config"
Cohesion: 0.20
Nodes (9): ComponentElRef, ComponentRef, ElRef, EmitType, Fn, LabelValueOptions, PromiseFn, RefType (+1 more)

### Community 148 - "Miscellaneous Module"
Cohesion: 0.28
Nodes (3): adminRequest(), confirmVerification(), inspectVerificationToken()

### Community 151 - "Miscellaneous Module"
Cohesion: 0.25
Nodes (7): AdminMenuBase, AdminMenuCreate, AdminMenuNode, AdminMenuRoute, AdminMenuRouteMeta, AdminMenuUpdate, ComponentOption

### Community 152 - "RBAC Data Models"
Cohesion: 0.22
Nodes (8): exportMatch, fs, getCallMatch, paramMatch, path, source, trainingApiPath, urlMatch

### Community 153 - "Token Verification"
Cohesion: 0.39
Nodes (7): followRoom(), getFollowedRooms(), isRoomFollowed(), normalizeRoom(), setFollowedRooms(), syncFollowedRooms(), unfollowRoom()

### Community 154 - "Room & Seat Management"
Cohesion: 0.22
Nodes (4): BasicSettings, EmailSettings, nativeMeta, SystemSettings

### Community 155 - "JWT Token Tests"
Cohesion: 0.33
Nodes (5): 固定班课下单：预约日期/开课日期取已预约第一课时日期，时段复制排课记录。, 创建固定班课完整数据：教室/用户/课程/老师/排课/2 个课时及课时排课。, 第一课时在未来 → 待开始；预约日期=第一课时日期；时段复制排课；不改排课表。, 第一课时日期 <= 今天 → 进行中（confirmed）。, TestFixedBookingStartDateAndTimeSlots

### Community 156 - "Integration Tests"
Cohesion: 0.22
Nodes (5): get_current_user_id returns the user UUID from a valid access token., get_current_user_id raises 401 for a blacklisted token., get_current_user_id raises 401 when token type is not 'access'., get_current_user_id raises 401 for an expired token., TestGetCurrentUserId

### Community 157 - "Deployment Config"
Cohesion: 0.29
Nodes (6): Run migrations in 'offline' mode.      Configures the context with just a URL an, Run migrations in 'online' mode with async engine., Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online()

### Community 158 - "Database Migrations"
Cohesion: 0.39
Nodes (5): create_coupon(), delete_coupon(), _service_error(), toggle_coupon_status(), update_coupon()

### Community 159 - "Miscellaneous Module"
Cohesion: 0.36
Nodes (5): create_teacher(), get_teacher_detail(), Admin teacher management API routes., toggle_teacher_status(), update_teacher()

### Community 161 - "Miscellaneous Module"
Cohesion: 0.32
Nodes (3): list_notifications(), mark_all_notifications_read(), _parse_notification_type()

### Community 162 - "Coupon Service Layer"
Cohesion: 0.32
Nodes (6): assertContains(), assertMatches(), fs, path, read(), root

### Community 163 - "Room & Seat Management"
Cohesion: 0.29
Nodes (7): appRoot, assert, fs, loadModule(), main(), path, vm

### Community 164 - "Teacher Management"
Cohesion: 0.25
Nodes (7): failures, fs, path, profilePath, requiredLinks, source, statsCardMatch

### Community 165 - "User Management"
Cohesion: 0.46
Nodes (7): followCourse(), getFollowedCourses(), isCourseFollowed(), normalizeCourse(), setFollowedCourses(), syncFollowedCourses(), unfollowCourse()

### Community 168 - "Data Models & Schemas"
Cohesion: 0.43
Nodes (6): _policy(), test_exact_24_hours_charges_20_percent(), test_exact_2_hours_charges_50_percent(), test_exact_48_hours_charges_10_percent(), test_non_round_amount_keeps_penalty_and_refund_balanced(), test_over_48_hours_full_refund()

### Community 169 - "Room & Seat Models"
Cohesion: 0.25
Nodes (2): auth_client(), seed_teacher_follow_data()

### Community 174 - "Course Management"
Cohesion: 0.52
Nodes (5): createUploadError(), normalizeErrorMessage(), parseUploadResponse(), uploadImage(), uploadOnce()

### Community 175 - "Miscellaneous Module"
Cohesion: 0.33
Nodes (6): close_redis(), get_redis(), init_redis(), Initialize and return the singleton Redis connection., Close the Redis connection., FastAPI dependency that provides an async Redis connection.

### Community 177 - "Auth & Login Tests"
Cohesion: 0.57
Nodes (6): base64url_encode(), CompactVerificationPayload, create_compact_verification_token(), decode_compact_verification_token(), ensure_utc(), sign_compact_token()

### Community 178 - "Booking Cancellation Tests"
Cohesion: 0.52
Nodes (6): followTeacher(), getFollowedTeachers(), isTeacherFollowed(), normalizeTeacher(), setFollowedTeachers(), unfollowTeacher()

### Community 181 - "Booking System Core"
Cohesion: 0.29
Nodes (4): list_active_activities returns only is_active=True records., Results are ordered by sort_order ascending., Returns empty list when no activities exist., TestListActiveActivities

### Community 182 - "Notification System"
Cohesion: 0.29
Nodes (4): Tests for the Booking model., Test that required fields are enforced., TestBookingDefaults, TestBookingRequiredFields

### Community 183 - "Auth & WeChat Integration"
Cohesion: 0.29
Nodes (1): TestCourseModel

### Community 184 - "Payment & Wallet"
Cohesion: 0.29
Nodes (1): seed_teacher_data()

### Community 189 - "Activity Management"
Cohesion: 0.33
Nodes (4): Unit tests for activity_service module., Seed activities for pagination and filter tests., seed_activities(), TestDeleteActivity

### Community 192 - "Room & Seat Management"
Cohesion: 0.40
Nodes (5): _booking_payment_reconciliation_loop(), _cleanup_unpaid_bookings_job(), lifespan(), Fallback periodic runner for environments without APScheduler., Application lifespan: startup and shutdown events.

### Community 193 - "Teacher Management"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 195 - "Wallet Service Layer"
Cohesion: 0.60
Nodes (3): can_cancel_paid_booking(), has_booking_started(), should_mark_booking_completed()

### Community 196 - "Miscellaneous Module"
Cohesion: 0.50
Nodes (3): PermissionsEnum, ActionItem, PopConfirm

### Community 197 - "Miscellaneous Module"
Cohesion: 0.50
Nodes (2): _admin_wallet_base_conditions(), export_transactions()

### Community 198 - "Auth & Login Tests"
Cohesion: 0.60
Nodes (4): AvailableCouponForBookingResponse, AvailableCouponsForBookingListResponse, CouponBaseResponse, CouponResponse

### Community 199 - "Booking Service Tests"
Cohesion: 0.70
Nodes (4): booking_now(), booking_start_datetime(), calculate_cancellation_policy(), CancellationPolicyResult

### Community 200 - "Community 200"
Cohesion: 0.60
Nodes (3): createPaymentStatusError(), getPaymentStatus(), pollPaymentStatus()

### Community 201 - "Community 201"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 202 - "Community 202"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 203 - "Community 203"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 204 - "Community 204"
Cohesion: 0.40
Nodes (3): Returns activity when found., Returns None when not found., TestGetActivityById

### Community 205 - "Community 205"
Cohesion: 0.40
Nodes (3): Creates an activity and returns it with an ID., Creates activity with minimal data., TestCreateActivity

### Community 206 - "Community 206"
Cohesion: 0.40
Nodes (3): Updates activity fields., None values in update data are ignored., TestUpdateActivity

### Community 207 - "Community 207"
Cohesion: 0.40
Nodes (3): Toggles activity to inactive., Toggles activity to active., TestToggleActivityStatus

### Community 208 - "Community 208"
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
Cohesion: 0.83
Nodes (2): setLoading(), useAsync()

### Community 217 - "Community 217"
Cohesion: 0.50
Nodes (1): key

### Community 219 - "Community 219"
Cohesion: 0.50
Nodes (3): cleanup_unpaid_bookings(), Cleanup for unpaid booking payment holds., Cancel stale pending WeChat bookings and restore attached coupons.

### Community 220 - "Community 220"
Cohesion: 0.50
Nodes (3): check_and_update_schedule_statuses(), 排课状态定时任务  定时扫描课程排课列表中状态为"进行中"（in_progress）的排课记录： - 当前日期 > 课程结束日期（end_date）→ sche, 定时扫描"进行中"的排课记录，将当前日期已超过结课日期的记录标记为已完成。      返回: {"total_scanned": N, "schedule_co

### Community 222 - "Community 222"
Cohesion: 0.50
Nodes (1): TestAdminAuth

### Community 224 - "Community 224"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17

### Community 225 - "Community 225"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:

### Community 226 - "Community 226"
Cohesion: 0.50
Nodes (1): create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create

### Community 227 - "Community 227"
Cohesion: 0.50
Nodes (1): create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat

### Community 228 - "Community 228"
Cohesion: 0.50
Nodes (1): booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:

### Community 229 - "Community 229"
Cohesion: 0.50
Nodes (1): create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea

### Community 230 - "Community 230"
Cohesion: 0.50
Nodes (1): create_wallet_table  Revision ID: 28a1f4af90df Revises: b3a7c9d2e4f1 Create Date

### Community 231 - "Community 231"
Cohesion: 0.50
Nodes (1): update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:

### Community 232 - "Community 232"
Cohesion: 0.50
Nodes (1): add_wechat_payment_fields  Revision ID: a8c3f1b2d4e5 Revises: 7c9d2e4f6a1b Creat

### Community 233 - "Community 233"
Cohesion: 0.50
Nodes (1): add_booking_payment_fields  Adds payment-related fields to bookings table: - pay

### Community 234 - "Community 234"
Cohesion: 0.50
Nodes (1): add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c

### Community 235 - "Community 235"
Cohesion: 0.50
Nodes (1): add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create

### Community 236 - "Community 236"
Cohesion: 0.50
Nodes (1): add booking cancellation audit fields  Revision ID: b8c9d0e1f2a3 Revises: a7b8c9

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
Nodes (1): extend teachers table and create teacher_rooms  Revision ID: d3e4f5a6b7c8 Revise

### Community 245 - "Community 245"
Cohesion: 0.50
Nodes (1): add time_slots and teacher_id to bookings  Revision ID: b9c0d1e2f3a4 Revises: e8

### Community 246 - "Community 246"
Cohesion: 0.50
Nodes (1): add_schedule_status_to_course_schedules  Revision ID: d4e5f6a7b8c9 Revises: b9c0

### Community 247 - "Community 247"
Cohesion: 0.50
Nodes (1): add_schedule_id_to_bookings  Revision ID: e5f6a7b8c9d0 Revises: d4e5f6a7b8c9 Cre

### Community 248 - "Community 248"
Cohesion: 0.67
Nodes (1): __APP_INFO__

### Community 249 - "Community 249"
Cohesion: 0.67
Nodes (2): PAYMENT_TERMINAL_FAILURE_STATUSES, WALLET_TRANSACTION_STATUS_LABELS

### Community 250 - "Community 250"
Cohesion: 0.67
Nodes (1): WindowSizeOptions

### Community 252 - "Community 252"
Cohesion: 0.67
Nodes (1): Battery

### Community 253 - "Community 253"
Cohesion: 0.67
Nodes (2): CourseResponse, 将逗号分隔字符串解析为列表，None 或空字符串返回空列表

### Community 254 - "Community 254"
Cohesion: 0.67
Nodes (1): TeacherDetailResponse

### Community 257 - "Community 257"
Cohesion: 0.67
Nodes (1): Tests for admin wallet API routes.

### Community 258 - "Community 258"
Cohesion: 0.67
Nodes (1): TestStudyRoomAPI

### Community 263 - "Community 263"
Cohesion: 1.00
Nodes (1): BookingUseCases

### Community 264 - "Community 264"
Cohesion: 1.00
Nodes (1): Application use case orchestration layer.

### Community 265 - "Community 265"
Cohesion: 1.00
Nodes (1): BasicProps

### Community 266 - "Community 266"
Cohesion: 1.00
Nodes (1): websiteConfig

### Community 268 - "Community 268"
Cohesion: 1.00
Nodes (1): directive

### Community 269 - "Community 269"
Cohesion: 1.00
Nodes (1): RoleEnum

### Community 274 - "Community 274"
Cohesion: 1.00
Nodes (1): Database repository adapters.

### Community 276 - "Community 276"
Cohesion: 1.00
Nodes (1): animates

### Community 278 - "Community 278"
Cohesion: 1.00
Nodes (1): Page beyond total items adjusts offset to last valid page.

### Community 282 - "Community 282"
Cohesion: 1.00
Nodes (1): DynamicProps

### Community 284 - "Community 284"
Cohesion: 1.00
Nodes (1): params

## Knowledge Gaps
- **505 isolated node(s):** `Base exception for booking payment operations.`, `Service for booking WeChat payment creation and callbacks.`, `Create a WeChat JSAPI payment order for a pending booking.`, `Verify a WeChat callback and mark a booking payment as paid once.`, `Query due pending WeChat bookings and advance their payment state.` (+500 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Teacher Management Tests`** (2 nodes): `routes`, `ParentLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (1 nodes): `WechatAuthService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Course Management`** (1 nodes): `admin_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (2 nodes): `_payload()`, `TestAdminTeacherApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth & Login Tests`** (2 nodes): `admin_client()`, `unauth_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coupon System`** (1 nodes): `TestCreateBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher & Course Models`** (1 nodes): `TestCancelBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher Management Tests`** (2 nodes): `Integration tests for file upload API endpoints.`, `TestUploadAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Room & Seat Management`** (1 nodes): `AdminMenuService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth & Login Tests`** (2 nodes): `SystemSetting`, `AdminSettingService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Wallet Service Layer`** (1 nodes): `TestAvailableCouponsForBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth & Login Tests`** (2 nodes): `_payload()`, `TestAdminCouponApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Cancellation Tests`** (1 nodes): `AdminRoleService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth & Login Tests`** (1 nodes): `TestSeatAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Room & Seat Models`** (2 nodes): `auth_client()`, `seed_teacher_follow_data()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth & WeChat Integration`** (1 nodes): `TestCourseModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Payment & Wallet`** (1 nodes): `seed_teacher_data()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (2 nodes): `_admin_wallet_base_conditions()`, `export_transactions()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 210`** (2 nodes): `StudyRoom.room_type 字段验证。`, `TestStudyRoomRoomType`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 211`** (1 nodes): `TestTeacherModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 216`** (2 nodes): `setLoading()`, `useAsync()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 217`** (1 nodes): `key`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 222`** (1 nodes): `TestAdminAuth`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 224`** (1 nodes): `create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 225`** (1 nodes): `create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 226`** (1 nodes): `create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 227`** (1 nodes): `create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 228`** (1 nodes): `booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (1 nodes): `create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 230`** (1 nodes): `create_wallet_table  Revision ID: 28a1f4af90df Revises: b3a7c9d2e4f1 Create Date`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 231`** (1 nodes): `update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 232`** (1 nodes): `add_wechat_payment_fields  Revision ID: a8c3f1b2d4e5 Revises: 7c9d2e4f6a1b Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 233`** (1 nodes): `add_booking_payment_fields  Adds payment-related fields to bookings table: - pay`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 234`** (1 nodes): `add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 235`** (1 nodes): `add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 236`** (1 nodes): `add booking cancellation audit fields  Revision ID: b8c9d0e1f2a3 Revises: a7b8c9`
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
- **Thin community `Community 244`** (1 nodes): `extend teachers table and create teacher_rooms  Revision ID: d3e4f5a6b7c8 Revise`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 245`** (1 nodes): `add time_slots and teacher_id to bookings  Revision ID: b9c0d1e2f3a4 Revises: e8`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 246`** (1 nodes): `add_schedule_status_to_course_schedules  Revision ID: d4e5f6a7b8c9 Revises: b9c0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 247`** (1 nodes): `add_schedule_id_to_bookings  Revision ID: e5f6a7b8c9d0 Revises: d4e5f6a7b8c9 Cre`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 248`** (1 nodes): `__APP_INFO__`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 249`** (2 nodes): `PAYMENT_TERMINAL_FAILURE_STATUSES`, `WALLET_TRANSACTION_STATUS_LABELS`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 250`** (1 nodes): `WindowSizeOptions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 252`** (1 nodes): `Battery`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 253`** (2 nodes): `CourseResponse`, `将逗号分隔字符串解析为列表，None 或空字符串返回空列表`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 254`** (1 nodes): `TeacherDetailResponse`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 257`** (1 nodes): `Tests for admin wallet API routes.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 258`** (1 nodes): `TestStudyRoomAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 263`** (1 nodes): `BookingUseCases`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 264`** (1 nodes): `Application use case orchestration layer.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 265`** (1 nodes): `BasicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 266`** (1 nodes): `websiteConfig`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 268`** (1 nodes): `directive`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 269`** (1 nodes): `RoleEnum`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 274`** (1 nodes): `Database repository adapters.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 276`** (1 nodes): `animates`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 278`** (1 nodes): `Page beyond total items adjusts offset to last valid page.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 282`** (1 nodes): `DynamicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 284`** (1 nodes): `params`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Auth & Login Tests` to `Wallet Service Tests`, `Auth & WeChat Integration`, `Booking Payment Tests`, `Teacher Management Tests`, `Miscellaneous Module`, `Database Config`, `Auth & Login Tests`, `Booking Cancellation Tests`, `Auth & WeChat Integration`, `Integration Tests`, `Booking Payment Tests`, `Database Config`, `Miscellaneous Module`, `Auth Service Layer`, `Booking Cancellation Tests`, `Teacher Management`, `Integration Tests`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `StudyRoom` connect `Booking Cancellation Tests` to `Booking Data Models`, `Auth Service Layer`, `Booking Service Tests`, `Booking Domain Service`, `Miscellaneous Module`, `Teacher Management Tests`, `Booking Cancellation Tests`, `User Profile Tests`, `Booking Payment Tests`, `Token Verification`, `Booking System Core`, `Community 222`, `Booking Service Tests`, `Teacher & Course Models`, `Coupon System`, `Booking Service Tests`, `Community 258`, `User Security Tests`, `Auth & Login Tests`, `Auth & Login Tests`, `Wallet Service Layer`, `Auth & Login Tests`, `Room & Seat Service`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `Booking` connect `Booking Cancellation Tests` to `Teacher Management Tests`, `Booking Cancellation Tests`, `Teacher Management Tests`, `User Profile Tests`, `Token Verification`, `Booking Payment Tests`, `Room & Seat Management`, `Auth Service Layer`, `User & Auth Models`, `Community 219`, `Booking Payment Tests`, `Booking System Core`, `Auth & WeChat Integration`, `Auth & Login Tests`, `Miscellaneous Module`, `Community 222`, `Teacher & Course Models`, `Coupon System`, `Auth & Login Tests`, `Auth & Login Tests`, `Notification System`, `Wallet Service Layer`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 244 inferred relationships involving `StudyRoom` (e.g. with `Base` and `City`) actually correct?**
  _`StudyRoom` has 244 INFERRED edges - model-reasoned connections that need verification._
- **Are the 212 inferred relationships involving `Settings` (e.g. with `AdminAuthService` and `AuthService`) actually correct?**
  _`Settings` has 212 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Base exception for booking payment operations.`, `Service for booking WeChat payment creation and callbacks.`, `Create a WeChat JSAPI payment order for a pending booking.` to the rest of the system?**
  _505 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Booking Service Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.016224785805842273 - nodes in this community are weakly interconnected._
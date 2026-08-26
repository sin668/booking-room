# Graph Report - .  (2026-08-26)

## Corpus Check
- Large corpus: 1023 files · ~507,552 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 5182 nodes · 10787 edges · 214 communities detected
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 2485 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output
- Edge kinds: contains: 2694 · uses: 2485 · MODIFIES: 1177 · ON_BRANCH: 1009 · calls: 954 · method: 676 · rationale_for: 546 · PARENT_OF: 337 · imports_from: 324 · inherits: 295 · imports: 283 · re_exports: 7


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 1023 · Candidates: 1431
- Excluded: 0 untracked · 89219 ignored · 0 sensitive · 24 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `74d09c0`
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
- `课程排课表。      存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。     从 courses 表迁移出的字段：teacher_id, sc` --uses--> `Base`  [INFERRED]
  br-server/app/models/course_schedule.py → br-server/app/core/database.py
- `老师与培训室/综合室的多对多关联表。      room_id 仅允许关联 study_rooms 中 room_type 为 training 或 compr` --uses--> `Base`  [INFERRED]
  br-server/app/models/teacher_room.py → br-server/app/core/database.py
- `Admin course management API routes.` --uses--> `AdminCourseService`  [INFERRED]
  br-server/app/api/routes/admin_course.py → br-server/app/services/admin_course_service.py
- `Return whichever contact field (phone/username) was provided.` --uses--> `AdminRoleSummary`  [INFERRED]
  br-server/app/schemas/admin_user_management.py → br-server/app/schemas/admin_auth.py
- `Cleanup for unpaid booking payment holds.` --uses--> `Booking`  [INFERRED]
  br-server/app/services/booking_cleanup_service.py → br-server/app/models/booking.py

## Communities

### Community 0 - "Booking Service Tests"
Cohesion: 0.05
Nodes (92): feature/20260817/course-booking, feature/20260817/course-detail-page, feature/20260817/teacher-profile-page, 0191aac fix: redirect expired admin sessions to login, 023eb00 feat: add GET /api/v1/training/rooms/{room_id} route, 061bda0 feat: 实现 seat-select 页面 viewMode 只读查看模式, 071ac5f chore: add implementation plan for training-room-overview, 0b53f3b 优化UI (+84 more)

### Community 1 - "Teacher Management Tests"
Cohesion: 0.04
Nodes (69): Booking, Seat, StudyRoom, PaymentProviderUnavailableError, 统一校验卡券适用范围。座位区域由预约查询携带 seat 后单独判断。, Return set of seat_ids that have overlapping confirmed bookings., Seed seat data for existing study rooms., Generate seats for a study room. Returns number of seats created. (+61 more)

### Community 2 - "Booking Cancellation Tests"
Cohesion: 0.04
Nodes (48): 0719233 fix: reconcile pending wechat bookings, 074aeae feat: add message notification APIs and app UI, 0e940af feat(course): 所有课程页统一格式化上课时间并新增开课时间行, 3252e57 实现预约取消退款, 3302a91 feat: add coupon package booking flow, 549c0fa refactor br-app mobile UI, 59abe7a fixed orders: 显示X课时, 6288c60 feat: add booking wechat payment flow (+40 more)

### Community 3 - "Wallet Service Tests"
Cohesion: 0.03
Nodes (50): City, get_active_cities(), Return active cities ordered by sort_order ascending., 测试 CourseDetailResponse / RoomBrief / RelatedCourseItem Schema。, RoomBrief cover_image 可选。, RelatedCourseItem 可正常创建。, CourseDetailResponse 完整创建。, TestCourseDetailSchemas (+42 more)

### Community 4 - "Booking Payment Tests"
Cohesion: 0.03
Nodes (72): BaseModel, AdminCurrentResponse, AdminLoginRequest, AdminMessageResponse, AdminPasswordUpdate, AdminPermissionItem, AdminProfileUpdate, AdminTokenResponse (+64 more)

### Community 5 - "Booking Payment Tests"
Cohesion: 0.10
Nodes (74): Base, BookingCompletionInput, CourseLesson, CourseSchedule, 课程排课表。      存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。     从 courses 表迁移出的字段：teacher_id, sc, 老师与培训室/综合室的多对多关联表。      room_id 仅允许关联 study_rooms 中 room_type 为 training 或 compr, TeacherRoom, Teacher (+66 more)

### Community 6 - "Token Verification"
Cohesion: 0.04
Nodes (54): Activity, ActivityCoupon, Coupon, UserCoupon, ActivityCouponClaimError, ActivityCouponClaimResult, ActivityCouponError, ActivityCouponPublishError (+46 more)

### Community 7 - "Room Management Tests"
Cohesion: 0.03
Nodes (11): get_current_admin(), Shared API dependencies., Compatibility entrypoint for legacy admin route dependencies., ae1887e merge: admin RBAC dynamic settings, c623596 feat: add admin RBAC dynamic settings, columns, upload_admin_image(), _upload_image() (+3 more)

### Community 8 - "Teacher Management Tests"
Cohesion: 0.04
Nodes (55): AdminContext, Course, RoomFollow, 管理端老师管理 API 测试。  覆盖：列表分页/筛选、详情、新增、编辑、删除（含排课拒绝）、状态切换、 room_type 校验、权限控制。, 发布设置：新增时可指定 status，编辑时可通过 PUT 修改 status。, C 端培训室详情的教师团队与课程讲师过滤未激活老师。, qualifications/teaching_tags 为空时入库为 NULL，详情接口应返回 200 且容忍为空列表。, API tests for current-user followed study rooms. (+47 more)

### Community 9 - "Booking Payment Tests"
Cohesion: 0.10
Nodes (53): Exception, WalletRepository, Booking direct payment orchestration., Verify a WeChat callback and mark a booking payment as paid once., Query due pending WeChat bookings and advance their payment state., Base exception for booking payment operations., Service for booking WeChat payment creation and callbacks., Create a WeChat JSAPI payment order for a pending booking. (+45 more)

### Community 10 - "Auth & Login Tests"
Cohesion: 0.04
Nodes (41): 14c7316 Merge branch 'implement-wechat-quick-login-phone-binding' into main, 6daf2cb feat: add username profile settings, a8157af feat: add account security settings, b3ae959 feat: implement wechat quick login, d4aefe4 登录有效期调整为 3 天, change_password(), deactivate_account(), get_account_security() (+33 more)

### Community 11 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (27): routes, routes, routes, routes, routes, routes, routes, routes (+19 more)

### Community 12 - "SMS & Captcha Tests"
Cohesion: 0.03
Nodes (23): 02a1920 fix: resolve menu icons, directory paths, and hidden menu filtering (BUG-19), 2f06520 merge: unified User-AdminUser model with user management CRUD, 9093d5e docs: archive merge-users-admin-users openspec and sync specs, c069a02 feat: unify user access control — remove user_type filtering from auth, client_with_user(), Integration tests for auth API endpoints., Create a client with get_current_user_id overridden to return FIXED_USER_ID., Test creating app user defaults user_type to 'app (+15 more)

### Community 13 - "Booking System Core"
Cohesion: 0.06
Nodes (46): AdminCouponItem, buildActivityCouponFormItem(), buildActivitySearchSchemas(), buildActivityTableColumns(), buildBookingSearchSchemas(), buildBookingTableColumns(), buildRoomSearchSchemas(), buildRoomTableColumns() (+38 more)

### Community 14 - "Booking Data Models"
Cohesion: 0.05
Nodes (47): feature/20260814/training-course-list, 037946c feat: add study record frontend page, 155ef06 Ignore local worktrees, 1f38399 Merge branch 'worktree-learning-record-frontend-t5-7' into main, 206bd75 chore: check off Task 1 (models + migration) complete, 342d280 fix(wallet): count only completed recharges in admin stats, 3a853fd docs: archive order payment wechat change, 3e4b38d docs: archive account security settings spec (+39 more)

### Community 15 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (59): main, 008166a chore: Comet build→verify transition — all guard checks passed, 04745c9 chore: archive course-booking, 10b5060 feat: add training course list page, 196e3db refactor: add admin business schema builders, 1a07999 chore: archive admin-teacher-management, 1e48f73 fix: 老师详情接口容忍 qualifications 为 NULL（AdminTeacherDetail 校验失败 500）, 21d2e4f feat(training): 排课时间段支持自定义新增 + 课程目录布局对齐优化 (+51 more)

### Community 16 - "Teacher Management Tests"
Cohesion: 0.08
Nodes (37): bind_wechat_phone(), bind_wechat_phone_by_sms(), get_me(), login(), logout(), Authenticate or create an app user with a WeChat mini program code., Bind a phone obtained from WeChat phone authorization code., Bind a phone to a WeChat user with SMS fallback verification. (+29 more)

### Community 17 - "Auth & Login Tests"
Cohesion: 0.07
Nodes (39): BaseSettings, Return missing mini program login settings without exposing values., Whether WeChat mini program login is enabled and configured., Raise a sanitized error if WeChat mini program login cannot be used., Return the normalized upload storage driver., Return missing OSS setting names without exposing configured values., Raise a sanitized error if upload storage cannot be used., Application settings loaded from environment variables and .env file. (+31 more)

### Community 18 - "Auth Service Layer"
Cohesion: 0.05
Nodes (28): Alova, result, TypeConsole, TypeOrderLarge, TypeSaleroom, TypeVisits, doCustomTimes(), pagination() (+20 more)

### Community 19 - "Booking System Core"
Cohesion: 0.04
Nodes (15): 287a7dd feat: 活动新建/编辑改为页面跳转，样式布局对齐课程编辑页, 7721d2b feat: 自习室新建/编辑改为页面跳转，列表新增城市/类型列与过滤，支持环境图片与上架状态, 7d4de92 chore: 房间管理模块文案「自习室」统一替换为「学习室」, 96611a0 chore: archive course-schedule-time-display, a4a1e8a fix: 排课删除出现成功+失败双提示 & 授课老师改为必选, routes, admin_get_room(), admin_list_rooms() (+7 more)

### Community 20 - "Room Management Tests"
Cohesion: 0.06
Nodes (43): AliyunSMSProvider, Aliyun Dysms API client for sending SMS verification codes., mock_redis(), Unit tests for SMS service (extended coverage)., Second send within 60 s is rejected with 429., The 11th send in one day is rejected with 429., Return a mock async Redis client., Invalid captcha token returns 400. (+35 more)

### Community 21 - "SMS & Captcha Tests"
Cohesion: 0.06
Nodes (39): Run migrations in 'offline' mode.      Configures the context with just a URL an, Run migrations in 'online' mode with async engine., Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online(), Base, get_db() (+31 more)

### Community 22 - "Auth & Login Tests"
Cohesion: 0.14
Nodes (47): base64url_encode(), CompactVerificationPayload, create_compact_verification_token(), decode_compact_verification_token(), ensure_utc(), ExpiredVerificationToken, InvalidVerificationToken, sign_compact_token() (+39 more)

### Community 23 - "Database Config"
Cohesion: 0.06
Nodes (13): be95476 feat: 老师新增/编辑页发布设置（是否激活）+ C 端老师列表过滤未激活 + 学习室编辑页行距统一, _course_count_map(), create_teacher(), delete_teacher(), get_teacher_detail(), list_teachers(), _load_rooms_for_teachers(), _sync_teacher_rooms() (+5 more)

### Community 24 - "Auth & Login Tests"
Cohesion: 0.07
Nodes (23): Notification, NotificationPreference, NotificationType, NotificationNotFoundError, NotificationService, _preference_enabled(), _validate_type(), StrEnum (+15 more)

### Community 25 - "JWT Token Tests"
Cohesion: 0.06
Nodes (32): ADMIN_NATIVE_META, AdminPageParams, AdminPageResponse, BasicTableResult, compactQuery(), normalizePageParams(), toBasicTableResult(), AdminLoginParams (+24 more)

### Community 26 - "Auth & WeChat Integration"
Cohesion: 0.06
Nodes (23): mock_db(), _mock_keys_result(), _mock_scalar_result(), Unit tests for AuthService., Successful registration returns TokenResponse., Registering with an existing phone raises 409., Registering with invalid SMS code raises 400., When nickname is None, a default '学习者XXXXXX' nickname is generated. (+15 more)

### Community 27 - "Coupon System"
Cohesion: 0.07
Nodes (29): get_current_admin_context(), get_current_user_id(), get_optional_current_user_id(), Extract and validate the current user ID from the access token., 有登录凭证时解析用户 ID，无凭证时返回 None。, Resolve the current administrator from Bearer or legacy admin token., AdminMenu, AdminRole (+21 more)

### Community 28 - "Teacher Management"
Cohesion: 0.06
Nodes (29): CaptchaService, Aliyun Captcha 2.0 verification service., Verify a captcha token.          - If no ``ALIYUN_CAPTCHA_SCENE_ID`` is configur, Check whether a captcha token has already been consumed., _percent_encode(), SMS verification code service with rate-limiting., Return a 6-digit random numeric string., Send a verification code to *phone*.          Workflow:         1. Validate capt (+21 more)

### Community 29 - "Data Models & Schemas"
Cohesion: 0.09
Nodes (35): legacy_headers(), test_create_admin_user(), test_create_admin_user_requires_username(), test_create_app_user(), test_create_app_user_invalid_phone_format(), test_create_app_user_requires_phone(), test_create_duplicate_phone_returns_409(), test_create_duplicate_username_returns_409() (+27 more)

### Community 30 - "Miscellaneous Module"
Cohesion: 0.06
Nodes (7): 7d72fbb test: add study record service and API tests, TestGetSummary, TestListRecords, _add_booking(), TestCalculateStreakDays, TestGetMonthlySummary, TestListStudyRecords

### Community 31 - "Auth & Login Tests"
Cohesion: 0.08
Nodes (18): _content_type_for_extension(), generate_object_key(), get_storage_adapter(), _has_valid_signature(), ImageUploadService, _join_public_url(), LocalStorageAdapter, normalize_extension() (+10 more)

### Community 32 - "Auth & Login Tests"
Cohesion: 0.08
Nodes (17): 02b3b93 feat: add course-detail page with all sections (7.1-7.8), 0fc7746 chore: add teacher-profile-page OpenSpec artifacts and design doc, 148395b feat(br-app): add course detail navigation from training list page, 24f5ae5 tweak: 老师管理前端 — br-admin 老师列表/新增/编辑页（多选所属房间）+ br-app 教师简介页接入库表数据, 3437127 test(task-6): 课程详情+关注完整测试，实现 list course follows, 38a606f chore: archive course-detail-page change, 7a418d3 tweak: 老师管理后端 — teachers 表扩展 + teacher_rooms 关联 + 管理端 CRUD API + C 端详情扩展与测试, 7ff33ae Complete course-detail-page change (+9 more)

### Community 33 - "Auth & WeChat Integration"
Cohesion: 0.08
Nodes (20): ContentTypeEnum, RequestEnum, ResultEnum, IAsyncRouteState, IScreenLockState, isLocked, useScreenLockStore, ITabsViewState (+12 more)

### Community 34 - "Payment & Wallet"
Cohesion: 0.08
Nodes (23): PageEnum, DEFAULT_CONFIG, filter(), getConfig(), TreeHelperConfig, useAsyncRoute(), useAsyncRouteStore, ProjectSettingState (+15 more)

### Community 35 - "Booking Payment Tests"
Cohesion: 0.06
Nodes (24): jwt_service(), _mock_keys_result(), mock_redis(), Unit tests for JWTService., Refresh token contains sub, type=refresh, exp, and jti., Each refresh token gets a unique jti., blacklist_token stores the jti in Redis with correct TTL., Return an AsyncMock whose coroutine resolves to the given list. (+16 more)

### Community 36 - "Booking Domain Service"
Cohesion: 0.08
Nodes (7): 8403348 refactor: extract admin page builders, d2114a6 merge: br-admin business refactor, routes, routes, columns, adminInfo, token

### Community 37 - "Booking Service Tests"
Cohesion: 0.06
Nodes (2): routes, ParentLayout()

### Community 38 - "Course Management"
Cohesion: 0.07
Nodes (13): ActivityCouponBase, ActivityCouponFormItem, ActivityCouponItem, ActivityCouponTemplate, ActivityFormParams, ActivityItem, ActivityListParams, ActivityListResult (+5 more)

### Community 39 - "Booking Cancellation Tests"
Cohesion: 0.07
Nodes (15): CourseCreateParams, CourseDetail, CourseItem, CourseListResult, CourseScheduleItem, CourseUpdateParams, LessonCreateParams, LessonItem (+7 more)

### Community 40 - "Miscellaneous Module"
Cohesion: 0.09
Nodes (15): Props, useForm(), EmitType, UseFormActionContext, DATE_TYPE, dateItemType, basicProps, FormActionType (+7 more)

### Community 41 - "Coupon Service Layer"
Cohesion: 0.13
Nodes (19): UseFormValuesContext, is(), isArray(), isAsyncFunction(), isBoolean(), isDate(), isDef(), isElement() (+11 more)

### Community 42 - "Teacher Management Tests"
Cohesion: 0.06
Nodes (8): Integration tests for admin activity API endpoints., TestAdminAuth, TestAdminCreateActivity, TestAdminDeleteActivity, TestAdminGetActivity, TestAdminListActivities, TestAdminToggleStatus, TestAdminUpdateActivity

### Community 43 - "Booking Service Tests"
Cohesion: 0.10
Nodes (16): AppMiddleware, _booking_payment_reconciliation_loop(), _cleanup_unpaid_bookings_job(), health_check(), lifespan(), Health check endpoint., Fallback periodic runner for environments without APScheduler., Application lifespan: startup and shutdown events. (+8 more)

### Community 44 - "Coupon Service Tests"
Cohesion: 0.07
Nodes (11): Unit tests for training_service and room_type filter in study_room_service., 只返回 room_type 为 training 或 comprehensive 且 status=open 的房间。, 非热门课程不出现在 hot_courses 中。, 只返回 status=active 的课程。, 不传 room_type 时返回所有 open 状态的房间。, admin_list_rooms 的 room_type 过滤。, status 和 room_type 同时过滤。, TestAdminListRoomsRoomTypeFilter (+3 more)

### Community 45 - "Deployment Config"
Cohesion: 0.17
Nodes (22): _mock_scalar_one_result(), _mock_scalar_result(), _mock_scalars_result(), test_admin_get_statistics_aggregates_totals_and_active_users(), test_admin_list_transactions_joins_users_and_maps_user_fields(), test_confirm_payment_disabled_in_production(), test_create_recharge_order_rejects_unsupported_alipay(), test_create_wechat_recharge_order_returns_payment_params() (+14 more)

### Community 46 - "Token Verification"
Cohesion: 0.09
Nodes (13): _make_course(), Unit tests for CourseBookingService., full_package_price 为 None 时不触发优惠。, full_package_price 高于标准价时，discount_amount 为 0。, 空 lesson_ids 应被 Schema 拒绝。, 不存在的 course_id 返回 None。, 构造一个轻量 Course mock 对象。, 固定班课：3 课时 × ¥80 = ¥240。 (+5 more)

### Community 47 - "Booking Verification Service"
Cohesion: 0.13
Nodes (11): AdminAssignRoles, AdminResetPassword, AdminToggleStatus, AdminUserCreate, AdminUserDetail, AdminUserListItem, AdminUserListParams, AdminUserListResponse (+3 more)

### Community 48 - "Booking Domain Service"
Cohesion: 0.15
Nodes (25): ALIGNMENT_POSITIONS, appendBits(), applyMask(), chooseVersion(), cloneMatrix(), createCodewords(), createDataCodewords(), createQrSvgDataUrl() (+17 more)

### Community 49 - "Auth Service Layer"
Cohesion: 0.08
Nodes (6): 53c230a chore: add implementation plan and design doc for course-detail-page, 8e4fbeb chore: archive training-room-overview change & add course-detail-page proposal, ae1876c fix: 提交历史遗留改动（旧 change 归档、种子脚本与迁移文件）, d84d0ce feat: 培训室概况页课程列表UI优化 - 后端: HotCourseItem 添加 schedule/tags 字段, TrainingRoomResponse 添加 rating - 后端: training_service 传递 schedule/tags 到热门课程 - 前端: training/index.vue 培训室名称可点击跳转到概况页 - 前端: 课程项添加时钟图标+培训时间+热销/新课/名师标签 - 前端: booking/detail.vue 课程列表同步优化UI样式, e8b4197 feat: add CourseLesson model, LessonResponse schema, and seed script, ea02245 feat(db): add course_lessons table, follow_type and description column

### Community 50 - "Booking Cancellation Tests"
Cohesion: 0.22
Nodes (23): NamedTuple, BookingCouponCalculation, _calc_discount(), _calculate_hours(), _calculate_original_price(), _check_scope(), CouponError, CouponNotFoundError (+15 more)

### Community 51 - "Booking Cancellation Tests"
Cohesion: 0.08
Nodes (8): Integration tests for Course Booking API.  注意：当前测试基础设施使用 SQLite 内存数据库，不支持 Postgr, POST /api/v1/course-bookings。, 无效 lesson_ids 返回 400。, POST /api/v1/course-bookings/{booking_id}/cancel。, GET /api/v1/courses/{id}/lessons。, TestCancelCourseBooking, TestCreateCourseBooking, TestGetCourseLessons

### Community 52 - "User & Auth Models"
Cohesion: 0.08
Nodes (9): TDD tests for course detail API (Task 4).  Covers: - 4.3 CourseDetailResponse /, 测试 training_service.get_course_detail()。, 正常返回课程详情，含教师、教室、课时和相关课程。, 无教师的课程，teacher 字段为 None。, 无同分类课程时，related_courses 为空列表。, 测试 GET /api/v1/training/courses/{course_id} 路由。, 相关课程超过 6 门时，只返回 6 门，排除当前课程。, TestCourseDetailRoute (+1 more)

### Community 53 - "Booking Payment Service"
Cohesion: 0.09
Nodes (12): { apiUrl, urlPrefix }, mockAdapter, { useMock, loggerMock }, BookingItem, BookingListParams, BookingListResult, useGlobSetting(), useLocalSetting() (+4 more)

### Community 54 - "Teacher Management Tests"
Cohesion: 0.10
Nodes (12): 06c38d2 fix: 优化管理端钱包流水展示, 13f942b fix: 更新用户端钱包退款文案, 7979a96 Complete admin wallet backend, 90b89ef docs: document admin wallet finance api, 99ced87 feat(admin): add wallet frontend routing api, 9e3fd4a feat: 注册 admin_wallet 路由到 main.py, a67a5e8 fix: 修正交易列表路由路径为 /transactions, c4ee8f1 fix: 调整用户端钱包退款导航文案 (+4 more)

### Community 55 - "Miscellaneous Module"
Cohesion: 0.21
Nodes (22): _activity_coupon_to_public_response(), _activity_to_admin_response(), _admin_coupon_to_response(), claim_activity_coupon(), claim_activity_coupon_response(), _count_user_claims(), _coupon_to_response(), create_activity() (+14 more)

### Community 57 - "Booking Data Models"
Cohesion: 0.17
Nodes (19): _access_token(), _phone_user(), _temp_wechat_user(), test_bind_phone_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_sms_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_with_sms_to_new_phone(), test_bind_wechat_phone_code_to_new_phone(), test_bound_user_binding_unused_phone_returns_409() (+11 more)

### Community 58 - "Coupon Service Layer"
Cohesion: 0.09
Nodes (23): ChangeEvent, DeepPartial, Element, ElementAttributesProperty, ElementClass, Event, ImportMetaEnv, Indexable (+15 more)

### Community 59 - "Auth & Login Tests"
Cohesion: 0.11
Nodes (8): 3baaa8d feat: integrate WeChat wallet payments, b15c9d7 updated .gitignore, b610482 Archive wechat payment integration OpenSpec change, e07a2b2 feat: add wallet transactions frontend, ed78866 Implement wallet recharge flow, f93686c merge: wallet transactions frontend, create_wallet_table  Revision ID: 28a1f4af90df Revises: b3a7c9d2e4f1 Create Date, update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:

### Community 61 - "Teacher Management Tests"
Cohesion: 0.19
Nodes (20): AdminCouponCreate, AdminCouponListResponse, AdminCouponResponse, AdminCouponStatusUpdate, AdminCouponUpdate, AdminCouponError, AdminCouponNotFoundError, _clean_coupon_data() (+12 more)

### Community 62 - "Teacher Management Tests"
Cohesion: 0.10
Nodes (10): 42c7c58 fix: commit missing Alembic migration file for training tables, 4ecad22 chore: add training-course-list OpenSpec artifacts, design doc, and implementation plan, 681b536 feat: add training API module, 8543cb6 feat: add Teacher/Course models and room_type migration, 8838ec3 chore: archive training-course-list, ade5071 Merge feature/20260814/training-course-list: training course list page with teacher/course models, training API, and frontend page, d44876b chore: archive hide-cancelled-order-actions, TDD 测试：验证 Teacher、Course 模型及 StudyRoom.room_type 字段存在。  此测试先于实现编写，应先失败（RED），再通过实 (+2 more)

### Community 63 - "Miscellaneous Module"
Cohesion: 0.09
Nodes (11): BookingUseCases, Application use case orchestration layer., 645d7d5 refactor: extract booking repository conflict query, 9ea74c1 test: align admin booking detail fixture assertion, bb3b56d refactor: extract verification token rules, bfd21f6 refactor: extract wallet transaction repository, e2a44c1 refactor: add app formatter constants, ef806eb refactor: add booking use case facade (+3 more)

### Community 64 - "Deployment Config"
Cohesion: 0.10
Nodes (9): 0e90f58 fix: 排课更新后强制刷新列表数据, 25778f9 fix: 发布设置区块去除多余空白间隔，课程排课查询强制绕过缓存, 31949f1 docs: 记录 BUG-25 排课保存后列表不刷新(Alova GET 内存缓存), 3d61e55 fix: 注册 NFormItemGi 和 NPopconfirm 组件，恢复发布设置区块, 3f1e632 fix: 课程编辑页布局调整 - 热门/排序/状态移入基本信息，课时编辑显示分钟单位，删除按钮可见, 8438d36 fix: 排课列表保存后不刷新 + time_slots 改为周几格式, 9068db6 fix: 基本信息移除课程状态，发布设置移除课程状态标签, ae205e4 refactor: 排课时间段选择器改为日期×时间段网格布局 (+1 more)

### Community 65 - "Backend Service Layer"
Cohesion: 0.26
Nodes (17): _make_booking(), _make_coupon(), _make_room(), _make_seat(), _make_user(), _make_user_coupon(), test_admin_cancel_booking(), test_admin_cancel_booking_already_cancelled() (+9 more)

### Community 67 - "Booking Cancellation Tests"
Cohesion: 0.10
Nodes (10): 0fad7a7 fix: resolve API 307 redirect and 404 caused by trailing slash inconsistency, 3af03bb fix: consolidate CORS and trailing-slash into single ASGI middleware, abed773 chore: update br-admin logo image, remove backup, bb0ffd4 feat: rebrand br-admin to 后台管理, update logos and Dockerfiles, bc0df21 docs: archive coupon management admin spec, da88def feat: update branding, logo and tabBar styling for br-app, df8ff83 fix: improve activity coupon selection, f0eb49c fix: resolve CORS policy error for production deployment on 8.129.17.71 (+2 more)

### Community 68 - "Booking Cancellation Tests"
Cohesion: 0.17
Nodes (18): ActivityAdminResponse, ActivityCouponAdminResponse, ActivityCouponClaimResponse, ActivityCouponClaimUserCouponResponse, ActivityCouponInput, ActivityCouponPublicResponse, ActivityCouponTemplateResponse, ActivityCreate (+10 more)

### Community 69 - "Booking Payment Tests"
Cohesion: 0.21
Nodes (7): BookingPaymentAlreadyProcessedError, BookingPaymentError, BookingPaymentNotFoundError, BookingPaymentService, BookingPaymentSignatureError, InvalidBookingPaymentCallbackError, WechatOpenIdRequiredError

### Community 70 - "Miscellaneous Module"
Cohesion: 0.19
Nodes (1): WechatAuthService

### Community 71 - "User Security Tests"
Cohesion: 0.15
Nodes (8): EditRecordRow, renderEditCell(), Instance, key, RetInstance, BasicColumn, BasicTableProps, TableActionType

### Community 72 - "Booking Service Tests"
Cohesion: 0.11
Nodes (12): BusinessSelectOption, useAdminBusiness(), useAdminBusinessStore, CityItem, getRoomList(), RoomFormParams, RoomItem, RoomListParams (+4 more)

### Community 73 - "Course Management"
Cohesion: 0.12
Nodes (4): 0605022 fix: 课程编辑页与列表页在原 tab 内互相跳转，不再新开标签页, 107108e tweak: 课程上课时间统一格式化并在培训室详情显示（截断+悬停提示）, 5f8183b fix: 课程编辑页返回改用 router.back 方案，修复保存成功后误报保存失败及导航异常, 8e1b05e feat: 保存课程后返回列表页，课程列表分类显示中文名称

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
Cohesion: 0.11
Nodes (5): Integration tests for training room and course APIs., Insert training rooms, teachers, and courses into the test database., seed_training_data(), TestCoursesAPI, TestTrainingRoomsAPI

### Community 78 - "Integration Tests"
Cohesion: 0.14
Nodes (9): 2caef8e Merge pull request #2 from sin668/feat/booking-room-list-detail-fix, 3709fe0 docs: localize br-app refactor plan, 3ec39c1 fix: resolve undefined `actions` reference in booking list page, 950b25d refactor: extract followed room service, d89d2c0 feat: add followed rooms to profile, df06846 Implement city selection frontend, e95d205 Archive city-selection-frontend OpenSpec change, ef18031 Archive wallet-recharge-frontend change and sync specs (+1 more)

### Community 79 - "Notification System"
Cohesion: 0.12
Nodes (3): 00cde52 Implement dynamic booking verification QR flow, 39024d3 fix: stabilize booking verification QR flow, 7143168 Archive personal QR OpenSpec change

### Community 80 - "Course Management"
Cohesion: 0.16
Nodes (14): ClickOutside, DocumentHandler, FlushList, nodeList, addClass(), getBoundingClientRect(), getViewportOffset(), hasClass() (+6 more)

### Community 81 - "Teacher & Course Models"
Cohesion: 0.18
Nodes (4): _coupon(), _seed_activity_coupon(), TestActivityCouponAPI, TestActivityCouponService

### Community 83 - "RBAC Service Layer"
Cohesion: 0.12
Nodes (3): 7c70899 feat: add VIP membership and coupon admin, add_membership_level  Revision ID: df6ae550899a Revises: f1a2b3c4d5e6 Create Dat, add_wallet_membership_result  Revision ID: a2b3c4d5e6f7 Revises: df6ae550899a Cr

### Community 84 - "Booking Cancellation Tests"
Cohesion: 0.23
Nodes (5): hash_id_card(), is_valid_id_card(), mask_id_card(), mask_phone(), UserSecurityService

### Community 85 - "Booking Verification Tests"
Cohesion: 0.12
Nodes (2): admin_client(), unauth_client()

### Community 86 - "Booking Service Tests"
Cohesion: 0.12
Nodes (1): TestCreateBooking

### Community 87 - "Booking Service Tests"
Cohesion: 0.15
Nodes (7): COURSE_WEEKDAY_NAMES, formatAmount(), formatHourCount(), formatHourDuration(), formatMoney(), formatRoomMinPrice(), toFiniteNumber()

### Community 88 - "Booking Service Tests"
Cohesion: 0.21
Nodes (16): del(), doRefreshToken(), get(), getRefreshToken(), getToken(), patch(), pendingRequests, post() (+8 more)

### Community 89 - "Coupon System"
Cohesion: 0.17
Nodes (11): 316d285 feat: add study record schemas, 5ce3f55 Merge branch 'worktree-learning-record-impl' into main, 83ccd35 feat: add study record backend (schema, service, routes), CalendarMark, StudyRecordItem, StudyRecordListResponse, StudyRecordSummaryResponse, _build_record_item() (+3 more)

### Community 90 - "Database Config"
Cohesion: 0.16
Nodes (8): useModal(), BasicProps, ModalMethods, ModalProps, RegisterFn, UseModalReturnType, isProdMode(), getDynamicProps()

### Community 91 - "Room & Seat Management"
Cohesion: 0.17
Nodes (10): Banner, list_active_banners(), Return all active banners ordered by sort_order ascending., Unit tests for banner_service module., Seed banners for tests., Only active banners are returned., Results are ordered by sort_order ascending., Empty DB returns empty list. (+2 more)

### Community 93 - "Coupon System"
Cohesion: 0.16
Nodes (11): asyncImportRoute(), generateDynamicRoutes(), generateRoutes(), LayoutMap, constantRouterIcon, AppRouteRecordRaw, Component, IModuleType (+3 more)

### Community 94 - "Room & Seat Management"
Cohesion: 0.14
Nodes (4): create_course(), get_course_detail(), Admin course management API routes., update_course()

### Community 95 - "Room Management Tests"
Cohesion: 0.13
Nodes (8): SeatBulkParams, SeatBulkResult, SeatBulkZoneConfig, SeatFormParams, SeatItem, SeatListParams, SeatStatusParams, SeatUpdateParams

### Community 97 - "Teacher Management"
Cohesion: 0.17
Nodes (5): 4df870a fix: 课程编辑页路由使用 hideInMenu 替代 hidden 以匹配动态路由合并逻辑, 55e7654 feat: 实现课程编辑后台页面及课时CRUD功能, cbcedef fix: 修复课程列表删除按钮颜色值错误导致的渲染崩溃, f8f8716 fix: 修复培训课程菜单图标不显示和课程列表为空的问题, fc88d29 feat: 培训课程列表新增排课弹窗功能

### Community 98 - "Booking Service Tests"
Cohesion: 0.13
Nodes (14): AdminWalletStatisticsResponse, AdminWalletTransactionListResponse, AdminWalletTransactionResponse, BalanceResponse, PaymentParams, PromoCodeRequest, PromoCodeResponse, RechargeOrderResponse (+6 more)

### Community 99 - "Teacher Management"
Cohesion: 0.13
Nodes (1): AdminCourseService

### Community 100 - "Miscellaneous Module"
Cohesion: 0.24
Nodes (1): TestCancelBooking

### Community 101 - "Teacher & Course Models"
Cohesion: 0.13
Nodes (2): Integration tests for file upload API endpoints., TestUploadAPI

### Community 103 - "Data Model Tests"
Cohesion: 0.27
Nodes (13): appRoot, assert, fs, loadModule(), main(), path, testAccountSecurity(), testAccountSecurityApi() (+5 more)

### Community 104 - "Coupon Service Tests"
Cohesion: 0.30
Nodes (1): AdminMenuService

### Community 105 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (13): _apply_menu_seed(), _ensure_role_menus(), _ensure_user_role(), _get_or_create_admin(), _get_or_create_app_role(), _get_or_create_menu(), _get_or_create_role(), main() (+5 more)

### Community 106 - "Room & Seat Management"
Cohesion: 0.15
Nodes (7): AdminTeacherCreateParams, AdminTeacherDetail, AdminTeacherItem, AdminTeacherListResult, AdminTeacherUpdateParams, QualificationItem, TeacherRoomBrief

### Community 108 - "Integration Tests"
Cohesion: 0.17
Nodes (11): 5187776 feat: show wallet balance on booking confirmation, 548e6b2 fix: load profile wallet stats, 597670e Add profile stat navigation links, 7487fee style: soften booking wallet balance, failures, fs, path, profilePath (+3 more)

### Community 109 - "Teacher Service Layer"
Cohesion: 0.18
Nodes (8): debounce, ElType, HTMLElement, permission, ElType, HTMLElement, throttle, usePermission()

### Community 110 - "Room & Seat Service"
Cohesion: 0.21
Nodes (7): DesignSettingState, useDesignSetting(), useDesignSettingStore, setupRouter(), pinia, setupStore(), store

### Community 111 - "Miscellaneous Module"
Cohesion: 0.15
Nodes (10): AdminTeacherCreate, AdminTeacherDetail, AdminTeacherListItem, AdminTeacherListResponse, AdminTeacherStatusUpdate, AdminTeacherUpdate, QualificationItem, 管理端老师管理 Pydantic schemas。 (+2 more)

### Community 112 - "Teacher Management"
Cohesion: 0.23
Nodes (3): _make_user(), TestProcessVipUpgrade, TestVIPScopeFilter

### Community 113 - "Auth & Login Tests"
Cohesion: 0.24
Nodes (4): ComponentProps, componentMap, EventEnum, ComponentType

### Community 114 - "Booking Cancellation Tests"
Cohesion: 0.35
Nodes (2): SystemSetting, AdminSettingService

### Community 116 - "Token Verification"
Cohesion: 0.17
Nodes (6): Delete a refresh token reference from Redis., Delete every stored refresh token for a user., Check whether a refresh token is still valid (present in Redis)., Rotate a refresh token: create a new one, store it, revoke the old one., Create a long-lived refresh token with a unique jti.          Payload contains:, Store a refresh token reference in Redis.          Key: ``refresh:{user_id}:{jti

### Community 117 - "Miscellaneous Module"
Cohesion: 0.27
Nodes (7): admin_list_seats(), bulk_create_seats(), create_seat(), _get_booked_seat_ids(), get_seat_stats(), list_seats(), _room_exists()

### Community 119 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (9): _create_user(), test_change_password_rejects_bad_old_password_or_mismatch(), test_change_password_updates_hash_and_revokes_refresh_tokens(), test_deactivate_account_blocks_risks(), test_deactivate_account_sets_deleted_without_removing_user(), test_security_summary_masks_sensitive_fields(), test_security_summary_returns_deleted_unbound_unverified_state(), test_submit_identity_rejects_invalid_or_different_verified() (+1 more)

### Community 122 - "User & Auth Models"
Cohesion: 0.29
Nodes (10): 0072a7a 时区Bug fixed, 0f28968 Bug fixed, 5c47a3c archive coupon package frontend openspec change, c66da47 updated bug-fixed.md, _china_now_naive(), _get_or_create_demo_user(), seed_all(), seed_coupons() (+2 more)

### Community 123 - "RBAC Service Layer"
Cohesion: 0.25
Nodes (7): screenEnum, screenMap, sizeEnum, CreateCallbackParams, RemoveEventFn, useEventListener(), UseEventParams

### Community 124 - "Miscellaneous Module"
Cohesion: 0.35
Nodes (10): _build_wechat_client(), confirm_recharge(), create_recharge(), get_balance(), get_recharge_order(), list_transactions(), _notify_failure(), redeem_promo_code() (+2 more)

### Community 126 - "Admin Coupon Tests"
Cohesion: 0.33
Nodes (3): _coupon_data(), _create_coupon(), TestAdminCouponService

### Community 127 - "Teacher Management Tests"
Cohesion: 0.22
Nodes (2): _payload(), TestAdminCouponApi

### Community 128 - "Seat Management Tests"
Cohesion: 0.18
Nodes (6): TrainingRoomDetailResponse schema 测试, 验证嵌套 CourseResponse 的 tags 为 None 时解析为空列表, 验证缺少必填字段时抛出 ValidationError, 验证 teachers 和 courses 字段默认值为空列表, 验证嵌套的 CourseResponse 中 tags 字段可以正确解析逗号分隔字符串, TestTrainingRoomDetailResponse

### Community 129 - "Teacher Management Tests"
Cohesion: 0.22
Nodes (3): test_first_wechat_login_creates_phone_null_user_and_caches_session_key(), test_repeat_wechat_login_reuses_bound_user(), _token_sub()

### Community 131 - "Token Verification"
Cohesion: 0.20
Nodes (4): TransactionLike, Protocol, Persist an upload object and return the public result., StorageAdapter

### Community 133 - "HTML Sanitizer"
Cohesion: 0.24
Nodes (2): HTMLParser, _RichTextSanitizer

### Community 134 - "User Management"
Cohesion: 0.27
Nodes (6): setupCustomComponents(), setupDirectives(), setupGlobalMethods(), naive, setupNaive(), setupNaiveDiscreteApi()

### Community 135 - "Miscellaneous Module"
Cohesion: 0.22
Nodes (9): SeatAdminResponse, SeatBulkCreate, SeatBulkZoneConfig, SeatCreate, SeatResponse, SeatStatsResponse, SeatStatusUpdate, SeatUpdate (+1 more)

### Community 137 - "Booking Payment Service"
Cohesion: 0.33
Nodes (1): AdminRoleService

### Community 139 - "Booking Service Tests"
Cohesion: 0.20
Nodes (1): TestSeatAPI

### Community 140 - "Booking Cancellation Tests"
Cohesion: 0.36
Nodes (8): _create_user(), test_get_current_user_profile_returns_username_fields(), test_update_nickname_does_not_require_username_cooldown(), test_update_profile_rejects_protected_fields(), test_update_username_rejects_cooldown(), test_update_username_rejects_duplicate(), test_update_username_rejects_invalid_format(), test_update_username_success_sets_cooldown_timestamp()

### Community 142 - "Teacher Management Tests"
Cohesion: 0.20
Nodes (9): GlobConfig, GlobEnvConfig, IBodySetting, ICrumbsSetting, IHeaderSetting, IMenuSetting, IMultiTabsSetting, LocalConfig (+1 more)

### Community 143 - "Auth & Login Tests"
Cohesion: 0.20
Nodes (9): ComponentElRef, ComponentRef, ElRef, EmitType, Fn, LabelValueOptions, PromiseFn, RefType (+1 more)

### Community 144 - "Deployment Config"
Cohesion: 0.29
Nodes (10): bchRemainder(), bitLength(), drawAlignment(), drawFinder(), drawFormatInfo(), drawFunctionPatterns(), drawVersionInfo(), FORMAT_COORDS_2() (+2 more)

### Community 145 - "Miscellaneous Module"
Cohesion: 0.28
Nodes (3): adminRequest(), confirmVerification(), inspectVerificationToken()

### Community 147 - "Deployment Config"
Cohesion: 0.31
Nodes (4): useTimeoutFn(), useTimeoutRef(), useBreakpoint(), useDesignSetting()

### Community 148 - "Miscellaneous Module"
Cohesion: 0.22
Nodes (7): COURSE_CATEGORY_LABELS, COURSE_CATEGORY_OPTIONS, COURSE_STATUS_TAGS, BusinessTagConfig, EDUCATION_OPTIONS, ROOM_TYPE_LABELS, TEACHER_STATUS_TAGS

### Community 149 - "Miscellaneous Module"
Cohesion: 0.25
Nodes (7): AdminMenuBase, AdminMenuCreate, AdminMenuNode, AdminMenuRoute, AdminMenuRouteMeta, AdminMenuUpdate, ComponentOption

### Community 150 - "Teacher Management"
Cohesion: 0.22
Nodes (8): exportMatch, fs, getCallMatch, paramMatch, path, source, trainingApiPath, urlMatch

### Community 151 - "Miscellaneous Module"
Cohesion: 0.39
Nodes (7): followRoom(), getFollowedRooms(), isRoomFollowed(), normalizeRoom(), setFollowedRooms(), syncFollowedRooms(), unfollowRoom()

### Community 152 - "RBAC Data Models"
Cohesion: 0.22
Nodes (1): TestAvailableCouponsForBooking

### Community 153 - "Token Verification"
Cohesion: 0.22
Nodes (5): get_current_user_id returns the user UUID from a valid access token., get_current_user_id raises 401 for a blacklisted token., get_current_user_id raises 401 when token type is not 'access'., get_current_user_id raises 401 for an expired token., TestGetCurrentUserId

### Community 154 - "Room & Seat Management"
Cohesion: 0.33
Nodes (5): getAppEnvConfig(), getCommonStoragePrefix(), getEnv(), getStorageShortName(), warn()

### Community 155 - "JWT Token Tests"
Cohesion: 0.25
Nodes (2): CountTo, withInstall()

### Community 156 - "Integration Tests"
Cohesion: 0.39
Nodes (5): create_coupon(), delete_coupon(), _service_error(), toggle_coupon_status(), update_coupon()

### Community 158 - "Database Migrations"
Cohesion: 0.36
Nodes (5): create_teacher(), get_teacher_detail(), Admin teacher management API routes., toggle_teacher_status(), update_teacher()

### Community 159 - "Miscellaneous Module"
Cohesion: 0.32
Nodes (3): list_notifications(), mark_all_notifications_read(), _parse_notification_type()

### Community 160 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (7): AdminRoleBase, AdminRoleCreate, AdminRoleListResponse, AdminRoleMenusResponse, AdminRoleMenuUpdate, AdminRoleResponse, AdminRoleUpdate

### Community 161 - "Miscellaneous Module"
Cohesion: 0.32
Nodes (6): assertContains(), assertMatches(), fs, path, read(), root

### Community 162 - "Coupon Service Layer"
Cohesion: 0.29
Nodes (7): appRoot, assert, fs, loadModule(), main(), path, vm

### Community 163 - "Room & Seat Management"
Cohesion: 0.46
Nodes (7): followCourse(), getFollowedCourses(), isCourseFollowed(), normalizeCourse(), setFollowedCourses(), syncFollowedCourses(), unfollowCourse()

### Community 165 - "User Management"
Cohesion: 0.43
Nodes (6): _policy(), test_exact_24_hours_charges_20_percent(), test_exact_2_hours_charges_50_percent(), test_exact_48_hours_charges_10_percent(), test_non_round_amount_keeps_penalty_and_refund_balanced(), test_over_48_hours_full_refund()

### Community 169 - "Room & Seat Models"
Cohesion: 0.52
Nodes (5): createUploadError(), normalizeErrorMessage(), parseUploadResponse(), uploadImage(), uploadOnce()

### Community 170 - "Teacher & Course Models"
Cohesion: 0.33
Nodes (6): close_redis(), get_redis(), init_redis(), Initialize and return the singleton Redis connection., Close the Redis connection., FastAPI dependency that provides an async Redis connection.

### Community 174 - "Course Management"
Cohesion: 0.52
Nodes (6): followTeacher(), getFollowedTeachers(), isTeacherFollowed(), normalizeTeacher(), setFollowedTeachers(), unfollowTeacher()

### Community 177 - "Auth & Login Tests"
Cohesion: 0.29
Nodes (4): send-code with captcha_token passes it through., When SMSService raises HTTPException, it propagates., Successful send-code returns 200., TestSendCode

### Community 178 - "Booking Cancellation Tests"
Cohesion: 0.29
Nodes (4): GET /me without auth returns 401., GET /me with valid auth returns user info., GET /me with auth but user not in DB returns 404., TestGetMeAuth

### Community 179 - "Token Verification"
Cohesion: 0.29
Nodes (4): Invalid token returns 401., No credentials (no Authorization header) returns 401., Valid access token returns the user ID., TestGetCurrentUserId

### Community 180 - "Project Documentation"
Cohesion: 0.29
Nodes (4): verify_token returns payload for a valid token., verify_token raises HTTPException 401 for an expired token., verify_token raises HTTPException 401 for a token with wrong secret., TestVerifyToken

### Community 181 - "Booking System Core"
Cohesion: 0.29
Nodes (4): store_refresh_token stores with correct key and TTL., revoke_refresh_token deletes the key from Redis., is_refresh_token_valid checks Redis existence., TestRefreshTokenStorage

### Community 182 - "Notification System"
Cohesion: 0.29
Nodes (1): TestCourseModel

### Community 183 - "Auth & WeChat Integration"
Cohesion: 0.29
Nodes (1): seed_teacher_data()

### Community 187 - "Token Verification"
Cohesion: 0.33
Nodes (3): FastAPI Depends-compatible callable.          Decodes the token, checks blacklis, Decode and return the token payload.          Raises HTTPException 401 if the to, Check whether a token (by jti) is in the Redis blacklist.

### Community 191 - "Admin RBAC System"
Cohesion: 0.33
Nodes (2): Integration tests for city APIs., TestCityAPI

### Community 192 - "Room & Seat Management"
Cohesion: 0.33
Nodes (2): Unit tests for the City model., TestCityModel

### Community 196 - "Miscellaneous Module"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 197 - "Miscellaneous Module"
Cohesion: 0.40
Nodes (3): copy, ElType, HTMLElement

### Community 198 - "Auth & Login Tests"
Cohesion: 0.60
Nodes (3): can_cancel_paid_booking(), has_booking_started(), should_mark_booking_completed()

### Community 199 - "Booking Service Tests"
Cohesion: 0.50
Nodes (3): PermissionsEnum, ActionItem, PopConfirm

### Community 200 - "Community 200"
Cohesion: 0.60
Nodes (4): AvailableCouponForBookingResponse, AvailableCouponsForBookingListResponse, CouponBaseResponse, CouponResponse

### Community 201 - "Community 201"
Cohesion: 0.70
Nodes (4): booking_now(), booking_start_datetime(), calculate_cancellation_policy(), CancellationPolicyResult

### Community 202 - "Community 202"
Cohesion: 0.60
Nodes (3): createPaymentStatusError(), getPaymentStatus(), pollPaymentStatus()

### Community 203 - "Community 203"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 204 - "Community 204"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 205 - "Community 205"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 206 - "Community 206"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_component_options_and_invalid_component(), test_dynamic_routes_exclude_buttons_and_disabled_nodes(), test_menu_tree_crud_and_delete_child_conflict()

### Community 207 - "Community 207"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_email_test_requires_complete_config(), test_settings_read_masks_smtp_password(), test_update_email_without_password_preserves_existing_secret()

### Community 209 - "Community 209"
Cohesion: 0.40
Nodes (3): No admin token returns 401., Wrong admin token returns 401., TestGetCurrentAdmin

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

### Community 216 - "Community 216"
Cohesion: 0.50
Nodes (3): BOOKING_STATUS_LABELS, BOOKING_TABS, SEAT_ZONE_LABELS

### Community 217 - "Community 217"
Cohesion: 0.50
Nodes (3): draggable, ElType, HTMLElement

### Community 218 - "Community 218"
Cohesion: 0.83
Nodes (2): setLoading(), useAsync()

### Community 219 - "Community 219"
Cohesion: 0.50
Nodes (1): key

### Community 220 - "Community 220"
Cohesion: 0.50
Nodes (1): useCityStore

### Community 223 - "Community 223"
Cohesion: 0.83
Nodes (3): legacy_headers(), test_role_crud_duplicate_and_assigned_delete_conflict(), test_role_menu_assignment_updates_auth_permissions()

### Community 225 - "Community 225"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17

### Community 226 - "Community 226"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:

### Community 227 - "Community 227"
Cohesion: 0.50
Nodes (1): create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create

### Community 228 - "Community 228"
Cohesion: 0.50
Nodes (1): create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat

### Community 229 - "Community 229"
Cohesion: 0.50
Nodes (1): booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:

### Community 230 - "Community 230"
Cohesion: 0.50
Nodes (1): create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea

### Community 231 - "Community 231"
Cohesion: 0.50
Nodes (1): add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf

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
Cohesion: 0.67
Nodes (1): __APP_INFO__

### Community 246 - "Community 246"
Cohesion: 0.67
Nodes (1): WindowSizeOptions

### Community 248 - "Community 248"
Cohesion: 0.67
Nodes (1): Battery

### Community 250 - "Community 250"
Cohesion: 0.67
Nodes (1): TeacherDetailResponse

### Community 251 - "Community 251"
Cohesion: 0.67
Nodes (2): appThemeList, setting

### Community 254 - "Community 254"
Cohesion: 0.67
Nodes (1): TestStudyRoomAPI

### Community 259 - "Community 259"
Cohesion: 1.00
Nodes (1): BasicProps

### Community 260 - "Community 260"
Cohesion: 1.00
Nodes (1): directive

### Community 261 - "Community 261"
Cohesion: 1.00
Nodes (1): RoleEnum

### Community 267 - "Community 267"
Cohesion: 1.00
Nodes (1): TeacherCourseItem

### Community 268 - "Community 268"
Cohesion: 1.00
Nodes (1): animates

### Community 270 - "Community 270"
Cohesion: 1.00
Nodes (1): DynamicProps

### Community 272 - "Community 272"
Cohesion: 1.00
Nodes (1): params

## Knowledge Gaps
- **384 isolated node(s):** `requestParams`, `result`, `token`, `adminInfo`, `menusList` (+379 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Booking Service Tests`** (2 nodes): `routes`, `ParentLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (1 nodes): `WechatAuthService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Token Verification`** (1 nodes): `admin_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Verification Tests`** (2 nodes): `admin_client()`, `unauth_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (1 nodes): `TestCreateBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher Management`** (1 nodes): `AdminCourseService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (1 nodes): `TestCancelBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher & Course Models`** (2 nodes): `Integration tests for file upload API endpoints.`, `TestUploadAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coupon Service Tests`** (1 nodes): `AdminMenuService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Cancellation Tests`** (2 nodes): `SystemSetting`, `AdminSettingService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher Management Tests`** (2 nodes): `_payload()`, `TestAdminCouponApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HTML Sanitizer`** (2 nodes): `HTMLParser`, `_RichTextSanitizer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Payment Service`** (1 nodes): `AdminRoleService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (1 nodes): `TestSeatAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `RBAC Data Models`** (1 nodes): `TestAvailableCouponsForBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `JWT Token Tests`** (2 nodes): `CountTo`, `withInstall()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Notification System`** (1 nodes): `TestCourseModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth & WeChat Integration`** (1 nodes): `seed_teacher_data()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Admin RBAC System`** (2 nodes): `Integration tests for city APIs.`, `TestCityAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Room & Seat Management`** (2 nodes): `Unit tests for the City model.`, `TestCityModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 210`** (2 nodes): `StudyRoom.room_type 字段验证。`, `TestStudyRoomRoomType`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 211`** (1 nodes): `TestTeacherModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 218`** (2 nodes): `setLoading()`, `useAsync()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 219`** (1 nodes): `key`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 220`** (1 nodes): `useCityStore`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 225`** (1 nodes): `create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 226`** (1 nodes): `create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 227`** (1 nodes): `create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 228`** (1 nodes): `create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (1 nodes): `booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 230`** (1 nodes): `create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 231`** (1 nodes): `add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf`
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
- **Thin community `Community 245`** (1 nodes): `__APP_INFO__`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 246`** (1 nodes): `WindowSizeOptions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 248`** (1 nodes): `Battery`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 250`** (1 nodes): `TeacherDetailResponse`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 251`** (2 nodes): `appThemeList`, `setting`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 254`** (1 nodes): `TestStudyRoomAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 259`** (1 nodes): `BasicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 260`** (1 nodes): `directive`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 261`** (1 nodes): `RoleEnum`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 267`** (1 nodes): `TeacherCourseItem`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 268`** (1 nodes): `animates`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 270`** (1 nodes): `DynamicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 272`** (1 nodes): `params`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Auth & Login Tests` to `Auth & Login Tests`, `Coupon System`, `Teacher Management Tests`, `Teacher Management`, `Token Verification`, `Token Verification`, `Room Management Tests`, `Auth & Login Tests`, `Booking Cancellation Tests`, `Token Verification`, `Token Verification`, `Booking Cancellation Tests`, `Booking Payment Tests`, `Miscellaneous Module`, `Booking Service Tests`, `Auth & WeChat Integration`, `Booking Payment Tests`, `Project Documentation`, `Booking System Core`, `Token Verification`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `StudyRoom` connect `Teacher Management Tests` to `Booking Service Tests`, `Booking Payment Tests`, `SMS & Captcha Tests`, `Wallet Service Tests`, `Teacher Management`, `Booking Payment Tests`, `Booking Payment Tests`, `Auth & Login Tests`, `Teacher Management Tests`, `Database Config`, `Miscellaneous Module`, `Booking Service Tests`, `Token Verification`, `Booking Cancellation Tests`, `Booking Data Models`, `Community 254`, `Booking Service Tests`, `Miscellaneous Module`, `RBAC Data Models`, `Token Verification`, `User & Auth Models`, `Auth & WeChat Integration`, `Coupon Service Tests`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `Base` connect `SMS & Captcha Tests` to `Token Verification`, `Coupon System`, `Booking Cancellation Tests`, `Room & Seat Management`, `Teacher Management Tests`, `Booking Cancellation Tests`, `Wallet Service Tests`, `Teacher Management Tests`, `Booking Payment Tests`, `Auth & Login Tests`, `SMS & Captcha Tests`, `Auth & Login Tests`, `Booking Cancellation Tests`, `Booking Data Models`, `Token Verification`, `Community 209`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 244 inferred relationships involving `StudyRoom` (e.g. with `Base` and `City`) actually correct?**
  _`StudyRoom` has 244 INFERRED edges - model-reasoned connections that need verification._
- **Are the 212 inferred relationships involving `Settings` (e.g. with `AdminAuthService` and `AuthService`) actually correct?**
  _`Settings` has 212 INFERRED edges - model-reasoned connections that need verification._
- **What connects `requestParams`, `result`, `token` to the rest of the system?**
  _384 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Booking Service Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.05128205128205128 - nodes in this community are weakly interconnected._
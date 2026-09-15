# Graph Report - .  (2026-09-11)

## Corpus Check
- Large corpus: 1118 files · ~618,475 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 5899 nodes · 13058 edges · 247 communities detected
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 3058 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output
- Edge kinds: uses: 3058 · contains: 2902 · ON_BRANCH: 1572 · MODIFIES: 1402 · calls: 1148 · rationale_for: 835 · method: 710 · PARENT_OF: 501 · imports_from: 324 · inherits: 316 · imports: 283 · re_exports: 7


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 1118 · Candidates: 1586
- Excluded: 56 untracked · 89385 ignored · 0 sensitive · 25 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `47a6400`
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
Cohesion: 0.03
Nodes (194): feature/20260902/booking-order-lifecycle-refactor, main, 00b5289 fix: 课程预约待开始订单取消时仅删除 custom 排课，fixed 固定班课排课保留, 00c24d0 refactor: 支付回调与课程下单改调状态纯函数，booking_now 收敛为 re-export, 0148cfd feat: br-app课程相关页面仅展示固定班课排课 - training_service全部C端查询(培训室列表热门课程/培训室详情/课程列表/课程详情/相关课程)排课JOIN限定schedule_type=fixed - get_course_with_lessons(课程预约页)排课JOIN限定fixed并按创建时间取最早一条 - 定制课时排课记录不在C端课程页面展示，订单页面不受影响, 020ddd3 debug: 延期功能前后端参数传递添加调试日志, 04745c9 chore: archive course-booking, 04f0a66 feat: 新增订单状态定时转换任务 (+186 more)

### Community 1 - "Teacher Management Tests"
Cohesion: 0.05
Nodes (188): dev, feature/20260814/training-course-list, feature/20260817/course-booking, feature/20260817/course-detail-page, feature/20260817/teacher-profile-page, 008166a chore: Comet build→verify transition — all guard checks passed, 0191aac fix: redirect expired admin sessions to login, 023eb00 feat: add GET /api/v1/training/rooms/{room_id} route (+180 more)

### Community 2 - "Booking Cancellation Tests"
Cohesion: 0.03
Nodes (99): AdminContext, Base, City, Course, StudyRoom, TeacherRoom, Teacher, 获取课程详情，包含所有排课记录和教师信息。 (+91 more)

### Community 3 - "Wallet Service Tests"
Cohesion: 0.05
Nodes (78): Exception, NamedTuple, WalletRepository, BookingPaymentAlreadyProcessedError, BookingPaymentError, BookingPaymentNotFoundError, BookingPaymentSignatureError, InvalidBookingPaymentCallbackError (+70 more)

### Community 4 - "Booking Payment Tests"
Cohesion: 0.03
Nodes (76): Booking, Coupon, UserCoupon, Seat, Cleanup for unpaid booking payment holds., Cancel stale pending WeChat bookings and restore attached coupons., PaymentProviderUnavailableError, Cancel own paid future booking and refund the remaining amount to wallet. (+68 more)

### Community 5 - "Booking Payment Tests"
Cohesion: 0.03
Nodes (75): bind_wechat_phone(), bind_wechat_phone_by_sms(), get_me(), login(), logout(), Authenticate or create an app user with a WeChat mini program code., Bind a phone obtained from WeChat phone authorization code., Bind a phone to a WeChat user with SMS fallback verification. (+67 more)

### Community 6 - "Token Verification"
Cohesion: 0.03
Nodes (31): 0fc7746 chore: add teacher-profile-page OpenSpec artifacts and design doc, 206bd75 chore: check off Task 1 (models + migration) complete, 2323e70 feat: implement course detail API with TDD, 3437127 test(task-6): 课程详情+关注完整测试，实现 list course follows, 3590666 Merge branch 'feature/20260814/training-room-overview' into main, 4c94688 feat: 为 StudyRoom 添加 rating 列和 city 关系，含迁移, 7a418d3 tweak: 老师管理后端 — teachers 表扩展 + teacher_rooms 关联 + 管理端 CRUD API + C 端详情扩展与测试, 7fc110c fix: 修复课程详情API访问已迁移字段的错误 (+23 more)

### Community 7 - "Room Management Tests"
Cohesion: 0.03
Nodes (8): get_current_admin(), Shared API dependencies., Compatibility entrypoint for legacy admin route dependencies., ae1887e merge: admin RBAC dynamic settings, c623596 feat: add admin RBAC dynamic settings, columns, setting, add_admin_rbac_tables  Revision ID: b7e4a9c1d2f3 Revises: a8c3f1b2d4e5 Create Da

### Community 8 - "Teacher Management Tests"
Cohesion: 0.05
Nodes (74): admin_cancel_booking(), admin_confirm_booking(), admin_get_booking(), admin_list_bookings(), BookingAlreadyCancelledError, BookingCancellationNotAllowedError, BookingConflictError, BookingCouponUnavailableError (+66 more)

### Community 9 - "Booking Payment Tests"
Cohesion: 0.09
Nodes (69): BookingCompletionInput, CourseLesson, CourseSchedule, 课程排课表。      存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。     从 courses 表迁移出的字段：teacher_id, sc, WalletTransaction, BookingRepository, 获取课程详情 + 课时列表 + 定价信息。, BookingPaymentService (+61 more)

### Community 10 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (64): BaseModel, AdminRoleSummary, BasicSettings, EmailSettings, EmailSettingsUpdate, EmailTestRequest, EmailTestResponse, SettingsResponse (+56 more)

### Community 11 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (27): routes, routes, routes, routes, routes, routes, routes, routes (+19 more)

### Community 12 - "SMS & Captcha Tests"
Cohesion: 0.10
Nodes (71): Enum, PaymentMethod, PaymentStatus, BookingAdminListResponse, BookingAdminResponse, BookingCreate, BookingListResponse, BookingResponse (+63 more)

### Community 13 - "Booking System Core"
Cohesion: 0.05
Nodes (44): Activity, ActivityCoupon, ActivityCouponClaimError, ActivityCouponClaimResult, ActivityCouponError, ActivityCouponPublishError, Return all active activities ordered by sort_order ascending., Return paginated activity list with optional keyword search and status filter. (+36 more)

### Community 14 - "Booking Data Models"
Cohesion: 0.03
Nodes (19): 2f06520 merge: unified User-AdminUser model with user management CRUD, 9093d5e docs: archive merge-users-admin-users openspec and sync specs, c069a02 feat: unify user access control — remove user_type filtering from auth, Test creating app user defaults user_type to 'app, Test User.roles relationship returns associated AdminRole, Test creating admin user sets user_type='admin, Test same phone can't create two users, Test same username can't create two users (+11 more)

### Community 15 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (49): AdminCouponItem, buildActivityCouponFormItem(), buildActivitySearchSchemas(), buildActivityTableColumns(), buildBookingSearchSchemas(), buildBookingTableColumns(), buildRoomSearchSchemas(), buildRoomTableColumns() (+41 more)

### Community 16 - "Teacher Management Tests"
Cohesion: 0.04
Nodes (12): 14c7316 Merge branch 'implement-wechat-quick-login-phone-binding' into main, 6daf2cb feat: add username profile settings, a8157af feat: add account security settings, b3ae959 feat: implement wechat quick login, d4aefe4 登录有效期调整为 3 天, Authentication business logic service., # TODO: implement invitation relationship logic, # TODO: integrate CaptchaService when captcha is enabled (+4 more)

### Community 17 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (45): BaseSettings, Raise a sanitized error if WeChat Pay cannot be used., Return missing mini program login settings without exposing values., Return missing mini program login settings without exposing values., Whether WeChat mini program login is enabled and configured., Whether WeChat mini program login is enabled and configured., Raise a sanitized error if WeChat mini program login cannot be used., Raise a sanitized error if WeChat mini program login cannot be used. (+37 more)

### Community 18 - "Auth Service Layer"
Cohesion: 0.05
Nodes (44): RoomFollow, API tests for current-user followed study rooms., GET without follow_type defaults to 'room'., GET with follow_type=course returns empty list (current phase)., GET with invalid follow_type returns 422., POST with follow_type=course validates against courses table., POST with invalid follow_type returns 422., DELETE with follow_type=course only deletes course follows. (+36 more)

### Community 19 - "Booking System Core"
Cohesion: 0.06
Nodes (36): { apiUrl, urlPrefix }, mockAdapter, { useMock, loggerMock }, ContentTypeEnum, RequestEnum, ResultEnum, IAsyncRouteState, IScreenLockState (+28 more)

### Community 20 - "Room Management Tests"
Cohesion: 0.07
Nodes (45): AliyunSMSProvider, SMS verification code service with rate-limiting., Aliyun Dysms API client for sending SMS verification codes., SMSService, mock_redis(), Unit tests for SMS service (extended coverage)., Second send within 60 s is rejected with 429., The 11th send in one day is rejected with 429. (+37 more)

### Community 21 - "SMS & Captcha Tests"
Cohesion: 0.05
Nodes (28): Alova, result, TypeConsole, TypeOrderLarge, TypeSaleroom, TypeVisits, doCustomTimes(), pagination() (+20 more)

### Community 22 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (35): 02a1920 fix: resolve menu icons, directory paths, and hidden menu filtering (BUG-19), PageEnum, DEFAULT_CONFIG, filter(), getConfig(), TreeHelperConfig, useAsyncRoute(), useAsyncRouteStore (+27 more)

### Community 23 - "Database Config"
Cohesion: 0.05
Nodes (7): 8403348 refactor: extract admin page builders, d2114a6 merge: br-admin business refactor, routes, routes, columns, adminInfo, token

### Community 24 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (28): ADMIN_NATIVE_META, AdminPageParams, AdminPageResponse, BasicTableResult, compactQuery(), normalizePageParams(), toBasicTableResult(), AdminLoginParams (+20 more)

### Community 25 - "JWT Token Tests"
Cohesion: 0.07
Nodes (23): Notification, NotificationPreference, NotificationType, NotificationNotFoundError, NotificationService, _preference_enabled(), _validate_type(), StrEnum (+15 more)

### Community 26 - "Auth & WeChat Integration"
Cohesion: 0.08
Nodes (37): legacy_headers(), seed_users(), test_create_admin_user(), test_create_admin_user_requires_username(), test_create_app_user(), test_create_app_user_invalid_phone_format(), test_create_app_user_requires_phone(), test_create_duplicate_phone_returns_409() (+29 more)

### Community 27 - "Coupon System"
Cohesion: 0.06
Nodes (23): mock_db(), _mock_keys_result(), _mock_scalar_result(), Unit tests for AuthService., Successful registration returns TokenResponse., Registering with an existing phone raises 409., Registering with invalid SMS code raises 400., When nickname is None, a default '学习者XXXXXX' nickname is generated. (+15 more)

### Community 28 - "Teacher Management"
Cohesion: 0.08
Nodes (29): Base, get_db(), FastAPI dependency that provides an async database session., DeclarativeBase, SystemSetting, 老师与培训室/综合室的多对多关联表。      room_id 仅允许关联 study_rooms 中 room_type 为 training 或 compr, UserIdentityVerification, User (+21 more)

### Community 29 - "Data Models & Schemas"
Cohesion: 0.06
Nodes (28): CaptchaService, Aliyun Captcha 2.0 verification service., Verify a captcha token.          - If no ``ALIYUN_CAPTCHA_SCENE_ID`` is configur, Check whether a captcha token has already been consumed., _percent_encode(), Return a 6-digit random numeric string., Send a verification code to *phone*.          Workflow:         1. Validate capt, Verify an SMS code.          - If the code matches, the key is deleted (one-time (+20 more)

### Community 30 - "Miscellaneous Module"
Cohesion: 0.08
Nodes (27): get_current_admin_context(), get_current_user_id(), get_optional_current_user_id(), Extract and validate the current user ID from the access token., 有登录凭证时解析用户 ID，无凭证时返回 None。, Resolve the current administrator from Bearer or legacy admin token., AdminMenu, AdminRole (+19 more)

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
Cohesion: 0.08
Nodes (15): AdminCourseService, 获取课程详情，包含所有排课记录和教师信息。, 延期某一课时及其后续所有课时。          逻辑：         1. 从 course_lessons 表获取课时列表         2. 解析 t, 延期某一课时及其后续所有课时。          延期逻辑（时间顺延）：         1. 第 N 讲的上课时间变为第 N+1 讲原来的上课时间, 从 lesson_schedule JSON 中计算 end_date（最后一个课时日期 + 1 天）。, 根据 start_date 和 time_slots 生成至少 needed 个可用时间槽位。          按日期+时间段排序，循环扩展周次直到生成足够槽, 将 CourseSchedule 模型转换为 CourseScheduleResponse。, 根据 start_date + time_slots + course_lessons 生成 lesson_schedules 记录。          如果 (+7 more)

### Community 35 - "Booking Payment Tests"
Cohesion: 0.12
Nodes (35): ALIGNMENT_POSITIONS, appendBits(), applyMask(), bchRemainder(), bitLength(), chooseVersion(), cloneMatrix(), createCodewords() (+27 more)

### Community 36 - "Booking Domain Service"
Cohesion: 0.06
Nodes (12): 7721d2b feat: 自习室新建/编辑改为页面跳转，列表新增城市/类型列与过滤，支持环境图片与上架状态, 7d4de92 chore: 房间管理模块文案「自习室」统一替换为「学习室」, routes, admin_get_room(), admin_list_rooms(), create_room(), delete_room(), get_study_room() (+4 more)

### Community 37 - "Booking Service Tests"
Cohesion: 0.06
Nodes (35): admin_cancel_booking(), admin_confirm_booking(), admin_get_booking(), admin_list_bookings(), _build_admin_booking_response(), _cleanup_course_booking_schedule(), _create_custom_schedule_on_confirm(), 管理员确认1V1定制订单时，创建定制排课记录和课时记录。      排课数据来源：     - start_date ← booking.date     - (+27 more)

### Community 38 - "Course Management"
Cohesion: 0.13
Nodes (24): HTMLParser, _activity_coupon_to_public_response(), _activity_to_admin_response(), _admin_coupon_to_response(), claim_activity_coupon(), claim_activity_coupon_response(), _count_user_claims(), _coupon_to_response() (+16 more)

### Community 39 - "Booking Cancellation Tests"
Cohesion: 0.06
Nodes (2): routes, ParentLayout()

### Community 40 - "Miscellaneous Module"
Cohesion: 0.07
Nodes (13): ActivityCouponBase, ActivityCouponFormItem, ActivityCouponItem, ActivityCouponTemplate, ActivityFormParams, ActivityItem, ActivityListParams, ActivityListResult (+5 more)

### Community 41 - "Coupon Service Layer"
Cohesion: 0.06
Nodes (15): CourseCreateParams, CourseDetail, CourseItem, CourseListResult, CourseScheduleItem, CourseUpdateParams, LessonCreateParams, LessonItem (+7 more)

### Community 42 - "Teacher Management Tests"
Cohesion: 0.20
Nodes (27): _make_booking(), _make_coupon(), _make_course_booking(), _make_course_data(), _make_room(), _make_seat(), _make_user(), _make_user_coupon() (+19 more)

### Community 43 - "Booking Service Tests"
Cohesion: 0.08
Nodes (6): 21d2e4f feat(training): 排课时间段支持自定义新增 + 课程目录布局对齐优化, 6a2c800 fix(training): 优化课程目录布局样式和课时循环计算逻辑, 6ccaa23 feat(training): 排课管理增加课程目录显示和课时延期功能, 74d09c0 fix: 排课弹窗 UI 修复 - 新增时间段按钮移至表格下方、修复课程目录重复第N讲前缀、加大上课时间与延期按钮间隔, c6f304c fix(training): 新增时间段按钮移至表格外 + 课程目录上课时间靠近延期按钮, ce65b2f fix(training): 新增时间段按钮移至表格下方 + 去掉重叠校验

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
Nodes (23): 0be12a3 style: 学习室详情首屏标题/图片计数上移40rpx防遮挡, 14cde26 chore: archive student-review, 19b0519 feat: 评价页快捷填入、订单信息分型展示与 UI 升级, 22c8e25 tweak: admin-teacher-management 全部任务勾选完成, 24f5ae5 tweak: 老师管理前端 — br-admin 老师列表/新增/编辑页（多选所属房间）+ br-app 教师简介页接入库表数据, 36d6456 tweak: 勾选 Task 组 7-8 完成状态, 39193b1 tweak: 新增后台评价审核页与状态选项, 40a76f5 Add lazyCodeLoading Setting (+15 more)

### Community 48 - "Booking Domain Service"
Cohesion: 0.10
Nodes (10): 0072a7a 时区Bug fixed, 0f28968 Bug fixed, 3302a91 feat: add coupon package booking flow, 5c47a3c archive coupon package frontend openspec change, c66da47 updated bug-fixed.md, d14db83 Merge branch 'feature/coupon-package-frontend', auth_client(), other_auth_client() (+2 more)

### Community 49 - "Auth Service Layer"
Cohesion: 0.17
Nodes (22): _mock_scalar_one_result(), _mock_scalar_result(), _mock_scalars_result(), test_admin_get_statistics_aggregates_totals_and_active_users(), test_admin_list_transactions_joins_users_and_maps_user_fields(), test_confirm_payment_disabled_in_production(), test_create_recharge_order_rejects_unsupported_alipay(), test_create_wechat_recharge_order_returns_payment_params() (+14 more)

### Community 50 - "Booking Cancellation Tests"
Cohesion: 0.14
Nodes (23): _add_review(), 在 seed['bookings'][index] 上挂一条评价。, 种子评分 4.8 必须被真实聚合覆盖，而不是与之平均。, 5/5/4/3 → 4.25，须回写 4.3（非银行家舍入的 4.2）。, test_admin_keyword_matches_content_and_nickname(), test_admin_list_filters_by_status(), test_admin_sees_real_identity_of_anonymous_review(), test_aggregate_counts_only_approved() (+15 more)

### Community 51 - "Booking Cancellation Tests"
Cohesion: 0.40
Nodes (23): AdminCourseCreate, AdminCourseDetailResponse, AdminCourseItem, AdminCourseListResponse, AdminCourseUpdate, AdminLessonCreate, AdminLessonItem, AdminLessonUpdate (+15 more)

### Community 52 - "User & Auth Models"
Cohesion: 0.08
Nodes (8): Integration tests for Course Booking API.  注意：当前测试基础设施使用 SQLite 内存数据库，不支持 Postgr, POST /api/v1/course-bookings。, 无效 lesson_ids 返回 400。, POST /api/v1/course-bookings/{booking_id}/cancel。, GET /api/v1/courses/{id}/lessons。, TestCancelCourseBooking, TestCreateCourseBooking, TestGetCourseLessons

### Community 53 - "Booking Payment Service"
Cohesion: 0.12
Nodes (19): 982aead tweak: 新增后台评价审核接口与评分聚合回写, dcb932c tweak: 新增学员评价 C 端查询与发表接口, _approved_rating_stats(), assemble_items(), _base_conditions(), create_review(), get_summary(), list_reviews() (+11 more)

### Community 56 - "Booking Verification Tests"
Cohesion: 0.17
Nodes (19): _access_token(), _phone_user(), _temp_wechat_user(), test_bind_phone_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_sms_route_sets_refresh_cookie_and_uses_bearer_user(), test_bind_phone_with_sms_to_new_phone(), test_bind_wechat_phone_code_to_new_phone(), test_bound_user_binding_unused_phone_returns_409() (+11 more)

### Community 57 - "Booking Data Models"
Cohesion: 0.09
Nodes (23): ChangeEvent, DeepPartial, Element, ElementAttributesProperty, ElementClass, Event, ImportMetaEnv, Indexable (+15 more)

### Community 58 - "Coupon Service Layer"
Cohesion: 0.10
Nodes (12): BookingItem, BookingListParams, BookingListResult, 6d4d4c1 docs: mark all order-admin-management tasks as completed, 6ffecfa Merge branch 'main' of github.com:sin668/booking-room into main, eeafd80 Merge pull request #1 from sin668/worktree-order-admin-management, client(), db_session() (+4 more)

### Community 59 - "Auth & Login Tests"
Cohesion: 0.21
Nodes (22): _booking_now(), _booking_timezone(), _build_booking_summary(), _build_verify_url(), confirm_verification(), _create_legacy_jwt_verification_token(), _create_verification_token(), _decode_compact_verification_token() (+14 more)

### Community 60 - "Booking Service Tests"
Cohesion: 0.13
Nodes (6): 3baaa8d feat: integrate WeChat wallet payments, b15c9d7 updated .gitignore, b610482 Archive wechat payment integration OpenSpec change, e07a2b2 feat: add wallet transactions frontend, ed78866 Implement wallet recharge flow, f93686c merge: wallet transactions frontend

### Community 61 - "Teacher Management Tests"
Cohesion: 0.16
Nodes (18): 7656202 tweak: 开放评价图片上传 scope 并种入后台评价审核菜单, upload_admin_image(), _upload_image(), upload_user_image(), _apply_menu_seed(), _ensure_role_menus(), _ensure_user_role(), _get_or_create_admin() (+10 more)

### Community 63 - "Miscellaneous Module"
Cohesion: 0.16
Nodes (7): AdminUserCreate, AdminUserDetail, AdminUserListItem, AdminUserListResponse, AdminUserUpdate, Return whichever contact field (phone/username) was provided., AdminUserService

### Community 65 - "Backend Service Layer"
Cohesion: 0.19
Nodes (1): WechatAuthService

### Community 66 - "Admin Coupon Tests"
Cohesion: 0.12
Nodes (9): COURSE_WEEKDAY_NAMES, formatAmount(), formatDateSlash(), formatHourCount(), formatHourDuration(), formatMoney(), formatRelativeDay(), formatRoomMinPrice() (+1 more)

### Community 67 - "Booking Cancellation Tests"
Cohesion: 0.10
Nodes (8): 45e5bef feat: extend Course and Booking models for course booking, 7180f81 fix: resolve alembic migration cycle by assigning unique revision ID e7f8a9b0c1d2, ab174bc feat: add course booking API routes and extend booking list, b1018ae feat: add course booking page with full UI and payment flow, ca1b440 feat: add course booking schemas and service layer, ea2d28b test: add course booking service and API tests, get_course_lessons(), add course booking fields  Revision ID: a1b2c3d4e5f7 Revises: e7f8a9b0c1d2 Creat

### Community 68 - "Booking Cancellation Tests"
Cohesion: 0.14
Nodes (9): 89f0643 feat: load booking detail seat stats from backend, d4a1403 chore: archive wallet transactions frontend spec, admin_list_seats(), bulk_create_seats(), create_seat(), _get_booked_seat_ids(), get_seat_stats(), list_seats() (+1 more)

### Community 69 - "Booking Payment Tests"
Cohesion: 0.12
Nodes (10): 037946c feat: add study record frontend page, 155ef06 Ignore local worktrees, 1f38399 Merge branch 'worktree-learning-record-frontend-t5-7' into main, 3fdaf66 Update study record page and ignore agents file, 48d24c9 docs: archive learning record openspec change, 8a261c4 Refine booking verification implementation tasks, 9ba2419 fix: format month param as YYYY-MM string and fix pagination race, ed0658d docs: mark learning record tasks complete (+2 more)

### Community 70 - "Miscellaneous Module"
Cohesion: 0.15
Nodes (8): EditRecordRow, renderEditCell(), Instance, key, RetInstance, BasicColumn, BasicTableProps, TableActionType

### Community 71 - "User Security Tests"
Cohesion: 0.44
Nodes (19): ExpiredVerificationToken, InvalidVerificationToken, BookingVerificationBookingSummary, BookingVerificationConfirmResponse, BookingVerificationDetailResponse, BookingVerificationTokenRequest, BookingVerificationTokenResponse, VerifiableBookingListResponse (+11 more)

### Community 72 - "Booking Service Tests"
Cohesion: 0.14
Nodes (17): AppMiddleware, _booking_payment_reconciliation_loop(), _cleanup_unpaid_bookings_job(), health_check(), lifespan(), _order_status_check_job(), _order_status_check_loop(), _parse_schedule_status_check_time() (+9 more)

### Community 73 - "Course Management"
Cohesion: 0.11
Nodes (12): BusinessSelectOption, useAdminBusiness(), useAdminBusinessStore, CityItem, getRoomList(), RoomFormParams, RoomItem, RoomListParams (+4 more)

### Community 74 - "Booking System Core"
Cohesion: 0.28
Nodes (18): _calc_discount(), _calculate_hours(), _calculate_original_price(), _check_scope(), _ensure_aware(), _get_coupon_status(), _has_booking_history(), list_available_coupons_for_booking() (+10 more)

### Community 75 - "Token Verification"
Cohesion: 0.25
Nodes (17): AdminCouponListResponse, AdminCouponResponse, AdminCouponError, AdminCouponNotFoundError, _clean_coupon_data(), create_coupon(), delete_coupon(), _get_coupon_model() (+9 more)

### Community 76 - "Miscellaneous Module"
Cohesion: 0.13
Nodes (14): applyWechatAppId(), DEFAULT_DEV_OUTPUT_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_SERVER_ENV_PATH, fs, parseEnvFile(), path, resolveOutputDirFromArgs() (+6 more)

### Community 77 - "Auth & WeChat Integration"
Cohesion: 0.11
Nodes (1): admin_client()

### Community 78 - "Integration Tests"
Cohesion: 0.11
Nodes (15): 培训课程相关 Schema 导入与功能测试  验证以下 schema 能正确导入和使用： - TeacherResponse, TeacherBrief, Ho, StudyRoomResponse 包含 room_type 字段, RoomCreate 包含 room_type 字段，默认值 study, RoomUpdate 包含 room_type 字段，默认 None, RoomAdminResponse 包含 room_type 字段, TeacherResponse 可正确导入并实例化, course.py 中所有 schema 可正确导入, CourseResponse.parse_tags 正确解析逗号分隔字符串 (+7 more)

### Community 79 - "Notification System"
Cohesion: 0.11
Nodes (4): df06846 Implement city selection frontend, e95d205 Archive city-selection-frontend OpenSpec change, ef18031 Archive wallet-recharge-frontend change and sync specs, API tests for homepage and study room endpoints.

### Community 80 - "Course Management"
Cohesion: 0.17
Nodes (17): _booking_payment_reconciliation_loop(), _cleanup_unpaid_bookings_job(), lifespan(), _order_status_check_job(), _order_status_check_loop(), _parse_schedule_status_check_time(), _payment_reconciliation_job(), Fallback periodic runner for order status check without APScheduler. (+9 more)

### Community 81 - "Teacher & Course Models"
Cohesion: 0.12
Nodes (3): 00cde52 Implement dynamic booking verification QR flow, 39024d3 fix: stabilize booking verification QR flow, 7143168 Archive personal QR OpenSpec change

### Community 82 - "Room & Seat Management"
Cohesion: 0.16
Nodes (14): ClickOutside, DocumentHandler, FlushList, nodeList, addClass(), getBoundingClientRect(), getViewportOffset(), hasClass() (+6 more)

### Community 83 - "RBAC Service Layer"
Cohesion: 0.18
Nodes (4): _coupon(), _seed_activity_coupon(), TestActivityCouponAPI, TestActivityCouponService

### Community 84 - "Booking Cancellation Tests"
Cohesion: 0.19
Nodes (2): _payload(), TestAdminTeacherApi

### Community 86 - "Booking Service Tests"
Cohesion: 0.12
Nodes (3): 7c70899 feat: add VIP membership and coupon admin, add_membership_level  Revision ID: df6ae550899a Revises: f1a2b3c4d5e6 Create Dat, add_wallet_membership_result  Revision ID: a2b3c4d5e6f7 Revises: df6ae550899a Cr

### Community 87 - "Booking Service Tests"
Cohesion: 0.12
Nodes (17): check_and_update_order_statuses(), _mark_completed_schedules(), _process_course_booking(), _process_seat_booking(), 处理培训课程预约订单      状态转换：     - pending + today >= 第一课时日期 → confirmed，高亮当前课时     - c, 处理培训课程预约订单      状态转换：     - pending + today >= 开课日期 → confirmed，高亮当前课时（开课日期统一取第一, 处理培训课程预约订单      状态转换：     - pending + today >= 第一课时日期 → confirmed，高亮当前课时     - c, 更新课时高亮      找到当前应该高亮的课时：当前日期所在课时，     即最后一个 lesson_date <= today 的课时（当前日期落在该课时的时 (+9 more)

### Community 88 - "Booking Service Tests"
Cohesion: 0.12
Nodes (2): admin_client(), unauth_client()

### Community 89 - "Coupon System"
Cohesion: 0.12
Nodes (1): TestCreateBooking

### Community 91 - "Room & Seat Management"
Cohesion: 0.21
Nodes (16): del(), doRefreshToken(), get(), getRefreshToken(), getToken(), patch(), pendingRequests, post() (+8 more)

### Community 92 - "Auth & Login Tests"
Cohesion: 0.17
Nodes (11): 316d285 feat: add study record schemas, 5ce3f55 Merge branch 'worktree-learning-record-impl' into main, 83ccd35 feat: add study record backend (schema, service, routes), CalendarMark, StudyRecordItem, StudyRecordListResponse, StudyRecordSummaryResponse, _build_record_item() (+3 more)

### Community 93 - "Coupon System"
Cohesion: 0.16
Nodes (8): useModal(), BasicProps, ModalMethods, ModalProps, RegisterFn, UseModalReturnType, isProdMode(), getDynamicProps()

### Community 94 - "Room & Seat Management"
Cohesion: 0.17
Nodes (10): Banner, list_active_banners(), Return all active banners ordered by sort_order ascending., Unit tests for banner_service module., Seed banners for tests., Only active banners are returned., Results are ordered by sort_order ascending., Empty DB returns empty list. (+2 more)

### Community 96 - "Database Seed Data"
Cohesion: 0.14
Nodes (4): create_course(), get_course_detail(), Admin course management API routes., update_course()

### Community 97 - "Teacher Management"
Cohesion: 0.23
Nodes (14): ActivityAdminResponse, ActivityCouponAdminResponse, ActivityCouponClaimResponse, ActivityCouponClaimUserCouponResponse, ActivityCouponInput, ActivityCouponPublicResponse, ActivityCouponTemplateResponse, ActivityCreate (+6 more)

### Community 98 - "Booking Service Tests"
Cohesion: 0.13
Nodes (8): SeatBulkParams, SeatBulkResult, SeatBulkZoneConfig, SeatFormParams, SeatItem, SeatListParams, SeatStatusParams, SeatUpdateParams

### Community 99 - "Teacher Management"
Cohesion: 0.22
Nodes (2): POST /api/v1/bookings/{booking_id}/cancel, TestCancelBooking

### Community 101 - "Teacher & Course Models"
Cohesion: 0.13
Nodes (1): TestUploadAPI

### Community 102 - "Teacher Management Tests"
Cohesion: 0.13
Nodes (4): 3ec39c1 fix: resolve undefined `actions` reference in booking list page, client_with_user(), Integration tests for auth API endpoints., Create a client with get_current_user_id overridden to return FIXED_USER_ID.

### Community 104 - "Coupon Service Tests"
Cohesion: 0.13
Nodes (14): AdminWalletStatisticsResponse, AdminWalletTransactionListResponse, AdminWalletTransactionResponse, BalanceResponse, PaymentParams, PromoCodeRequest, PromoCodeResponse, RechargeOrderResponse (+6 more)

### Community 105 - "Miscellaneous Module"
Cohesion: 0.17
Nodes (9): get_storage_adapter(), ImageUploadService, _join_public_url(), LocalStorageAdapter, OssStorageAdapter, Raised when upload storage is not usable., Raised when upload storage is not usable., UploadConfigError (+1 more)

### Community 106 - "Room & Seat Management"
Cohesion: 0.21
Nodes (14): _make_base_data(), _make_custom_booking(), 订单状态定时任务（课程订单）回归测试。  背景：同一课程下固定班课排课与定制排课可能引用相同 lesson_id（不同日期）， 旧代码按 course_id +, 到达开课日期后正常转为 confirmed 并高亮第一课时。, 到达开课日期后正常转为 confirmed 并高亮第一课时。, 开课日期口径：定制订单与固定班课一致，以第一课时日期为准而非 bookings.date。      bookings.date 早于第一课时日期时，未到首课时, 定制订单未到开课日期时不得被误转 confirmed（订单 98 事故回归）。      同课程固定班课排课含相同 lesson_id 且已开课，订单通过 sc, 定制订单未到开课日期时不得被误转 confirmed（订单 98 事故回归）。      同课程固定班课排课含相同 lesson_id 且已开课，订单通过 sc (+6 more)

### Community 108 - "Integration Tests"
Cohesion: 0.27
Nodes (11): ReviewItem, AdminReviewItem, AdminReviewListResponse, 后台评价条目：永不脱敏，额外携带审核元数据。, 审核请求。目标状态限定 approved / rejected，pending 不由审核接口写入。, ReviewReplyUpdate, ReviewStatusUpdate, 后台评价审核。  可见性契约：后台永不脱敏，匿名评价同样返回真实昵称与头像，并携带匿名标记。 事务契约：不自行 commit，由 `get_db` 依赖统一提交 (+3 more)

### Community 109 - "Teacher Service Layer"
Cohesion: 0.27
Nodes (13): appRoot, assert, fs, loadModule(), main(), path, testAccountSecurity(), testAccountSecurityApi() (+5 more)

### Community 110 - "Room & Seat Service"
Cohesion: 0.30
Nodes (1): AdminMenuService

### Community 111 - "Miscellaneous Module"
Cohesion: 0.14
Nodes (8): Tests for API dependencies., Invalid token returns 401., No admin token returns 401., Wrong admin token returns 401., No credentials (no Authorization header) returns 401., Valid access token returns the user ID., TestGetCurrentAdmin, TestGetCurrentUserId

### Community 114 - "Booking Cancellation Tests"
Cohesion: 0.18
Nodes (8): debounce, ElType, HTMLElement, permission, ElType, HTMLElement, throttle, usePermission()

### Community 115 - "Auth & Login Tests"
Cohesion: 0.21
Nodes (7): DesignSettingState, useDesignSetting(), useDesignSettingStore, setupRouter(), pinia, setupStore(), store

### Community 116 - "Token Verification"
Cohesion: 0.15
Nodes (10): AdminTeacherCreate, AdminTeacherDetail, AdminTeacherListItem, AdminTeacherListResponse, AdminTeacherStatusUpdate, AdminTeacherUpdate, QualificationItem, 管理端老师管理 Pydantic schemas。 (+2 more)

### Community 117 - "Miscellaneous Module"
Cohesion: 0.31
Nodes (11): _content_type_for_extension(), generate_object_key(), _has_valid_signature(), normalize_extension(), Image upload validation and storage adapters., Raised when an uploaded file is invalid., Raised when an uploaded file is invalid., UploadObject (+3 more)

### Community 118 - "Coupon System"
Cohesion: 0.15
Nodes (8): Unit tests for study_room_service module., Seed study rooms for tests., Only open rooms are returned., Pagination works correctly., Page size is capped at MAX_PAGE_SIZE (50)., Empty DB returns zero total and empty items., seed_study_rooms(), TestListStudyRooms

### Community 119 - "Miscellaneous Module"
Cohesion: 0.23
Nodes (3): _make_user(), TestProcessVipUpgrade, TestVIPScopeFilter

### Community 120 - "Booking Payment Service"
Cohesion: 0.24
Nodes (4): ComponentProps, componentMap, EventEnum, ComponentType

### Community 122 - "User & Auth Models"
Cohesion: 0.30
Nodes (10): _course_count_map(), create_teacher(), delete_teacher(), get_teacher_detail(), list_teachers(), _load_rooms_for_teachers(), _sync_teacher_rooms(), _tags_to_db() (+2 more)

### Community 125 - "Admin Coupon Tests"
Cohesion: 0.29
Nodes (9): _create_user(), test_change_password_rejects_bad_old_password_or_mismatch(), test_change_password_updates_hash_and_revokes_refresh_tokens(), test_deactivate_account_blocks_risks(), test_deactivate_account_sets_deleted_without_removing_user(), test_security_summary_masks_sensitive_fields(), test_security_summary_returns_deleted_unbound_unverified_state(), test_submit_identity_rejects_invalid_or_different_verified() (+1 more)

### Community 128 - "Seat Management Tests"
Cohesion: 0.18
Nodes (4): AdminCouponCreateParams, AdminCouponListParams, AdminCouponListResult, AdminCouponUpdateParams

### Community 129 - "Teacher Management Tests"
Cohesion: 0.18
Nodes (5): TransactionLike, Protocol, Persist an upload object and return the public result., Persist an upload object and return the public result., StorageAdapter

### Community 130 - "Auth & Login Tests"
Cohesion: 0.25
Nodes (7): screenEnum, screenMap, sizeEnum, CreateCallbackParams, RemoveEventFn, useEventListener(), UseEventParams

### Community 131 - "Token Verification"
Cohesion: 0.29
Nodes (7): _build_wechat_client(), create_booking(), get_payment_status(), _notify_failure(), pay_pending_booking_route(), _payment_service(), wechat_notify()

### Community 132 - "Miscellaneous Module"
Cohesion: 0.35
Nodes (10): _build_wechat_client(), confirm_recharge(), create_recharge(), get_balance(), get_recharge_order(), list_transactions(), _notify_failure(), redeem_promo_code() (+2 more)

### Community 133 - "HTML Sanitizer"
Cohesion: 0.18
Nodes (7): AdminCurrentResponse, AdminLoginRequest, AdminMessageResponse, AdminPasswordUpdate, AdminPermissionItem, AdminProfileUpdate, AdminTokenResponse

### Community 134 - "User Management"
Cohesion: 0.40
Nodes (1): AdminSettingService

### Community 135 - "Miscellaneous Module"
Cohesion: 0.18
Nodes (11): get_course_detail(), get_training_room_detail(), _has_in_progress_fixed_schedule(), list_training_rooms(), 返回培训室详情，包含课程列表和教师团队。      仅 room_type 为 training 或 comprehensive 的房间有效。, 返回培训室详情，包含课程列表和教师团队。      仅 room_type 为 training 或 comprehensive 的房间有效。, 返回课程详情，含教师、教室、课时和相关课程。      3 步查询，避免 N+1：     Step 1: courses + LEFT JOIN course, 构造存在性过滤：课程至少有一条进行中（in_progress）的固定班课排课。      C 端课程列表类查询统一口径：没有进行中固定班课排课的课程不展示。 (+3 more)

### Community 137 - "Booking Payment Service"
Cohesion: 0.33
Nodes (3): _coupon_data(), _create_coupon(), TestAdminCouponService

### Community 138 - "Wallet Service Layer"
Cohesion: 0.22
Nodes (2): _payload(), TestAdminCouponApi

### Community 139 - "Booking Service Tests"
Cohesion: 0.18
Nodes (5): C 端课程展示口径测试：没有进行中固定班课排课的课程不展示。  覆盖 4 个列表类展示入口： - list_courses（培训课程列表 /pages/trai, TestHotCoursesVisibility, TestListCoursesVisibility, TestRelatedCoursesVisibility, TestTrainingRoomDetailVisibility

### Community 140 - "Booking Cancellation Tests"
Cohesion: 0.18
Nodes (6): TrainingRoomDetailResponse schema 测试, 验证嵌套 CourseResponse 的 tags 为 None 时解析为空列表, 验证缺少必填字段时抛出 ValidationError, 验证 teachers 和 courses 字段默认值为空列表, 验证嵌套的 CourseResponse 中 tags 字段可以正确解析逗号分隔字符串, TestTrainingRoomDetailResponse

### Community 141 - "User Profile Tests"
Cohesion: 0.22
Nodes (3): test_first_wechat_login_creates_phone_null_user_and_caches_session_key(), test_repeat_wechat_login_reuses_bound_user(), _token_sub()

### Community 142 - "Teacher Management Tests"
Cohesion: 0.18
Nodes (10): get_course_detail(), _get_first_schedule_for_courses(), get_training_room_detail(), list_courses(), list_training_rooms(), 返回培训室详情，包含课程列表和教师团队。      仅 room_type 为 training 或 comprehensive 的房间有效。, 返回分页课程列表，附带教室名和教师信息。      单条查询：JOIN StudyRoom + CourseSchedule + Teacher。, 返回课程详情，含教师、教室、课时和相关课程。      3 步查询，避免 N+1：     Step 1: courses + LEFT JOIN course (+2 more)

### Community 144 - "Deployment Config"
Cohesion: 0.27
Nodes (9): check_and_update_order_statuses(), _process_course_booking(), _process_seat_booking(), 订单状态定时转换服务  定时检查并更新所有已支付的待开始/进行中订单状态： - 自习室座位预约：pending → confirmed（当前时间 >= 开始时间, 处理培训课程预约订单      状态转换：     - pending + today >= 开课日期 → confirmed，高亮当前课时（1V1 定制订单开, 更新课时高亮      找到当前应该高亮的课时：当前日期所在课时，     即最后一个 lesson_date <= today 的课时（当前日期落在该课时的时, 定时检查并更新所有已支付的待开始/进行中订单状态。      返回: {"seat_started": N, "seat_completed": N, "cou, 处理自习室座位预约订单      状态转换：     - pending + now >= date+start_time → confirmed（进行中） (+1 more)

### Community 145 - "Miscellaneous Module"
Cohesion: 0.27
Nodes (6): setupCustomComponents(), setupDirectives(), setupGlobalMethods(), naive, setupNaive(), setupNaiveDiscreteApi()

### Community 146 - "Project Documentation"
Cohesion: 0.22
Nodes (9): SeatAdminResponse, SeatBulkCreate, SeatBulkZoneConfig, SeatCreate, SeatResponse, SeatStatsResponse, SeatStatusUpdate, SeatUpdate (+1 more)

### Community 147 - "Deployment Config"
Cohesion: 0.33
Nodes (1): AdminRoleService

### Community 149 - "Miscellaneous Module"
Cohesion: 0.20
Nodes (1): TestSeatAPI

### Community 150 - "Teacher Management"
Cohesion: 0.36
Nodes (8): _create_user(), test_get_current_user_profile_returns_username_fields(), test_update_nickname_does_not_require_username_cooldown(), test_update_profile_rejects_protected_fields(), test_update_username_rejects_cooldown(), test_update_username_rejects_duplicate(), test_update_username_rejects_invalid_format(), test_update_username_success_sets_cooldown_timestamp()

### Community 152 - "RBAC Data Models"
Cohesion: 0.20
Nodes (9): GlobConfig, GlobEnvConfig, IBodySetting, ICrumbsSetting, IHeaderSetting, IMenuSetting, IMultiTabsSetting, LocalConfig (+1 more)

### Community 153 - "Token Verification"
Cohesion: 0.20
Nodes (9): ComponentElRef, ComponentRef, ElRef, EmitType, Fn, LabelValueOptions, PromiseFn, RefType (+1 more)

### Community 154 - "Room & Seat Management"
Cohesion: 0.28
Nodes (3): adminRequest(), confirmVerification(), inspectVerificationToken()

### Community 156 - "Integration Tests"
Cohesion: 0.31
Nodes (4): useTimeoutFn(), useTimeoutRef(), useBreakpoint(), useDesignSetting()

### Community 158 - "Database Migrations"
Cohesion: 0.22
Nodes (7): COURSE_CATEGORY_LABELS, COURSE_CATEGORY_OPTIONS, COURSE_STATUS_TAGS, BusinessTagConfig, EDUCATION_OPTIONS, ROOM_TYPE_LABELS, TEACHER_STATUS_TAGS

### Community 159 - "Miscellaneous Module"
Cohesion: 0.25
Nodes (7): AdminMenuBase, AdminMenuCreate, AdminMenuNode, AdminMenuRoute, AdminMenuRouteMeta, AdminMenuUpdate, ComponentOption

### Community 160 - "Miscellaneous Module"
Cohesion: 0.22
Nodes (8): exportMatch, fs, getCallMatch, paramMatch, path, source, trainingApiPath, urlMatch

### Community 161 - "Miscellaneous Module"
Cohesion: 0.39
Nodes (7): followRoom(), getFollowedRooms(), isRoomFollowed(), normalizeRoom(), setFollowedRooms(), syncFollowedRooms(), unfollowRoom()

### Community 162 - "Coupon Service Layer"
Cohesion: 0.22
Nodes (4): BasicSettings, EmailSettings, nativeMeta, SystemSettings

### Community 163 - "Room & Seat Management"
Cohesion: 0.33
Nodes (5): 固定班课下单：预约日期/开课日期取已预约第一课时日期，时段复制排课记录。, 创建固定班课完整数据：教室/用户/课程/老师/排课/2 个课时及课时排课。, 第一课时在未来 → 待开始；预约日期=第一课时日期；时段复制排课；不改排课表。, 第一课时日期 <= 今天 → 进行中（confirmed）。, TestFixedBookingStartDateAndTimeSlots

### Community 164 - "Teacher Management"
Cohesion: 0.22
Nodes (5): get_current_user_id returns the user UUID from a valid access token., get_current_user_id raises 401 for a blacklisted token., get_current_user_id raises 401 when token type is not 'access'., get_current_user_id raises 401 for an expired token., TestGetCurrentUserId

### Community 165 - "User Management"
Cohesion: 0.33
Nodes (5): getAppEnvConfig(), getCommonStoragePrefix(), getEnv(), getStorageShortName(), warn()

### Community 166 - "Notification System"
Cohesion: 0.29
Nodes (6): Run migrations in 'offline' mode.      Configures the context with just a URL an, Run migrations in 'online' mode with async engine., Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online()

### Community 167 - "RBAC Data Models"
Cohesion: 0.25
Nodes (2): CountTo, withInstall()

### Community 168 - "Data Models & Schemas"
Cohesion: 0.39
Nodes (5): create_coupon(), delete_coupon(), _service_error(), toggle_coupon_status(), update_coupon()

### Community 170 - "Teacher & Course Models"
Cohesion: 0.36
Nodes (5): create_teacher(), get_teacher_detail(), Admin teacher management API routes., toggle_teacher_status(), update_teacher()

### Community 171 - "Token Verification"
Cohesion: 0.32
Nodes (3): list_notifications(), mark_all_notifications_read(), _parse_notification_type()

### Community 172 - "Token Verification"
Cohesion: 0.29
Nodes (7): AdminRoleBase, AdminRoleCreate, AdminRoleListResponse, AdminRoleMenusResponse, AdminRoleMenuUpdate, AdminRoleResponse, AdminRoleUpdate

### Community 173 - "Token Verification"
Cohesion: 0.32
Nodes (6): assertContains(), assertMatches(), fs, path, read(), root

### Community 174 - "Course Management"
Cohesion: 0.29
Nodes (7): appRoot, assert, fs, loadModule(), main(), path, vm

### Community 175 - "Miscellaneous Module"
Cohesion: 0.25
Nodes (7): failures, fs, path, profilePath, requiredLinks, source, statsCardMatch

### Community 176 - "Teacher Management"
Cohesion: 0.46
Nodes (7): followCourse(), getFollowedCourses(), isCourseFollowed(), normalizeCourse(), setFollowedCourses(), syncFollowedCourses(), unfollowCourse()

### Community 178 - "Booking Cancellation Tests"
Cohesion: 0.43
Nodes (6): _policy(), test_exact_24_hours_charges_20_percent(), test_exact_2_hours_charges_50_percent(), test_exact_48_hours_charges_10_percent(), test_non_round_amount_keeps_penalty_and_refund_balanced(), test_over_48_hours_full_refund()

### Community 179 - "Token Verification"
Cohesion: 0.25
Nodes (2): auth_client(), seed_teacher_follow_data()

### Community 180 - "Project Documentation"
Cohesion: 0.25
Nodes (1): TestTrainingRoomsAPI

### Community 185 - "Redis Connection"
Cohesion: 0.52
Nodes (5): createUploadError(), normalizeErrorMessage(), parseUploadResponse(), uploadImage(), uploadOnce()

### Community 186 - "Payment & Wallet"
Cohesion: 0.33
Nodes (3): formatBookingTimeRange(), formatTimeSlots(), WEEKDAY_NAMES

### Community 187 - "Token Verification"
Cohesion: 0.38
Nodes (4): a67a5e8 fix: 修正交易列表路由路径为 /transactions, fb3958c feat: 新增管理端钱包路由（含 CSV 导出）, _admin_wallet_base_conditions(), export_transactions()

### Community 188 - "Miscellaneous Module"
Cohesion: 0.33
Nodes (6): close_redis(), get_redis(), init_redis(), Initialize and return the singleton Redis connection., Close the Redis connection., FastAPI dependency that provides an async Redis connection.

### Community 190 - "Miscellaneous Module"
Cohesion: 0.57
Nodes (6): base64url_encode(), CompactVerificationPayload, create_compact_verification_token(), decode_compact_verification_token(), ensure_utc(), sign_compact_token()

### Community 191 - "Admin RBAC System"
Cohesion: 0.29
Nodes (3): AdminReviewItem, AdminReviewListParams, ReviewStatusParams

### Community 193 - "Teacher Management"
Cohesion: 0.52
Nodes (6): followTeacher(), getFollowedTeachers(), isTeacherFollowed(), normalizeTeacher(), setFollowedTeachers(), unfollowTeacher()

### Community 194 - "Database Seed Data"
Cohesion: 0.57
Nodes (6): _china_now_naive(), _get_or_create_demo_user(), seed_all(), seed_coupons(), _seed_notification_preferences(), seed_notifications()

### Community 195 - "Wallet Service Layer"
Cohesion: 0.29
Nodes (6): Base upload error with a user-safe message., Base upload error with a user-safe message., Raised when storage fails., Raised when storage fails., UploadError, UploadStorageError

### Community 198 - "Auth & Login Tests"
Cohesion: 0.29
Nodes (4): send-code with captcha_token passes it through., When SMSService raises HTTPException, it propagates., Successful send-code returns 200., TestSendCode

### Community 199 - "Booking Service Tests"
Cohesion: 0.29
Nodes (4): GET /me without auth returns 401., GET /me with valid auth returns user info., GET /me with auth but user not in DB returns 404., TestGetMeAuth

### Community 200 - "Community 200"
Cohesion: 0.29
Nodes (1): TestCourseModel

### Community 201 - "Community 201"
Cohesion: 0.29
Nodes (1): seed_teacher_data()

### Community 202 - "Community 202"
Cohesion: 0.29
Nodes (1): TestCoursesAPI

### Community 206 - "Community 206"
Cohesion: 0.67
Nodes (5): _get_review_or_404(), list_reviews(), _to_admin_items(), update_reply(), update_status()

### Community 207 - "Community 207"
Cohesion: 0.40
Nodes (5): Seed seat data for existing study rooms., Generate seats for a study room. Returns number of seats created., Seed seats for all rooms. Returns total seats created., seed_all_rooms(), seed_seats_for_room()

### Community 210 - "Community 210"
Cohesion: 0.33
Nodes (2): Integration tests for city APIs., TestCityAPI

### Community 211 - "Community 211"
Cohesion: 0.33
Nodes (2): Unit tests for the City model., TestCityModel

### Community 214 - "Community 214"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 215 - "Community 215"
Cohesion: 0.40
Nodes (3): copy, ElType, HTMLElement

### Community 216 - "Community 216"
Cohesion: 0.60
Nodes (3): can_cancel_paid_booking(), has_booking_started(), should_mark_booking_completed()

### Community 217 - "Community 217"
Cohesion: 0.50
Nodes (3): PermissionsEnum, ActionItem, PopConfirm

### Community 219 - "Community 219"
Cohesion: 0.60
Nodes (4): AvailableCouponForBookingResponse, AvailableCouponsForBookingListResponse, CouponBaseResponse, CouponResponse

### Community 220 - "Community 220"
Cohesion: 0.70
Nodes (4): booking_now(), booking_start_datetime(), calculate_cancellation_policy(), CancellationPolicyResult

### Community 221 - "Community 221"
Cohesion: 0.60
Nodes (3): createPaymentStatusError(), getPaymentStatus(), pollPaymentStatus()

### Community 222 - "Community 222"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 223 - "Community 223"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 224 - "Community 224"
Cohesion: 0.40
Nodes (4): columns, ListData, sexMap, statusMap

### Community 225 - "Community 225"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_component_options_and_invalid_component(), test_dynamic_routes_exclude_buttons_and_disabled_nodes(), test_menu_tree_crud_and_delete_child_conflict()

### Community 226 - "Community 226"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_email_test_requires_complete_config(), test_settings_read_masks_smtp_password(), test_update_email_without_password_preserves_existing_secret()

### Community 227 - "Community 227"
Cohesion: 0.40
Nodes (5): _admin_context(), audit_client(), 持有全部评价权限的真实管理员上下文，用于断言 reviewed_by。, 只有查看权限的非超管，用于断言审核/回复被 403 拦截。, view_only_client()

### Community 228 - "Community 228"
Cohesion: 0.40
Nodes (2): StudyRoom.room_type 字段验证。, TestStudyRoomRoomType

### Community 229 - "Community 229"
Cohesion: 0.40
Nodes (1): TestTeacherModel

### Community 230 - "Community 230"
Cohesion: 0.40
Nodes (3): NOTIFICATION_TYPE_CONFIGS, NOTIFICATION_TYPE_MAP, NOTIFICATION_TYPES

### Community 231 - "Community 231"
Cohesion: 0.50
Nodes (3): _generate_username(), add_username_updated_at  Adds users.username_updated_at and backfills existing u, upgrade()

### Community 235 - "Community 235"
Cohesion: 0.50
Nodes (3): BOOKING_STATUS_LABELS, BOOKING_TABS, SEAT_ZONE_LABELS

### Community 236 - "Community 236"
Cohesion: 0.50
Nodes (3): draggable, ElType, HTMLElement

### Community 237 - "Community 237"
Cohesion: 0.83
Nodes (2): setLoading(), useAsync()

### Community 238 - "Community 238"
Cohesion: 0.50
Nodes (1): key

### Community 239 - "Community 239"
Cohesion: 0.50
Nodes (1): useCityStore

### Community 242 - "Community 242"
Cohesion: 0.50
Nodes (3): check_and_update_schedule_statuses(), 排课状态定时任务  定时扫描课程排课列表中状态为"进行中"（in_progress）的排课记录： - 当前日期 > 课程结束日期（end_date）→ sche, 定时扫描"进行中"的排课记录，将当前日期已超过结课日期的记录标记为已完成。      返回: {"total_scanned": N, "schedule_co

### Community 245 - "Community 245"
Cohesion: 0.83
Nodes (3): legacy_headers(), test_role_crud_duplicate_and_assigned_delete_conflict(), test_role_menu_assignment_updates_auth_permissions()

### Community 247 - "Community 247"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17

### Community 248 - "Community 248"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:

### Community 249 - "Community 249"
Cohesion: 0.50
Nodes (1): create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create

### Community 250 - "Community 250"
Cohesion: 0.50
Nodes (1): create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat

### Community 251 - "Community 251"
Cohesion: 0.50
Nodes (1): booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:

### Community 252 - "Community 252"
Cohesion: 0.50
Nodes (1): create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea

### Community 253 - "Community 253"
Cohesion: 0.50
Nodes (1): create_wallet_table  Revision ID: 28a1f4af90df Revises: b3a7c9d2e4f1 Create Date

### Community 254 - "Community 254"
Cohesion: 0.50
Nodes (1): update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:

### Community 255 - "Community 255"
Cohesion: 0.50
Nodes (1): add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf

### Community 256 - "Community 256"
Cohesion: 0.50
Nodes (1): add_wechat_payment_fields  Revision ID: a8c3f1b2d4e5 Revises: 7c9d2e4f6a1b Creat

### Community 257 - "Community 257"
Cohesion: 0.50
Nodes (1): add_booking_payment_fields  Adds payment-related fields to bookings table: - pay

### Community 258 - "Community 258"
Cohesion: 0.50
Nodes (1): add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c

### Community 259 - "Community 259"
Cohesion: 0.50
Nodes (1): add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create

### Community 260 - "Community 260"
Cohesion: 0.50
Nodes (1): add booking cancellation audit fields  Revision ID: b8c9d0e1f2a3 Revises: a7b8c9

### Community 261 - "Community 261"
Cohesion: 0.50
Nodes (1): add room follows  Revision ID: c9d0e1f2a3b4 Revises: b8c9d0e1f2a3 Create Date: 2

### Community 262 - "Community 262"
Cohesion: 0.50
Nodes (1): add_activity_coupon_campaign  Revision ID: f1a2b3c4d5e6 Revises: d0e1f2a3b4c5 Cr

### Community 263 - "Community 263"
Cohesion: 0.50
Nodes (1): create_schedule_HotCourseItem  Revision ID: fccf087f0f34 Revises: e3f4a5b6c7d8 C

### Community 264 - "Community 264"
Cohesion: 0.50
Nodes (1): create_course_table  Revision ID: c84abd1322d4 Revises: c4d5e6f7a8b9 Create Date

### Community 265 - "Community 265"
Cohesion: 0.50
Nodes (1): add teacher bio and student_count  Revision ID: e7f8a9b0c1d2 Revises: c84abd1322

### Community 266 - "Community 266"
Cohesion: 0.50
Nodes (1): add full_custom_price to courses  Revision ID: 5d8e53290b12 Revises: a1b2c3d4e5f

### Community 267 - "Community 267"
Cohesion: 0.50
Nodes (1): create course_schedules table and migrate fields from courses  Revision ID: b1c2

### Community 268 - "Community 268"
Cohesion: 0.50
Nodes (1): extend teachers table and create teacher_rooms  Revision ID: d3e4f5a6b7c8 Revise

### Community 269 - "Community 269"
Cohesion: 0.50
Nodes (1): add time_slots and teacher_id to bookings  Revision ID: b9c0d1e2f3a4 Revises: e8

### Community 270 - "Community 270"
Cohesion: 0.50
Nodes (1): add_schedule_status_to_course_schedules  Revision ID: d4e5f6a7b8c9 Revises: b9c0

### Community 271 - "Community 271"
Cohesion: 0.50
Nodes (1): add_schedule_id_to_bookings  Revision ID: e5f6a7b8c9d0 Revises: d4e5f6a7b8c9 Cre

### Community 272 - "Community 272"
Cohesion: 0.67
Nodes (1): AppMiddleware

### Community 273 - "Community 273"
Cohesion: 0.67
Nodes (3): health_check(), Health check endpoint., Health check endpoint.

### Community 274 - "Community 274"
Cohesion: 0.67
Nodes (1): __APP_INFO__

### Community 275 - "Community 275"
Cohesion: 0.67
Nodes (2): PAYMENT_TERMINAL_FAILURE_STATUSES, WALLET_TRANSACTION_STATUS_LABELS

### Community 276 - "Community 276"
Cohesion: 0.67
Nodes (1): WindowSizeOptions

### Community 278 - "Community 278"
Cohesion: 0.67
Nodes (1): Battery

### Community 280 - "Community 280"
Cohesion: 0.67
Nodes (2): CourseResponse, 将逗号分隔字符串解析为列表，None 或空字符串返回空列表

### Community 281 - "Community 281"
Cohesion: 0.67
Nodes (1): TeacherDetailResponse

### Community 282 - "Community 282"
Cohesion: 0.67
Nodes (2): get_active_cities(), Return active cities ordered by sort_order ascending.

### Community 283 - "Community 283"
Cohesion: 0.67
Nodes (2): appThemeList, setting

### Community 286 - "Community 286"
Cohesion: 0.67
Nodes (1): Tests for admin wallet API routes.

### Community 288 - "Community 288"
Cohesion: 0.67
Nodes (1): TestStudyRoomAPI

### Community 293 - "Community 293"
Cohesion: 1.00
Nodes (1): BasicProps

### Community 294 - "Community 294"
Cohesion: 1.00
Nodes (1): websiteConfig

### Community 296 - "Community 296"
Cohesion: 1.00
Nodes (1): directive

### Community 297 - "Community 297"
Cohesion: 1.00
Nodes (1): RoleEnum

### Community 302 - "Community 302"
Cohesion: 1.00
Nodes (1): Database repository adapters.

### Community 304 - "Community 304"
Cohesion: 1.00
Nodes (1): TeacherCourseItem

### Community 305 - "Community 305"
Cohesion: 1.00
Nodes (1): animates

### Community 307 - "Community 307"
Cohesion: 1.00
Nodes (2): auth_client(), conftest 已把 get_current_admin 覆盖为 None（放行全部后台权限）。

### Community 308 - "Community 308"
Cohesion: 1.00
Nodes (2): 课程与老师带种子评分（模拟 seed 数据），下挂若干已完成订单。, seed()

### Community 311 - "Community 311"
Cohesion: 1.00
Nodes (1): DynamicProps

### Community 313 - "Community 313"
Cohesion: 1.00
Nodes (1): params

### Community 317 - "Community 317"
Cohesion: 1.00
Nodes (1): Application use case orchestration layer.

## Knowledge Gaps
- **562 isolated node(s):** `Base exception for booking operations.`, `Create a booking with conflict detection.      Note: For MVP, conflict detection`, `List bookings for the current user with pagination.`, `Get a booking detail. Only own bookings are visible.`, `Cancel own paid future booking and refund the remaining amount to wallet.` (+557 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Booking Cancellation Tests`** (2 nodes): `routes`, `ParentLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Backend Service Layer`** (1 nodes): `WechatAuthService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth & WeChat Integration`** (1 nodes): `admin_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Cancellation Tests`** (2 nodes): `_payload()`, `TestAdminTeacherApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (2 nodes): `admin_client()`, `unauth_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coupon System`** (1 nodes): `TestCreateBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher Management`** (2 nodes): `POST /api/v1/bookings/{booking_id}/cancel`, `TestCancelBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher & Course Models`** (1 nodes): `TestUploadAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Room & Seat Service`** (1 nodes): `AdminMenuService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `User Management`** (1 nodes): `AdminSettingService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Wallet Service Layer`** (2 nodes): `_payload()`, `TestAdminCouponApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Deployment Config`** (1 nodes): `AdminRoleService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (1 nodes): `TestSeatAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `RBAC Data Models`** (2 nodes): `CountTo`, `withInstall()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Token Verification`** (2 nodes): `auth_client()`, `seed_teacher_follow_data()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Project Documentation`** (1 nodes): `TestTrainingRoomsAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 200`** (1 nodes): `TestCourseModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 201`** (1 nodes): `seed_teacher_data()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 202`** (1 nodes): `TestCoursesAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 210`** (2 nodes): `Integration tests for city APIs.`, `TestCityAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 211`** (2 nodes): `Unit tests for the City model.`, `TestCityModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 228`** (2 nodes): `StudyRoom.room_type 字段验证。`, `TestStudyRoomRoomType`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (1 nodes): `TestTeacherModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 237`** (2 nodes): `setLoading()`, `useAsync()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 238`** (1 nodes): `key`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 239`** (1 nodes): `useCityStore`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 247`** (1 nodes): `create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 248`** (1 nodes): `create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 249`** (1 nodes): `create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 250`** (1 nodes): `create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 251`** (1 nodes): `booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 252`** (1 nodes): `create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 253`** (1 nodes): `create_wallet_table  Revision ID: 28a1f4af90df Revises: b3a7c9d2e4f1 Create Date`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 254`** (1 nodes): `update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 255`** (1 nodes): `add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 256`** (1 nodes): `add_wechat_payment_fields  Revision ID: a8c3f1b2d4e5 Revises: 7c9d2e4f6a1b Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 257`** (1 nodes): `add_booking_payment_fields  Adds payment-related fields to bookings table: - pay`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 258`** (1 nodes): `add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 259`** (1 nodes): `add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 260`** (1 nodes): `add booking cancellation audit fields  Revision ID: b8c9d0e1f2a3 Revises: a7b8c9`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 261`** (1 nodes): `add room follows  Revision ID: c9d0e1f2a3b4 Revises: b8c9d0e1f2a3 Create Date: 2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 262`** (1 nodes): `add_activity_coupon_campaign  Revision ID: f1a2b3c4d5e6 Revises: d0e1f2a3b4c5 Cr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 263`** (1 nodes): `create_schedule_HotCourseItem  Revision ID: fccf087f0f34 Revises: e3f4a5b6c7d8 C`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 264`** (1 nodes): `create_course_table  Revision ID: c84abd1322d4 Revises: c4d5e6f7a8b9 Create Date`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 265`** (1 nodes): `add teacher bio and student_count  Revision ID: e7f8a9b0c1d2 Revises: c84abd1322`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 266`** (1 nodes): `add full_custom_price to courses  Revision ID: 5d8e53290b12 Revises: a1b2c3d4e5f`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 267`** (1 nodes): `create course_schedules table and migrate fields from courses  Revision ID: b1c2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 268`** (1 nodes): `extend teachers table and create teacher_rooms  Revision ID: d3e4f5a6b7c8 Revise`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 269`** (1 nodes): `add time_slots and teacher_id to bookings  Revision ID: b9c0d1e2f3a4 Revises: e8`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 270`** (1 nodes): `add_schedule_status_to_course_schedules  Revision ID: d4e5f6a7b8c9 Revises: b9c0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 271`** (1 nodes): `add_schedule_id_to_bookings  Revision ID: e5f6a7b8c9d0 Revises: d4e5f6a7b8c9 Cre`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 272`** (1 nodes): `AppMiddleware`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 274`** (1 nodes): `__APP_INFO__`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 275`** (2 nodes): `PAYMENT_TERMINAL_FAILURE_STATUSES`, `WALLET_TRANSACTION_STATUS_LABELS`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 276`** (1 nodes): `WindowSizeOptions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 278`** (1 nodes): `Battery`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 280`** (2 nodes): `CourseResponse`, `将逗号分隔字符串解析为列表，None 或空字符串返回空列表`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 281`** (1 nodes): `TeacherDetailResponse`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 282`** (2 nodes): `get_active_cities()`, `Return active cities ordered by sort_order ascending.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 283`** (2 nodes): `appThemeList`, `setting`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 286`** (1 nodes): `Tests for admin wallet API routes.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 288`** (1 nodes): `TestStudyRoomAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 293`** (1 nodes): `BasicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 294`** (1 nodes): `websiteConfig`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 296`** (1 nodes): `directive`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 297`** (1 nodes): `RoleEnum`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 302`** (1 nodes): `Database repository adapters.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 304`** (1 nodes): `TeacherCourseItem`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 305`** (1 nodes): `animates`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 307`** (2 nodes): `auth_client()`, `conftest 已把 get_current_admin 覆盖为 None（放行全部后台权限）。`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 308`** (2 nodes): `课程与老师带种子评分（模拟 seed 数据），下挂若干已完成订单。`, `seed()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 311`** (1 nodes): `DynamicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 313`** (1 nodes): `params`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 317`** (1 nodes): `Application use case orchestration layer.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Auth & Login Tests` to `Teacher Management Tests`, `Miscellaneous Module`, `Booking Payment Tests`, `Data Models & Schemas`, `Room Management Tests`, `Miscellaneous Module`, `Miscellaneous Module`, `Wallet Service Layer`, `Teacher Management Tests`, `Booking Payment Tests`, `Auth & WeChat Integration`, `Wallet Service Tests`, `Backend Service Layer`, `Coupon System`, `Teacher Management`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `StudyRoom` connect `Booking Cancellation Tests` to `Token Verification`, `Teacher Management`, `Payment & Wallet`, `Booking Cancellation Tests`, `Wallet Service Tests`, `Booking Payment Tests`, `Booking Payment Tests`, `SMS & Captcha Tests`, `User Security Tests`, `Community 207`, `Booking Cancellation Tests`, `Teacher Management`, `Coupon System`, `User & Auth Models`, `Notification System`, `Community 288`, `Auth Service Layer`, `Miscellaneous Module`, `Auth & Login Tests`, `Auth & Login Tests`, `Coupon System`, `Community 202`, `Project Documentation`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `Booking` connect `Booking Payment Tests` to `Booking Service Tests`, `Booking Cancellation Tests`, `Wallet Service Tests`, `Booking Payment Tests`, `SMS & Captcha Tests`, `Booking Service Tests`, `Booking Service Tests`, `Teacher Management`, `Miscellaneous Module`, `User Security Tests`, `Auth & WeChat Integration`, `Auth & Login Tests`, `Backend Service Layer`, `Teacher Management`, `Coupon System`, `Miscellaneous Module`, `Auth & Login Tests`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 244 inferred relationships involving `StudyRoom` (e.g. with `Base` and `City`) actually correct?**
  _`StudyRoom` has 244 INFERRED edges - model-reasoned connections that need verification._
- **Are the 212 inferred relationships involving `Settings` (e.g. with `AdminAuthService` and `AuthService`) actually correct?**
  _`Settings` has 212 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Base exception for booking operations.`, `Create a booking with conflict detection.      Note: For MVP, conflict detection`, `List bookings for the current user with pagination.` to the rest of the system?**
  _562 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Booking Service Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.03395151163913841 - nodes in this community are weakly interconnected._
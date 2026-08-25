# Graph Report - .  (2026-08-25)

## Corpus Check
- Large corpus: 1012 files · ~453,540 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 5150 nodes · 10747 edges · 217 communities detected
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 2485 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output
- Edge kinds: contains: 2672 · uses: 2485 · MODIFIES: 1177 · ON_BRANCH: 1000 · calls: 954 · method: 676 · rationale_for: 546 · PARENT_OF: 328 · imports_from: 324 · inherits: 295 · imports: 283 · re_exports: 7


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 1012 · Candidates: 1392
- Excluded: 896 untracked · 88603 ignored · 0 sensitive · 24 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `e78ec5c`
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

### Community 17 - "Auth & Login Tests"
Cohesion: 0.05
Nodes (28): resultSuccess(), resultPageSuccess(), pagination(), doCustomTimes(), requestParams, result, menusList, TypeVisits (+20 more)

### Community 35 - "Booking Payment Tests"
Cohesion: 0.08
Nodes (7): token, adminInfo, routes, routes, columns, 8403348 refactor: extract admin page builders, d2114a6 merge: br-admin business refactor

### Community 11 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (46): AdminCouponItem, WalletTransactionItem, WalletStatistics, buildActivitySearchSchemas(), buildActivityTableColumns(), buildActivityCouponFormItem(), validateActivityCoupons(), columns (+38 more)

### Community 43 - "Booking Service Tests"
Cohesion: 0.07
Nodes (12): get_active_cities(), Return active cities ordered by sort_order ascending., TestStudyRoomAPI, API tests for homepage and study room endpoints., 0fad7a7 fix: resolve API 307 redirect and 404 caused by trailing slash inconsistency, bc0df21 docs: archive coupon management admin spec, da88def feat: update branding, logo and tabBar styling for br-app, df06846 Implement city selection frontend (+4 more)

### Community 37 - "Booking Service Tests"
Cohesion: 0.07
Nodes (13): ActivityItem, ActivityListResult, ActivityFormParams, ActivityUpdateParams, ActivityListParams, ActivityCouponBase, ActivityCouponTemplate, ActivityCouponItem (+5 more)

### Community 19 - "Booking System Core"
Cohesion: 0.04
Nodes (31): BookingItem, BookingListResult, BookingListParams, ADMIN_NATIVE_META, AdminPageParams, AdminPageResponse, BasicTableResult, compactQuery() (+23 more)

### Community 29 - "Data Models & Schemas"
Cohesion: 0.06
Nodes (14): AdminCouponListResult, AdminCouponCreateParams, AdminCouponUpdateParams, AdminCouponListParams, add_coupon_models  Revision ID: b3a7c9d2e4f1 Revises: 985785a787d8 Create Date:, seed_room_seat(), auth_client(), other_auth_client() (+6 more)

### Community 38 - "Course Management"
Cohesion: 0.07
Nodes (15): CourseScheduleItem, CourseItem, CourseListResult, CourseCreateParams, CourseUpdateParams, TeacherBrief, CourseDetail, LessonItem (+7 more)

### Community 74 - "Booking System Core"
Cohesion: 0.11
Nodes (12): RoomType, RoomItem, RoomListResult, RoomFormParams, RoomUpdateParams, RoomStatusParams, RoomListParams, CityItem (+4 more)

### Community 97 - "Teacher Management"
Cohesion: 0.13
Nodes (8): SeatItem, SeatFormParams, SeatBulkZoneConfig, SeatBulkParams, SeatBulkResult, SeatUpdateParams, SeatStatusParams, SeatListParams

### Community 96 - "Database Seed Data"
Cohesion: 0.16
Nodes (11): adminMenus(), LayoutMap, generateRoutes(), generateDynamicRoutes(), asyncImportRoute(), constantRouterIcon, Component, AppRouteRecordRaw (+3 more)

### Community 156 - "Integration Tests"
Cohesion: 0.22
Nodes (4): BasicSettings, EmailSettings, SystemSettings, nativeMeta

### Community 14 - "Booking Data Models"
Cohesion: 0.06
Nodes (36): AdminUserInfo, getUserInfo(), login(), WalletListParams, WalletTransactionListResponse, WalletListResult, normalizeParams(), buildQuery() (+28 more)

### Community 161 - "Miscellaneous Module"
Cohesion: 0.25
Nodes (2): CountTo, withInstall()

### Community 39 - "Booking Cancellation Tests"
Cohesion: 0.09
Nodes (15): DATE_TYPE, dateItemType, Props, useForm(), EmitType, UseFormActionContext, basicProps, FormSchema (+7 more)

### Community 222 - "Community 222"
Cohesion: 0.50
Nodes (1): key

### Community 40 - "Miscellaneous Module"
Cohesion: 0.13
Nodes (19): UseFormValuesContext, PaginationProps, is(), isFunction(), isDef(), isUnDef(), isObject(), isDate() (+11 more)

### Community 93 - "Coupon System"
Cohesion: 0.16
Nodes (8): useModal(), ModalMethods, ModalProps, RegisterFn, UseModalReturnType, BasicProps, isProdMode(), getDynamicProps()

### Community 73 - "Course Management"
Cohesion: 0.15
Nodes (8): renderEditCell(), EditRecordRow, key, Instance, RetInstance, BasicColumn, TableActionType, BasicTableProps

### Community 112 - "Teacher Management"
Cohesion: 0.24
Nodes (4): EventEnum, componentMap, ComponentProps, ComponentType

### Community 204 - "Community 204"
Cohesion: 0.50
Nodes (3): ActionItem, PopConfirm, PermissionsEnum

### Community 13 - "Booking System Core"
Cohesion: 0.06
Nodes (54): websiteConfig, _get_first_schedule_for_courses(), list_training_rooms(), get_training_room_detail(), list_courses(), get_course_detail(), 04745c9 chore: archive course-booking, 0e940af feat(course): 所有课程页统一格式化上课时间并新增开课时间行 (+46 more)

### Community 82 - "Room & Seat Management"
Cohesion: 0.16
Nodes (14): DocumentHandler, FlushList, nodeList, ClickOutside, ViewportOffsetResult, getBoundingClientRect(), trim(), hasClass() (+6 more)

### Community 202 - "Community 202"
Cohesion: 0.40
Nodes (3): ElType, HTMLElement, copy

### Community 108 - "Integration Tests"
Cohesion: 0.18
Nodes (8): ElType, HTMLElement, debounce, permission, ElType, HTMLElement, throttle, usePermission()

### Community 220 - "Community 220"
Cohesion: 0.50
Nodes (3): ElType, HTMLElement, draggable

### Community 262 - "Community 262"
Cohesion: 1.00
Nodes (1): directive

### Community 123 - "RBAC Service Layer"
Cohesion: 0.25
Nodes (7): sizeEnum, screenEnum, screenMap, CreateCallbackParams, RemoveEventFn, UseEventParams, useEventListener()

### Community 32 - "Auth & Login Tests"
Cohesion: 0.08
Nodes (23): PageEnum, useProjectSetting(), RouteLocationRawEx, ErrorPageRoute, RedirectRoute, ErrorPage(), whitePathList, createRouterGuards() (+15 more)

### Community 263 - "Community 263"
Cohesion: 1.00
Nodes (1): RoleEnum

### Community 150 - "Teacher Management"
Cohesion: 0.31
Nodes (4): useTimeoutFn(), useTimeoutRef(), useBreakpoint(), useDesignSetting()

### Community 249 - "Community 249"
Cohesion: 0.67
Nodes (1): WindowSizeOptions

### Community 221 - "Community 221"
Cohesion: 0.83
Nodes (2): setLoading(), useAsync()

### Community 251 - "Community 251"
Cohesion: 0.67
Nodes (1): Battery

### Community 9 - "Booking Payment Tests"
Cohesion: 0.05
Nodes (27): Layout(), routes, routes, routes, routes, routes, routes, routes (+19 more)

### Community 109 - "Teacher Service Layer"
Cohesion: 0.21
Nodes (7): setupRouter(), store, setupStore(), DesignSettingState, useDesignSettingStore, useDesignSetting(), pinia

### Community 136 - "Room & Seat Models"
Cohesion: 0.27
Nodes (6): setupCustomComponents(), setupDirectives(), setupGlobalMethods(), naive, setupNaive(), setupNaiveDiscreteApi()

### Community 36 - "Booking Domain Service"
Cohesion: 0.06
Nodes (2): ParentLayout(), routes

### Community 20 - "Room Management Tests"
Cohesion: 0.04
Nodes (15): routes, add environment_images to study_rooms  Revision ID: c2d3e4f5a6b7 Revises: b1c2d3, list_study_rooms(), get_study_room(), admin_list_rooms(), admin_get_room(), create_room(), update_room() (+7 more)

### Community 269 - "Community 269"
Cohesion: 1.00
Nodes (1): animates

### Community 254 - "Community 254"
Cohesion: 0.67
Nodes (2): appThemeList, setting

### Community 2 - "Booking Cancellation Tests"
Cohesion: 0.03
Nodes (8): setting, columns, add_admin_rbac_tables  Revision ID: b7e4a9c1d2f3 Revises: a8c3f1b2d4e5 Create Da, _upload_image(), upload_admin_image(), upload_user_image(), ae1887e merge: admin RBAC dynamic settings, c623596 feat: add admin RBAC dynamic settings

### Community 273 - "Community 273"
Cohesion: 1.00
Nodes (1): params

### Community 159 - "Miscellaneous Module"
Cohesion: 0.33
Nodes (5): getCommonStoragePrefix(), getStorageShortName(), getAppEnvConfig(), getEnv(), warn()

### Community 152 - "RBAC Data Models"
Cohesion: 0.22
Nodes (7): BusinessTagConfig, COURSE_STATUS_TAGS, COURSE_CATEGORY_OPTIONS, COURSE_CATEGORY_LABELS, TEACHER_STATUS_TAGS, EDUCATION_OPTIONS, ROOM_TYPE_LABELS

### Community 209 - "Community 209"
Cohesion: 0.40
Nodes (4): ListData, sexMap, statusMap, columns

### Community 208 - "Community 208"
Cohesion: 0.40
Nodes (4): ListData, sexMap, statusMap, columns

### Community 210 - "Community 210"
Cohesion: 0.40
Nodes (4): ListData, sexMap, statusMap, columns

### Community 86 - "Booking Service Tests"
Cohesion: 0.12
Nodes (3): add_membership_level  Revision ID: df6ae550899a Revises: f1a2b3c4d5e6 Create Dat, add_wallet_membership_result  Revision ID: a2b3c4d5e6f7 Revises: df6ae550899a Cr, 7c70899 feat: add VIP membership and coupon admin

### Community 261 - "Community 261"
Cohesion: 1.00
Nodes (1): BasicProps

### Community 201 - "Community 201"
Cohesion: 0.40
Nodes (4): ListData, sexMap, statusMap, columns

### Community 7 - "Room Management Tests"
Cohesion: 0.03
Nodes (23): merge_users_phase1_extend  Extend users table with admin-user fields and rename, # NOTE: admin_user_roles FK changes are deferred to Phase 2,, merge_users_phase2_data  Migrate data from admin_users into users table and upda, merge_users_phase3_drop  Drop admin_users table now that data has been merged in, client_with_user(), Integration tests for auth API endpoints., Create a client with get_current_user_id overridden to return FIXED_USER_ID., test_app_user_defaults_user_type_to_app() (+15 more)

### Community 72 - "Booking Service Tests"
Cohesion: 0.11
Nodes (7): 0e90f58 fix: 排课更新后强制刷新列表数据, 25778f9 fix: 发布设置区块去除多余空白间隔，课程排课查询强制绕过缓存, 31949f1 docs: 记录 BUG-25 排课保存后列表不刷新(Alova GET 内存缓存), 8438d36 fix: 排课列表保存后不刷新 + time_slots 改为周几格式, 9068db6 fix: 基本信息移除课程状态，发布设置移除课程状态标签, ae205e4 refactor: 排课时间段选择器改为日期×时间段网格布局, c06c18f fix: 修复排课更新后列表数据不刷新的问题

### Community 64 - "Deployment Config"
Cohesion: 0.11
Nodes (6): 0605022 fix: 课程编辑页与列表页在原 tab 内互相跳转，不再新开标签页, 107108e tweak: 课程上课时间统一格式化并在培训室详情显示（截断+悬停提示）, 3d61e55 fix: 注册 NFormItemGi 和 NPopconfirm 组件，恢复发布设置区块, 3f1e632 fix: 课程编辑页布局调整 - 热门/排序/状态移入基本信息，课时编辑显示分钟单位，删除按钮可见, 5f8183b fix: 课程编辑页返回改用 router.back 方案，修复保存成功后误报保存失败及导航异常, 8e1b05e feat: 保存课程后返回列表页，课程列表分类显示中文名称

### Community 53 - "Booking Payment Service"
Cohesion: 0.10
Nodes (12): _admin_wallet_base_conditions(), export_transactions(), Tests for admin wallet API routes., 06c38d2 fix: 优化管理端钱包流水展示, 13f942b fix: 更新用户端钱包退款文案, 7979a96 Complete admin wallet backend, 90b89ef docs: document admin wallet finance api, 99ced87 feat(admin): add wallet frontend routing api (+4 more)

### Community 145 - "Miscellaneous Module"
Cohesion: 0.20
Nodes (9): ProjectSettingState, IBodySetting, IHeaderSetting, IMenuSetting, ICrumbsSetting, IMultiTabsSetting, GlobConfig, LocalConfig (+1 more)

### Community 57 - "Booking Data Models"
Cohesion: 0.09
Nodes (23): PropType, VueNode, Writable, InResult, Nullable, NonNullable, Recordable, ReadonlyRecordable (+15 more)

### Community 146 - "Project Documentation"
Cohesion: 0.20
Nodes (9): Fn, PromiseFn, RefType, LabelValueOptions, EmitType, TargetContext, ComponentElRef, ComponentRef (+1 more)

### Community 271 - "Community 271"
Cohesion: 1.00
Nodes (1): DynamicProps

### Community 248 - "Community 248"
Cohesion: 0.67
Nodes (1): __APP_INFO__

### Community 76 - "Miscellaneous Module"
Cohesion: 0.13
Nodes (14): fs, path, DEFAULT_OUTPUT_DIR, DEFAULT_DEV_OUTPUT_DIR, DEFAULT_SERVER_ENV_PATH, parseEnvFile(), resolveWechatAppId(), applyWechatAppId() (+6 more)

### Community 103 - "Data Model Tests"
Cohesion: 0.27
Nodes (13): assert, fs, path, vm, appRoot, loadModule(), testFormatters(), testAccountSecurity() (+5 more)

### Community 167 - "RBAC Data Models"
Cohesion: 0.32
Nodes (6): fs, path, root, read(), assertContains(), assertMatches()

### Community 168 - "Data Models & Schemas"
Cohesion: 0.29
Nodes (7): assert, fs, path, vm, appRoot, loadModule(), main()

### Community 107 - "Auth & WeChat Integration"
Cohesion: 0.17
Nodes (11): fs, path, profilePath, source, requiredLinks, statsCardMatch, failures, 5187776 feat: show wallet balance on booking confirmation (+3 more)

### Community 154 - "Room & Seat Management"
Cohesion: 0.22
Nodes (8): fs, path, trainingApiPath, source, exportMatch, paramMatch, urlMatch, getCallMatch

### Community 12 - "SMS & Captcha Tests"
Cohesion: 0.06
Nodes (44): 037946c feat: add study record frontend page, 061bda0 feat: 实现 seat-select 页面 viewMode 只读查看模式, 074aeae feat: add message notification APIs and app UI, 11f3494 docs: archive unify-user-access openspec and sync specs to main, 155ef06 Ignore local worktrees, 1580995 fix: disable past booking time slots, 1f38399 Merge branch 'worktree-learning-record-frontend-t5-7' into main, 247eff9 docs: update notification frontend backend spec (+36 more)

### Community 148 - "Miscellaneous Module"
Cohesion: 0.28
Nodes (3): adminRequest(), inspectVerificationToken(), confirmVerification()

### Community 63 - "Miscellaneous Module"
Cohesion: 0.10
Nodes (5): add_booking_payment_fields  Adds payment-related fields to bookings table: - pay, cleanup_unpaid_bookings(), Cleanup for unpaid booking payment holds., Cancel stale pending WeChat bookings and restore attached coupons., 6288c60 feat: add booking wechat payment flow

### Community 80 - "Course Management"
Cohesion: 0.14
Nodes (9): add_course_description_and_room_follow_type  Revision ID: c4d5e6f7a8b9 Revises:, _to_followed_room(), list_followed_rooms(), follow_room(), 3437127 test(task-6): 课程详情+关注完整测试，实现 list course follows, 794936b Add persisted study room follows, 84887cb fix: resolve Alembic migration revision ID conflict and fix inactive course test, a581dc1 feat: extend room_follow with follow_type for course follows (+1 more)

### Community 70 - "Miscellaneous Module"
Cohesion: 0.14
Nodes (9): _room_exists(), _get_booked_seat_ids(), list_seats(), get_seat_stats(), admin_list_seats(), create_seat(), bulk_create_seats(), 89f0643 feat: load booking detail seat stats from backend (+1 more)

### Community 23 - "Database Config"
Cohesion: 0.06
Nodes (20): add room_type, teachers, courses  Revision ID: b3c4d5e6f7a8 Revises: a2b3c4d5e6f, create_training_table  Revision ID: f61f3ab400f5 Revises: b3c4d5e6f7a8 Create Da, TeacherResponse, TeacherRoomItem, get_teacher_detail(), TDD 测试：验证 Teacher、Course 模型及 StudyRoom.room_type 字段存在。  此测试先于实现编写，应先失败（RED），再通过实, seed_teacher_data(), 0fc7746 chore: add teacher-profile-page OpenSpec artifacts and design doc (+12 more)

### Community 44 - "Coupon Service Tests"
Cohesion: 0.07
Nodes (14): add_rating_to_study_rooms  Revision ID: e3f4a5b6c7d8 Revises: f61f3ab400f5 Creat, TrainingRoomDetailResponse schema 单元测试  验证培训室详情响应 schema 的字段构造、默认值及嵌套 tags 解析。, 023eb00 feat: add GET /api/v1/training/rooms/{room_id} route, 2c762c3 docs: add GET /api/v1/training/rooms/{room_id} API documentation, 2fe2097 feat: add get_training_room_detail to training_service (TDD green phase), 3590666 Merge branch 'feature/20260814/training-room-overview' into main, 4150deb test: add failing tests for get_training_room_detail (TDD red phase), 4c94688 feat: 为 StudyRoom 添加 rating 列和 city 关系，含迁移 (+6 more)

### Community 175 - "Miscellaneous Module"
Cohesion: 0.52
Nodes (5): normalizeErrorMessage(), createUploadError(), parseUploadResponse(), uploadOnce(), uploadImage()

### Community 8 - "Teacher Management Tests"
Cohesion: 0.04
Nodes (41): add account security  Revision ID: d0e1f2a3b4c5 Revises: c9d0e1f2a3b4 Create Dat, get_me(), update_me(), get_account_security(), change_password(), submit_identity_verification(), deactivate_account(), Get the current authenticated user's info. (+33 more)

### Community 71 - "User Security Tests"
Cohesion: 0.14
Nodes (8): create_wallet_table  Revision ID: 28a1f4af90df Revises: b3a7c9d2e4f1 Create Date, 3baaa8d feat: integrate WeChat wallet payments, b15c9d7 updated .gitignore, b610482 Archive wechat payment integration OpenSpec change, c66da47 updated bug-fixed.md, e07a2b2 feat: add wallet transactions frontend, ed78866 Implement wallet recharge flow, f93686c merge: wallet transactions frontend

### Community 219 - "Community 219"
Cohesion: 0.50
Nodes (3): BOOKING_TABS, BOOKING_STATUS_LABELS, SEAT_ZONE_LABELS

### Community 47 - "Booking Verification Service"
Cohesion: 0.08
Nodes (14): WALLET_TRANSACTION_STATUS_LABELS, PAYMENT_TERMINAL_FAILURE_STATUSES, Application use case orchestration layer., BookingUseCases, Database repository adapters., 645d7d5 refactor: extract booking repository conflict query, 69fc18d refactor: extract wallet display rules, 9ea74c1 test: align admin booking detail fixture assertion (+6 more)

### Community 1 - "Teacher Management Tests"
Cohesion: 0.07
Nodes (103): 008166a chore: Comet build→verify transition — all guard checks passed, 0191aac fix: redirect expired admin sessions to login, 0719233 fix: reconcile pending wechat bookings, 071ac5f chore: add implementation plan for training-room-overview, 0b53f3b 优化UI, 0bd9a4a fix: make phone and username uniqueness checks global (Task 3), 10b5060 feat: add training course list page, 182fcdd chore: checkoff Task 9 in plan (+95 more)

### Community 81 - "Teacher & Course Models"
Cohesion: 0.12
Nodes (3): 00cde52 Implement dynamic booking verification QR flow, 39024d3 fix: stabilize booking verification QR flow, 7143168 Archive personal QR OpenSpec change

### Community 58 - "Coupon Service Layer"
Cohesion: 0.09
Nodes (5): 02b3b93 feat: add course-detail page with all sections (7.1-7.8), 148395b feat(br-app): add course detail navigation from training list page, 8e4fbeb chore: archive training-room-overview change & add course-detail-page proposal, c2f96bd fix: add course_lessons table to migration & align frontend field names, d84d0ce feat: 培训室概况页课程列表UI优化 - 后端: HotCourseItem 添加 schedule/tags 字段, TrainingRoomResponse 添加 rating - 后端: training_service 传递 schedule/tags 到热门课程 - 前端: training/index.vue 培训室名称可点击跳转到概况页 - 前端: 课程项添加时钟图标+培训时间+热销/新课/名师标签 - 前端: booking/detail.vue 课程列表同步优化UI样式

### Community 169 - "Room & Seat Models"
Cohesion: 0.46
Nodes (7): normalizeCourse(), getFollowedCourses(), setFollowedCourses(), syncFollowedCourses(), isCourseFollowed(), followCourse(), unfollowCourse()

### Community 155 - "JWT Token Tests"
Cohesion: 0.39
Nodes (7): normalizeRoom(), getFollowedRooms(), setFollowedRooms(), syncFollowedRooms(), isRoomFollowed(), followRoom(), unfollowRoom()

### Community 179 - "Token Verification"
Cohesion: 0.52
Nodes (6): normalizeTeacher(), getFollowedTeachers(), setFollowedTeachers(), isTeacherFollowed(), followTeacher(), unfollowTeacher()

### Community 207 - "Community 207"
Cohesion: 0.60
Nodes (3): createPaymentStatusError(), getPaymentStatus(), pollPaymentStatus()

### Community 223 - "Community 223"
Cohesion: 0.50
Nodes (1): useCityStore

### Community 90 - "Database Config"
Cohesion: 0.15
Nodes (7): toFiniteNumber(), formatMoney(), formatAmount(), formatRoomMinPrice(), formatHourDuration(), formatHourCount(), COURSE_WEEKDAY_NAMES

### Community 215 - "Community 215"
Cohesion: 0.40
Nodes (3): NOTIFICATION_TYPE_CONFIGS, NOTIFICATION_TYPES, NOTIFICATION_TYPE_MAP

### Community 49 - "Auth Service Layer"
Cohesion: 0.15
Nodes (25): RS_BLOCKS_L, ALIGNMENT_POSITIONS, EXP_TABLE, LOG_TABLE, gfMul(), polyMul(), rsGenerator(), rsRemainder() (+17 more)

### Community 147 - "Deployment Config"
Cohesion: 0.29
Nodes (10): setModule(), drawFinder(), drawAlignment(), drawFunctionPatterns(), reserveFormatAreas(), bchRemainder(), bitLength(), drawFormatInfo() (+2 more)

### Community 91 - "Room & Seat Management"
Cohesion: 0.21
Nodes (16): pendingRequests, getToken(), getRefreshToken(), setToken(), setRefreshToken(), removeToken(), removeRefreshToken(), resolvePendingRequests() (+8 more)

### Community 160 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (6): run_migrations_offline(), run_async_migrations(), run_migrations_online(), Run migrations in 'offline' mode.      Configures the context with just a URL an, Run migrations in 'online' mode with async engine., Run migrations in 'online' mode.

### Community 229 - "Community 229"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17

### Community 230 - "Community 230"
Cohesion: 0.50
Nodes (1): create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:

### Community 231 - "Community 231"
Cohesion: 0.50
Nodes (1): create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create

### Community 232 - "Community 232"
Cohesion: 0.50
Nodes (1): create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat

### Community 122 - "User & Auth Models"
Cohesion: 0.18
Nodes (4): booking seat table  Revision ID: 2c56c35e7075 Revises: de5e1f080747 Create Date:, create_booking_order_table  Revision ID: 985785a787d8 Revises: 2c56c35e7075 Crea, Tests for API dependencies., a75fe60 优化前端UI页面

### Community 233 - "Community 233"
Cohesion: 0.50
Nodes (1): update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:

### Community 234 - "Community 234"
Cohesion: 0.50
Nodes (1): add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf

### Community 235 - "Community 235"
Cohesion: 0.50
Nodes (1): add_wechat_payment_fields  Revision ID: a8c3f1b2d4e5 Revises: 7c9d2e4f6a1b Creat

### Community 216 - "Community 216"
Cohesion: 0.50
Nodes (3): _generate_username(), upgrade(), add_username_updated_at  Adds users.username_updated_at and backfills existing u

### Community 236 - "Community 236"
Cohesion: 0.50
Nodes (1): add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c

### Community 237 - "Community 237"
Cohesion: 0.50
Nodes (1): add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create

### Community 238 - "Community 238"
Cohesion: 0.50
Nodes (1): add booking cancellation audit fields  Revision ID: b8c9d0e1f2a3 Revises: a7b8c9

### Community 239 - "Community 239"
Cohesion: 0.50
Nodes (1): add room follows  Revision ID: c9d0e1f2a3b4 Revises: b8c9d0e1f2a3 Create Date: 2

### Community 240 - "Community 240"
Cohesion: 0.50
Nodes (1): add_activity_coupon_campaign  Revision ID: f1a2b3c4d5e6 Revises: d0e1f2a3b4c5 Cr

### Community 241 - "Community 241"
Cohesion: 0.50
Nodes (1): create_schedule_HotCourseItem  Revision ID: fccf087f0f34 Revises: e3f4a5b6c7d8 C

### Community 242 - "Community 242"
Cohesion: 0.50
Nodes (1): create_course_table  Revision ID: c84abd1322d4 Revises: c4d5e6f7a8b9 Create Date

### Community 243 - "Community 243"
Cohesion: 0.50
Nodes (1): add teacher bio and student_count  Revision ID: e7f8a9b0c1d2 Revises: c84abd1322

### Community 244 - "Community 244"
Cohesion: 0.50
Nodes (1): add course booking fields  Revision ID: a1b2c3d4e5f7 Revises: e7f8a9b0c1d2 Creat

### Community 245 - "Community 245"
Cohesion: 0.50
Nodes (1): add full_custom_price to courses  Revision ID: 5d8e53290b12 Revises: a1b2c3d4e5f

### Community 246 - "Community 246"
Cohesion: 0.50
Nodes (1): create course_schedules table and migrate fields from courses  Revision ID: b1c2

### Community 247 - "Community 247"
Cohesion: 0.50
Nodes (1): extend teachers table and create teacher_rooms  Revision ID: d3e4f5a6b7c8 Revise

### Community 121 - "Wallet Service Layer"
Cohesion: 0.20
Nodes (9): get_current_user_id(), get_optional_current_user_id(), get_current_admin_context(), get_current_admin(), Shared API dependencies., Extract and validate the current user ID from the access token., 有登录凭证时解析用户 ID，无凭证时返回 None。, Resolve the current administrator from Bearer or legacy admin token. (+1 more)

### Community 6 - "Token Verification"
Cohesion: 0.04
Nodes (55): AdminContext, Course, RoomFollow, 管理端老师管理 API 测试。  覆盖：列表分页/筛选、详情、新增、编辑、删除（含排课拒绝）、状态切换、 room_type 校验、权限控制。, qualifications/teaching_tags 为空时入库为 NULL，详情接口应返回 200 且容忍为空列表。, 发布设置：新增时可指定 status，编辑时可通过 PUT 修改 status。, C 端培训室详情的教师团队与课程讲师过滤未激活老师。, test_list_followed_rooms_default_type_is_room() (+47 more)

### Community 162 - "Coupon Service Layer"
Cohesion: 0.39
Nodes (5): _service_error(), create_coupon(), update_coupon(), toggle_coupon_status(), delete_coupon()

### Community 41 - "Coupon Service Layer"
Cohesion: 0.07
Nodes (5): get_course_detail(), create_course(), update_course(), Admin course management API routes., AdminCourseService

### Community 164 - "Teacher Management"
Cohesion: 0.36
Nodes (5): get_teacher_detail(), create_teacher(), update_teacher(), toggle_teacher_status(), Admin teacher management API routes.

### Community 15 - "Auth & Login Tests"
Cohesion: 0.08
Nodes (37): _set_refresh_token_cookie(), send_code(), register(), login(), wechat_login(), bind_wechat_phone(), bind_wechat_phone_by_sms(), refresh() (+29 more)

### Community 124 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (7): _build_wechat_client(), _payment_service(), _notify_failure(), create_booking(), wechat_notify(), get_payment_status(), pay_pending_booking_route()

### Community 224 - "Community 224"
Cohesion: 0.50
Nodes (1): get_course_lessons()

### Community 4 - "Booking Payment Tests"
Cohesion: 0.11
Nodes (70): 获取课程详情 + 课时列表 + 定价信息。, BookingCompletionInput, Base, Booking, CourseLesson, CourseSchedule, 课程排课表。      存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。     从 courses 表迁移出的字段：teacher_id, sc, WalletTransaction (+62 more)

### Community 165 - "User Management"
Cohesion: 0.32
Nodes (3): _parse_notification_type(), list_notifications(), mark_all_notifications_read()

### Community 92 - "Auth & Login Tests"
Cohesion: 0.17
Nodes (11): CalendarMark, StudyRecordSummaryResponse, StudyRecordItem, StudyRecordListResponse, _calculate_streak_days(), _build_record_item(), get_monthly_summary(), list_study_records() (+3 more)

### Community 125 - "Admin Coupon Tests"
Cohesion: 0.35
Nodes (10): _build_wechat_client(), _service(), _notify_failure(), create_recharge(), get_recharge_order(), list_transactions(), wechat_notify(), confirm_recharge() (+2 more)

### Community 16 - "Teacher Management Tests"
Cohesion: 0.07
Nodes (39): Settings, BaseSettings, Application settings loaded from environment variables and .env file., Return missing setting names without exposing configured values., Whether WeChat Pay is enabled and has all required configuration., Raise a sanitized error if WeChat Pay cannot be used., Return missing mini program login settings without exposing values., Whether WeChat mini program login is enabled and configured. (+31 more)

### Community 24 - "Auth & Login Tests"
Cohesion: 0.07
Nodes (31): Base, DeclarativeBase, get_db(), FastAPI dependency that provides an async database session., SystemSetting, User, UserIdentityVerification, _create_access_token() (+23 more)

### Community 176 - "Teacher Management"
Cohesion: 0.33
Nodes (6): init_redis(), close_redis(), get_redis(), Initialize and return the singleton Redis connection., Close the Redis connection., FastAPI dependency that provides an async Redis connection.

### Community 203 - "Community 203"
Cohesion: 0.60
Nodes (3): has_booking_started(), can_cancel_paid_booking(), should_mark_booking_completed()

### Community 22 - "Auth & Login Tests"
Cohesion: 0.14
Nodes (47): InvalidVerificationToken, ValueError, ExpiredVerificationToken, CompactVerificationPayload, create_compact_verification_token(), decode_compact_verification_token(), sign_compact_token(), base64url_encode() (+39 more)

### Community 133 - "HTML Sanitizer"
Cohesion: 0.20
Nodes (4): TransactionLike, Protocol, StorageAdapter, Persist an upload object and return the public result.

### Community 75 - "Token Verification"
Cohesion: 0.15
Nodes (15): _cleanup_unpaid_bookings_job(), _booking_payment_reconciliation_loop(), lifespan(), Fallback periodic runner for environments without APScheduler., Application lifespan: startup and shutdown events., event_loop(), db_session(), client() (+7 more)

### Community 52 - "User & Auth Models"
Cohesion: 0.13
Nodes (11): AppMiddleware, health_check(), Health check endpoint., WechatPayClient, _json_dumps(), _parse_response(), Small API v3 client that owns WeChat Pay protocol details., Create a JSAPI prepay order and return its prepay_id. (+3 more)

### Community 10 - "Auth & Login Tests"
Cohesion: 0.06
Nodes (44): Activity, ActivityCoupon, Coupon, UserCoupon, ActivityCouponError, ActivityCouponClaimError, ActivityCouponPublishError, ActivityCouponClaimResult (+36 more)

### Community 33 - "Auth & WeChat Integration"
Cohesion: 0.10
Nodes (21): AdminMenu, AdminRole, AdminAuthService, MenuSeed, test_admin_login_with_phone(), test_admin_login_missing_both_fields(), Admin login with phone (no username) returns 200., Admin login with neither phone nor username returns 422. (+13 more)

### Community 94 - "Room & Seat Management"
Cohesion: 0.17
Nodes (10): Banner, list_active_banners(), Return all active banners ordered by sort_order ascending., seed_banners(), TestListActiveBanners, Unit tests for banner_service module., Seed banners for tests., Only active banners are returned. (+2 more)

### Community 83 - "RBAC Service Layer"
Cohesion: 0.15
Nodes (17): PaymentMethod, str, Enum, PaymentStatus, PaymentMethodEnum, PaymentStatusEnum, SeatBrief, RoomBrief (+9 more)

### Community 0 - "Booking Service Tests"
Cohesion: 0.02
Nodes (79): City, Teacher, TeacherRoom, 老师与培训室/综合室的多对多关联表。      room_id 仅允许关联 study_rooms 中 room_type 为 training 或 compr, 按老师统计关联课程数（去重 course_id）。, 校验房间存在且 room_type 为培训室或综合室。, 删除老师。返回 "ok"；不存在返回 "not_found"；存在排课返回 "has_schedules"。, 获取教师详情，包含关联课程列表和课时计数；停用教师对 C 端不可见 (+71 more)

### Community 25 - "JWT Token Tests"
Cohesion: 0.07
Nodes (23): NotificationType, StrEnum, Notification, NotificationPreference, NotificationNotFoundError, _validate_type(), _preference_enabled(), NotificationService (+15 more)

### Community 3 - "Wallet Service Tests"
Cohesion: 0.04
Nodes (51): Seat, StudyRoom, Return set of seat_ids that have overlapping confirmed bookings., seed_seats_for_room(), seed_all_rooms(), Seed seat data for existing study rooms., Generate seats for a study room. Returns number of seats created., Seed seats for all rooms. Returns total seats created. (+43 more)

### Community 18 - "Auth Service Layer"
Cohesion: 0.15
Nodes (47): WalletRepository, Booking direct payment orchestration., Base exception for booking payment operations., Service for booking WeChat payment creation and callbacks., Create a WeChat JSAPI payment order for a pending booking., Verify a WeChat callback and mark a booking payment as paid once., Query due pending WeChat bookings and advance their payment state., Exception (+39 more)

### Community 65 - "Backend Service Layer"
Cohesion: 0.17
Nodes (18): ActivityResponse, ActivityCouponInput, ActivityCouponTemplateResponse, ActivityCouponAdminResponse, ActivityCouponPublicResponse, ActivityCreate, ActivityUpdate, ActivityAdminResponse (+10 more)

### Community 5 - "Booking Payment Tests"
Cohesion: 0.04
Nodes (62): BaseModel, AdminLoginRequest, AdminTokenResponse, AdminPermissionItem, AdminCurrentResponse, AdminProfileUpdate, AdminPasswordUpdate, AdminMessageResponse (+54 more)

### Community 153 - "Token Verification"
Cohesion: 0.25
Nodes (7): AdminMenuBase, AdminMenuCreate, AdminMenuUpdate, AdminMenuNode, AdminMenuRouteMeta, AdminMenuRoute, ComponentOption

### Community 166 - "Notification System"
Cohesion: 0.29
Nodes (7): AdminRoleBase, AdminRoleCreate, AdminRoleUpdate, AdminRoleResponse, AdminRoleListResponse, AdminRoleMenusResponse, AdminRoleMenuUpdate

### Community 110 - "Room & Seat Service"
Cohesion: 0.15
Nodes (10): QualificationItem, AdminTeacherCreate, AdminTeacherUpdate, AdminTeacherStatusUpdate, AdminTeacherListItem, AdminTeacherListResponse, TeacherRoomBrief, AdminTeacherDetail (+2 more)

### Community 48 - "Booking Domain Service"
Cohesion: 0.13
Nodes (11): AdminUserListParams, AdminUserListItem, AdminUserListResponse, AdminUserCreate, AdminUserUpdate, AdminUserDetail, AdminResetPassword, AdminToggleStatus (+3 more)

### Community 205 - "Community 205"
Cohesion: 0.60
Nodes (4): CouponBaseResponse, CouponResponse, AvailableCouponForBookingResponse, AvailableCouponsForBookingListResponse

### Community 59 - "Auth & Login Tests"
Cohesion: 0.19
Nodes (20): AdminCouponCreate, AdminCouponUpdate, AdminCouponResponse, AdminCouponListResponse, AdminCouponStatusUpdate, _now_for_db(), AdminCouponError, AdminCouponNotFoundError (+12 more)

### Community 137 - "Booking Payment Service"
Cohesion: 0.22
Nodes (9): SeatResponse, SeatWithAvailabilityResponse, SeatStatsResponse, SeatCreate, SeatBulkZoneConfig, SeatBulkCreate, SeatUpdate, SeatStatusUpdate (+1 more)

### Community 253 - "Community 253"
Cohesion: 0.67
Nodes (1): TeacherDetailResponse

### Community 99 - "Teacher Management"
Cohesion: 0.13
Nodes (14): RechargeRequest, PaymentParams, RechargeResponse, RechargeOrderResponse, BalanceResponse, WalletTransactionResponse, WalletTransactionListResponse, PromoCodeRequest (+6 more)

### Community 54 - "Teacher Management Tests"
Cohesion: 0.21
Nodes (22): sanitize_activity_content(), _now(), _normalize_activity_coupon_time(), _coupon_to_response(), _admin_coupon_to_response(), _activity_to_admin_response(), _load_activity_coupon_rows(), _replace_activity_coupons() (+14 more)

### Community 135 - "Miscellaneous Module"
Cohesion: 0.24
Nodes (2): _RichTextSanitizer, HTMLParser

### Community 104 - "Coupon Service Tests"
Cohesion: 0.30
Nodes (1): AdminMenuService

### Community 139 - "Booking Service Tests"
Cohesion: 0.33
Nodes (1): AdminRoleService

### Community 126 - "Admin Coupon Tests"
Cohesion: 0.40
Nodes (1): AdminSettingService

### Community 114 - "Booking Cancellation Tests"
Cohesion: 0.30
Nodes (10): _tags_to_db(), _course_count_map(), _validate_room_ids(), _sync_teacher_rooms(), _load_rooms_for_teachers(), list_teachers(), get_teacher_detail(), create_teacher() (+2 more)

### Community 206 - "Community 206"
Cohesion: 0.70
Nodes (4): CancellationPolicyResult, booking_start_datetime(), booking_now(), calculate_cancellation_policy()

### Community 66 - "Admin Coupon Tests"
Cohesion: 0.21
Nodes (7): BookingPaymentError, WechatOpenIdRequiredError, BookingPaymentNotFoundError, InvalidBookingPaymentCallbackError, BookingPaymentSignatureError, BookingPaymentAlreadyProcessedError, BookingPaymentService

### Community 28 - "Teacher Management"
Cohesion: 0.06
Nodes (29): CaptchaService, Aliyun Captcha 2.0 verification service., Verify a captcha token.          - If no ``ALIYUN_CAPTCHA_SCENE_ID`` is configur, Check whether a captcha token has already been consumed., _percent_encode(), _sign_request(), URL-encode per Aliyun signature spec (uppercase hex, encode / += etc)., Sign Aliyun API request parameters with HMAC-SHA1. (+21 more)

### Community 50 - "Booking Cancellation Tests"
Cohesion: 0.22
Nodes (23): CouponError, CouponNotFoundError, CouponUnavailableError, BookingCouponCalculation, NamedTuple, _now(), _now_for_db(), _ensure_aware() (+15 more)

### Community 115 - "Auth & Login Tests"
Cohesion: 0.17
Nodes (6): Create a long-lived refresh token with a unique jti.          Payload contains:, Store a refresh token reference in Redis.          Key: ``refresh:{user_id}:{jti, Delete a refresh token reference from Redis., Delete every stored refresh token for a user., Check whether a refresh token is still valid (present in Redis)., Rotate a refresh token: create a new one, store it, revoke the old one.

### Community 193 - "Teacher Management"
Cohesion: 0.33
Nodes (3): Decode and return the token payload.          Raises HTTPException 401 if the to, Check whether a token (by jti) is in the Redis blacklist., FastAPI Depends-compatible callable.          Decodes the token, checks blacklis

### Community 105 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (13): seed_admin(), _get_or_create_role(), _get_or_create_admin(), _ensure_user_role(), _get_or_create_app_role(), _ensure_role_menus(), _seed_menus(), _seed_buttons() (+5 more)

### Community 180 - "Project Documentation"
Cohesion: 0.57
Nodes (6): _china_now_naive(), seed_coupons(), _get_or_create_demo_user(), _seed_notification_preferences(), seed_notifications(), seed_all()

### Community 21 - "SMS & Captcha Tests"
Cohesion: 0.06
Nodes (43): AliyunSMSProvider, Aliyun Dysms API client for sending SMS verification codes., mock_redis(), settings(), settings_with_creds(), sms_service(), sms_service_prod(), _send_and_expect_code() (+35 more)

### Community 31 - "Auth & Login Tests"
Cohesion: 0.08
Nodes (18): UploadValidationError, UploadConfigError, UploadObject, LocalStorageAdapter, OssStorageAdapter, get_storage_adapter(), ImageUploadService, validate_scope() (+10 more)

### Community 87 - "Booking Service Tests"
Cohesion: 0.23
Nodes (5): UserSecurityService, mask_phone(), mask_id_card(), hash_id_card(), is_valid_id_card()

### Community 60 - "Booking Service Tests"
Cohesion: 0.16
Nodes (6): _transaction_title(), _transaction_direction(), _transaction_completed_at(), _now_for_coupon_db(), WalletService, admin_list_transactions()

### Community 67 - "Booking Cancellation Tests"
Cohesion: 0.19
Nodes (1): WechatAuthService

### Community 84 - "Booking Cancellation Tests"
Cohesion: 0.18
Nodes (4): _coupon(), _seed_activity_coupon(), TestActivityCouponService, TestActivityCouponAPI

### Community 68 - "Booking Cancellation Tests"
Cohesion: 0.10
Nodes (11): TestListActivities, Default pagination returns page 1 with all items., Custom page_size limits items per page., Page 2 returns remaining items., Page beyond total items adjusts offset to last valid page., Keyword search filters by title and description., Keyword search with no matches returns empty., Filter is_active=True returns only active activities. (+3 more)

### Community 61 - "Teacher Management Tests"
Cohesion: 0.26
Nodes (17): _make_room(), _make_seat(), _make_user(), _make_booking(), _make_coupon(), _make_user_coupon(), test_create_booking_service_without_coupon_sets_original_and_zero_discount(), test_create_booking_service_with_coupon_marks_coupon_used() (+9 more)

### Community 128 - "Seat Management Tests"
Cohesion: 0.33
Nodes (3): _coupon_data(), _create_coupon(), TestAdminCouponService

### Community 211 - "Community 211"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_component_options_and_invalid_component(), test_menu_tree_crud_and_delete_child_conflict(), test_dynamic_routes_exclude_buttons_and_disabled_nodes()

### Community 227 - "Community 227"
Cohesion: 0.83
Nodes (3): legacy_headers(), test_role_crud_duplicate_and_assigned_delete_conflict(), test_role_menu_assignment_updates_auth_permissions()

### Community 88 - "Booking Service Tests"
Cohesion: 0.12
Nodes (2): admin_client(), unauth_client()

### Community 77 - "Auth & WeChat Integration"
Cohesion: 0.11
Nodes (1): admin_client()

### Community 212 - "Community 212"
Cohesion: 0.70
Nodes (4): legacy_headers(), test_settings_read_masks_smtp_password(), test_update_email_without_password_preserves_existing_secret(), test_email_test_requires_complete_config()

### Community 26 - "Auth & WeChat Integration"
Cohesion: 0.08
Nodes (37): legacy_headers(), seed_users(), test_list_users_default(), test_list_users_pagination(), test_list_users_pagination_page2(), test_list_users_filter_by_user_type_app(), test_list_users_filter_by_user_type_admin(), test_list_users_filter_by_keyword_phone() (+29 more)

### Community 42 - "Teacher Management Tests"
Cohesion: 0.06
Nodes (8): TestAdminAuth, TestAdminListActivities, TestAdminCreateActivity, TestAdminGetActivity, TestAdminUpdateActivity, TestAdminDeleteActivity, TestAdminToggleStatus, Integration tests for admin activity API endpoints.

### Community 129 - "Teacher Management Tests"
Cohesion: 0.22
Nodes (2): _payload(), TestAdminCouponApi

### Community 69 - "Booking Payment Tests"
Cohesion: 0.16
Nodes (2): _payload(), TestAdminTeacherApi

### Community 183 - "Auth & WeChat Integration"
Cohesion: 0.29
Nodes (4): TestSendCode, Successful send-code returns 200., send-code with captcha_token passes it through., When SMSService raises HTTPException, it propagates.

### Community 184 - "Payment & Wallet"
Cohesion: 0.29
Nodes (4): TestGetMeAuth, GET /me without auth returns 401., GET /me with valid auth returns user info., GET /me with auth but user not in DB returns 404.

### Community 89 - "Coupon System"
Cohesion: 0.12
Nodes (1): TestCreateBooking

### Community 100 - "Miscellaneous Module"
Cohesion: 0.24
Nodes (1): TestCancelBooking

### Community 51 - "Booking Cancellation Tests"
Cohesion: 0.08
Nodes (8): TestGetCourseLessons, TestCreateCourseBooking, TestCancelCourseBooking, Integration tests for Course Booking API.  注意：当前测试基础设施使用 SQLite 内存数据库，不支持 Postgr, GET /api/v1/courses/{id}/lessons。, POST /api/v1/course-bookings。, 无效 lesson_ids 返回 400。, POST /api/v1/course-bookings/{booking_id}/cancel。

### Community 141 - "User Profile Tests"
Cohesion: 0.20
Nodes (1): TestSeatAPI

### Community 30 - "Miscellaneous Module"
Cohesion: 0.06
Nodes (7): TestGetSummary, TestListRecords, _add_booking(), TestCalculateStreakDays, TestGetMonthlySummary, TestListStudyRecords, 7d72fbb test: add study record service and API tests

### Community 101 - "Teacher & Course Models"
Cohesion: 0.13
Nodes (2): TestUploadAPI, Integration tests for file upload API endpoints.

### Community 142 - "Teacher Management Tests"
Cohesion: 0.36
Nodes (8): _create_user(), test_get_current_user_profile_returns_username_fields(), test_update_username_success_sets_cooldown_timestamp(), test_update_username_rejects_duplicate(), test_update_username_rejects_invalid_format(), test_update_username_rejects_cooldown(), test_update_nickname_does_not_require_username_cooldown(), test_update_profile_rejects_protected_fields()

### Community 118 - "Coupon System"
Cohesion: 0.29
Nodes (9): _create_user(), test_security_summary_masks_sensitive_fields(), test_security_summary_returns_deleted_unbound_unverified_state(), test_change_password_updates_hash_and_revokes_refresh_tokens(), test_change_password_rejects_bad_old_password_or_mismatch(), test_submit_identity_verification_masks_and_verifies(), test_submit_identity_rejects_invalid_or_different_verified(), test_deactivate_account_sets_deleted_without_removing_user() (+1 more)

### Community 27 - "Coupon System"
Cohesion: 0.06
Nodes (23): _mock_keys_result(), mock_db(), _mock_scalar_result(), TestRegister, TestLogin, TestRefreshToken, Unit tests for AuthService., Return an AsyncMock whose coroutine resolves to the given list. (+15 more)

### Community 171 - "Token Verification"
Cohesion: 0.43
Nodes (6): _policy(), test_over_48_hours_full_refund(), test_exact_48_hours_charges_10_percent(), test_exact_24_hours_charges_20_percent(), test_exact_2_hours_charges_50_percent(), test_non_round_amount_keeps_penalty_and_refund_balanced()

### Community 185 - "Redis Connection"
Cohesion: 0.29
Nodes (4): TestBookingDefaults, TestBookingRequiredFields, Tests for the Booking model., Test that required fields are enforced.

### Community 196 - "Miscellaneous Module"
Cohesion: 0.33
Nodes (2): TestCityAPI, Integration tests for city APIs.

### Community 197 - "Miscellaneous Module"
Cohesion: 0.33
Nodes (2): TestCityModel, Unit tests for the City model.

### Community 157 - "Deployment Config"
Cohesion: 0.22
Nodes (1): TestAvailableCouponsForBooking

### Community 46 - "Token Verification"
Cohesion: 0.09
Nodes (13): _make_course(), TestCourseBookingPricing, TestCourseBookingValidation, Unit tests for CourseBookingService., 构造一个轻量 Course mock 对象。, 固定班课：3 课时 × ¥80 = ¥240。, 1V1 定制：2 课时 × ¥200 = ¥400。, 全套优惠：12 课时，price=80, full_package_price=860         → original_price=860, discou (+5 more)

### Community 186 - "Payment & Wallet"
Cohesion: 0.29
Nodes (4): TestGetCurrentUserId, No credentials (no Authorization header) returns 401., Valid access token returns the user ID., Invalid token returns 401.

### Community 34 - "Payment & Wallet"
Cohesion: 0.06
Nodes (24): _mock_keys_result(), settings(), mock_redis(), jwt_service(), user_id(), TestCreateAccessToken, TestCreateRefreshToken, TestBlacklist (+16 more)

### Community 187 - "Token Verification"
Cohesion: 0.29
Nodes (4): TestVerifyToken, verify_token returns payload for a valid token., verify_token raises HTTPException 401 for an expired token., verify_token raises HTTPException 401 for a token with wrong secret.

### Community 188 - "Miscellaneous Module"
Cohesion: 0.29
Nodes (4): TestRefreshTokenStorage, store_refresh_token stores with correct key and TTL., revoke_refresh_token deletes the key from Redis., is_refresh_token_valid checks Redis existence.

### Community 158 - "Database Migrations"
Cohesion: 0.22
Nodes (5): TestGetCurrentUserId, get_current_user_id returns the user UUID from a valid access token., get_current_user_id raises 401 for a blacklisted token., get_current_user_id raises 401 when token type is not 'access'., get_current_user_id raises 401 for an expired token.

### Community 214 - "Community 214"
Cohesion: 0.40
Nodes (1): TestTeacherModel

### Community 189 - "Activity Management"
Cohesion: 0.29
Nodes (1): TestCourseModel

### Community 213 - "Community 213"
Cohesion: 0.40
Nodes (2): TestStudyRoomRoomType, StudyRoom.room_type 字段验证。

### Community 78 - "Integration Tests"
Cohesion: 0.11
Nodes (15): test_import_teacher_response(), test_import_course_schemas(), test_course_response_tags_parsing(), test_study_room_response_has_room_type(), test_room_create_has_room_type(), test_room_update_has_room_type(), test_room_admin_response_has_room_type(), 培训课程相关 Schema 导入与功能测试  验证以下 schema 能正确导入和使用： - TeacherResponse, TeacherBrief, Ho (+7 more)

### Community 79 - "Notification System"
Cohesion: 0.11
Nodes (5): seed_training_data(), TestTrainingRoomsAPI, TestCoursesAPI, Integration tests for training room and course APIs., Insert training rooms, teachers, and courses into the test database.

### Community 130 - "Auth & Login Tests"
Cohesion: 0.18
Nodes (6): TestTrainingRoomDetailResponse, TrainingRoomDetailResponse schema 测试, 验证 teachers 和 courses 字段默认值为空列表, 验证嵌套的 CourseResponse 中 tags 字段可以正确解析逗号分隔字符串, 验证嵌套 CourseResponse 的 tags 为 None 时解析为空列表, 验证缺少必填字段时抛出 ValidationError

### Community 143 - "Auth & Login Tests"
Cohesion: 0.20
Nodes (3): TestListTrainingRooms, 只返回 room_type 为 training 或 comprehensive 且 status=open 的房间。, 非热门课程不出现在 hot_courses 中。

### Community 111 - "Miscellaneous Module"
Cohesion: 0.23
Nodes (3): _make_user(), TestProcessVipUpgrade, TestVIPScopeFilter

### Community 45 - "Deployment Config"
Cohesion: 0.17
Nodes (22): _mock_scalar_result(), _mock_scalar_one_result(), _mock_scalars_result(), _test_user_id(), test_get_balance(), test_list_transactions_returns_current_user_first_page(), test_list_transactions_filters_by_recharge_type(), test_list_transactions_maps_booking_refund_title_and_linkage() (+14 more)

### Community 131 - "Token Verification"
Cohesion: 0.22
Nodes (3): _token_sub(), test_first_wechat_login_creates_phone_null_user_and_caches_session_key(), test_repeat_wechat_login_reuses_bound_user()

### Community 56 - "Booking Verification Tests"
Cohesion: 0.17
Nodes (19): _access_token(), _token_sub(), _temp_wechat_user(), _phone_user(), test_bind_wechat_phone_code_to_new_phone(), test_bind_phone_with_sms_to_new_phone(), test_wechat_phone_code_failure_maps_to_400(), test_wechat_access_token_failure_maps_to_phone_503() (+11 more)

## Knowledge Gaps
- **384 isolated node(s):** `requestParams`, `result`, `token`, `adminInfo`, `menusList` (+379 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Miscellaneous Module`** (2 nodes): `CountTo`, `withInstall()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 222`** (1 nodes): `key`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 262`** (1 nodes): `directive`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 263`** (1 nodes): `RoleEnum`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 249`** (1 nodes): `WindowSizeOptions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 221`** (2 nodes): `setLoading()`, `useAsync()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 251`** (1 nodes): `Battery`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Domain Service`** (2 nodes): `ParentLayout()`, `routes`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 269`** (1 nodes): `animates`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 254`** (2 nodes): `appThemeList`, `setting`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 273`** (1 nodes): `params`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 261`** (1 nodes): `BasicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 271`** (1 nodes): `DynamicProps`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 248`** (1 nodes): `__APP_INFO__`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 223`** (1 nodes): `useCityStore`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (1 nodes): `create_users_table  Revision ID: 0a2b2652445d Revises:  Create Date: 2026-04-17`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 230`** (1 nodes): `create_users_table  Revision ID: 1dfa25667f22 Revises: 0a2b2652445d Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 231`** (1 nodes): `create_activities_table  Revision ID: ba64420678cf Revises: 1dfa25667f22 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 232`** (1 nodes): `create_seats_and_bookings  Revision ID: de5e1f080747 Revises: ba64420678cf Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 233`** (1 nodes): `update_users_table  Revision ID: f836feddafc6 Revises: 28a1f4af90df Create Date:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 234`** (1 nodes): `add_cities_table_and_room_city_id  Revision ID: 7c9d2e4f6a1b Revises: f836feddaf`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 235`** (1 nodes): `add_wechat_payment_fields  Revision ID: a8c3f1b2d4e5 Revises: 7c9d2e4f6a1b Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 236`** (1 nodes): `add_booking_payment_query_schedule  Revision ID: f6a1b2c3d4e5 Revises: e5f6a1b2c`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 237`** (1 nodes): `add_notification_tables  Revision ID: a7b8c9d0e1f2 Revises: f6a1b2c3d4e5 Create`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 238`** (1 nodes): `add booking cancellation audit fields  Revision ID: b8c9d0e1f2a3 Revises: a7b8c9`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 239`** (1 nodes): `add room follows  Revision ID: c9d0e1f2a3b4 Revises: b8c9d0e1f2a3 Create Date: 2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 240`** (1 nodes): `add_activity_coupon_campaign  Revision ID: f1a2b3c4d5e6 Revises: d0e1f2a3b4c5 Cr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 241`** (1 nodes): `create_schedule_HotCourseItem  Revision ID: fccf087f0f34 Revises: e3f4a5b6c7d8 C`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 242`** (1 nodes): `create_course_table  Revision ID: c84abd1322d4 Revises: c4d5e6f7a8b9 Create Date`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 243`** (1 nodes): `add teacher bio and student_count  Revision ID: e7f8a9b0c1d2 Revises: c84abd1322`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 244`** (1 nodes): `add course booking fields  Revision ID: a1b2c3d4e5f7 Revises: e7f8a9b0c1d2 Creat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 245`** (1 nodes): `add full_custom_price to courses  Revision ID: 5d8e53290b12 Revises: a1b2c3d4e5f`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 246`** (1 nodes): `create course_schedules table and migrate fields from courses  Revision ID: b1c2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 247`** (1 nodes): `extend teachers table and create teacher_rooms  Revision ID: d3e4f5a6b7c8 Revise`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 224`** (1 nodes): `get_course_lessons()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 253`** (1 nodes): `TeacherDetailResponse`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (2 nodes): `_RichTextSanitizer`, `HTMLParser`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coupon Service Tests`** (1 nodes): `AdminMenuService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (1 nodes): `AdminRoleService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Admin Coupon Tests`** (1 nodes): `AdminSettingService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Cancellation Tests`** (1 nodes): `WechatAuthService`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Service Tests`** (2 nodes): `admin_client()`, `unauth_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth & WeChat Integration`** (1 nodes): `admin_client()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher Management Tests`** (2 nodes): `_payload()`, `TestAdminCouponApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Booking Payment Tests`** (2 nodes): `_payload()`, `TestAdminTeacherApi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coupon System`** (1 nodes): `TestCreateBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (1 nodes): `TestCancelBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `User Profile Tests`** (1 nodes): `TestSeatAPI`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Teacher & Course Models`** (2 nodes): `TestUploadAPI`, `Integration tests for file upload API endpoints.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (2 nodes): `TestCityAPI`, `Integration tests for city APIs.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Miscellaneous Module`** (2 nodes): `TestCityModel`, `Unit tests for the City model.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Deployment Config`** (1 nodes): `TestAvailableCouponsForBooking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 214`** (1 nodes): `TestTeacherModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Activity Management`** (1 nodes): `TestCourseModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 213`** (2 nodes): `TestStudyRoomRoomType`, `StudyRoom.room_type 字段验证。`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Teacher Management Tests` to `Teacher Management Tests`, `Auth & WeChat Integration`, `Auth & Login Tests`, `Teacher Management`, `Auth & Login Tests`, `Teacher Management`, `SMS & Captcha Tests`, `Auth & Login Tests`, `Backend Service Layer`, `HTML Sanitizer`, `Auth & Login Tests`, `Booking Service Tests`, `Auth Service Layer`, `Booking Service Tests`, `Booking Cancellation Tests`, `User & Auth Models`, `Coupon System`, `Payment & Wallet`, `Token Verification`, `Miscellaneous Module`, `Database Migrations`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `StudyRoom` connect `Wallet Service Tests` to `Database Config`, `Booking Payment Tests`, `Auth & Login Tests`, `Booking Service Tests`, `Coupon Service Layer`, `Admin Coupon Tests`, `Auth Service Layer`, `Auth & Login Tests`, `Token Verification`, `Booking Payment Tests`, `Miscellaneous Module`, `Coupon System`, `Auth & Login Tests`, `Booking Cancellation Tests`, `Booking Service Tests`, `User Profile Tests`, `Miscellaneous Module`, `Deployment Config`, `Token Verification`, `Notification System`, `Auth & Login Tests`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `Base` connect `Auth & Login Tests` to `Miscellaneous Module`, `Auth & Login Tests`, `Auth & WeChat Integration`, `Room & Seat Management`, `Booking Payment Tests`, `RBAC Service Layer`, `Booking Service Tests`, `Token Verification`, `JWT Token Tests`, `Wallet Service Tests`, `Token Verification`, `Room Management Tests`, `Auth & WeChat Integration`, `Payment & Wallet`, `User & Auth Models`, `Payment & Wallet`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 244 inferred relationships involving `StudyRoom` (e.g. with `Base` and `City`) actually correct?**
  _`StudyRoom` has 244 INFERRED edges - model-reasoned connections that need verification._
- **Are the 212 inferred relationships involving `Settings` (e.g. with `AdminAuthService` and `AuthService`) actually correct?**
  _`Settings` has 212 INFERRED edges - model-reasoned connections that need verification._
- **What connects `requestParams`, `result`, `token` to the rest of the system?**
  _384 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Auth & Login Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.05241090146750524 - nodes in this community are weakly interconnected._
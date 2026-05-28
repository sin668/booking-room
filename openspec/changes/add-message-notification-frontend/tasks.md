## 1. Backend Data Model and Migration

- [x] 1.1 Inspect existing SQLAlchemy model conventions in `br-server/app/models/*.py`, especially user ownership, timestamps, enum/string fields, and relationship imports.
- [x] 1.2 Create `br-server/app/models/notification.py` with `NotificationType`, `Notification`, and `NotificationPreference`.
- [x] 1.3 Add `NotificationType` values `booking`, `activity`, `report`, and `arrival`.
- [x] 1.4 Add `notifications` table fields: `id`, `user_id`, `type`, `title`, `content`, `target_url`, `target_type`, `target_id`, `is_read`, `created_at`, and `read_at`.
- [x] 1.5 Add `notifications` indexes for current-user list and unread summary queries: `user_id`, `user_id/type`, `user_id/is_read`, and `user_id/created_at`.
- [x] 1.6 Add `notification_preferences` table fields: `id`, `user_id`, `booking_enabled`, `activity_enabled`, `report_enabled`, `arrival_enabled`, and `updated_at`.
- [x] 1.7 Add a unique constraint/index on `notification_preferences.user_id`.
- [x] 1.8 Import the notification models from `br-server/app/models/__init__.py` so Alembic metadata and tests can discover them.
- [x] 1.9 Create an Alembic migration in `br-server/alembic/versions/` for both tables.
- [x] 1.10 Ensure the migration downgrade drops indexes and tables in reverse dependency order.

## 2. Backend Schemas and Service

- [x] 2.1 Inspect existing Pydantic schema conventions in `br-server/app/schemas/*.py` for response model naming and ORM serialization style.
- [x] 2.2 Create `br-server/app/schemas/notification.py` with schemas for notification list item, paginated list response, unread summary, preferences response, and preferences update request.
- [x] 2.3 Validate schema field names match the OpenSpec contract: `total_unread`, per-type counts, `is_read`, `created_at`, `read_at`, and enabled flags.
- [x] 2.4 Create `br-server/app/services/notification_service.py`.
- [x] 2.5 Add service method to get or create default preferences with all four types enabled.
- [x] 2.6 Add service method to list current-user notifications with optional `type`, `page`, and `page_size`.
- [x] 2.7 Add service method to calculate unread summary while excluding disabled notification types from `total_unread`.
- [x] 2.8 Add service method to mark one current-user notification as read and set `read_at`.
- [x] 2.9 Add service method to mark all current-user notifications as read, optionally limited by type.
- [x] 2.10 Add service method to update preferences for the current user.
- [x] 2.11 Add `create_notification(...)` service method for future backend producers, with type validation and default unread state.

## 3. Backend Routes and API Documentation

- [x] 3.1 Inspect existing authenticated route patterns in `br-server/app/api/routes/*.py` and current-user dependency usage in `br-server/app/api/dependencies.py`.
- [x] 3.2 Create `br-server/app/api/routes/notification.py` with authenticated user routes.
- [x] 3.3 Add `GET /api/v1/notifications` with `type?`, `page`, and `page_size` query parameters.
- [x] 3.4 Add `GET /api/v1/notifications/unread-summary`.
- [x] 3.5 Add `POST /api/v1/notifications/{id}/read`.
- [x] 3.6 Add `POST /api/v1/notifications/read-all` with optional `type`.
- [x] 3.7 Add `GET /api/v1/notifications/preferences`.
- [x] 3.8 Add `PUT /api/v1/notifications/preferences`.
- [x] 3.9 Register the notification router in `br-server/app/main.py`.
- [x] 3.10 Confirm every route derives `user_id` from the authenticated current user and does not accept client-supplied `user_id`.
- [x] 3.11 Update `docs/api.md` with request parameters, response fields, auth requirement, and failure behavior for all notification endpoints.

## 4. Backend Tests

- [x] 4.1 Inspect existing API test fixtures in `br-server/tests/conftest.py` and current authenticated client patterns.
- [x] 4.2 Add `br-server/tests/test_notification_service.py` for service-level behavior.
- [x] 4.3 Test default preferences are all enabled when no preference row exists.
- [x] 4.4 Test updating preferences persists all four enabled flags.
- [x] 4.5 Test unread summary excludes disabled types from `total_unread`.
- [x] 4.6 Test `create_notification(...)` creates an unread notification for the target user.
- [x] 4.7 Add `br-server/tests/test_api_notifications.py` for route-level behavior.
- [x] 4.8 Test `GET /api/v1/notifications` returns only the current user's messages.
- [x] 4.9 Test notification list type filtering and pagination.
- [x] 4.10 Test `POST /api/v1/notifications/{id}/read` marks only current-user notification IDs.
- [x] 4.11 Test `POST /api/v1/notifications/read-all` marks all or one filtered type for the current user only.
- [x] 4.12 Test cross-user notification IDs cannot be read or modified.
- [x] 4.13 Run focused backend tests: `pytest tests/test_notification_service.py tests/test_api_notifications.py -v` from `br-server`.

## 5. Frontend Notification API and Shared Types

- [x] 5.1 Inspect existing br-app API wrappers in `br-app/src/api/*.js` and request helper behavior in `br-app/src/utils/request.js`.
- [x] 5.2 Create a shared notification type config in an appropriate frontend module, with keys, labels, setting labels, color/icon metadata, and default target routes.
- [x] 5.3 Add `br-app/src/api/notifications.js`.
- [x] 5.4 Implement API wrapper methods: `getNotifications`, `getNotificationUnreadSummary`, `markNotificationRead`, `markAllNotificationsRead`, `getNotificationPreferences`, and `updateNotificationPreferences`.
- [x] 5.5 Ensure all page code imports notification API methods instead of duplicating request paths.
- [x] 5.6 Ensure frontend field names match backend schemas exactly, especially enabled flags and unread summary fields.

## 6. Settings Integration

- [x] 6.1 Inspect current settings switch state and save behavior in `br-app/src/pages/settings/index.vue`.
- [x] 6.2 Refactor notification switches in `br-app/src/pages/settings/index.vue` to render from the shared 4-type config.
- [x] 6.3 Load preferences with `getNotificationPreferences()` when the settings page opens.
- [x] 6.4 Show a non-blocking loading state for notification preferences without preventing other settings content from rendering.
- [x] 6.5 Save changed preferences with `updateNotificationPreferences(payload)` when a switch changes.
- [x] 6.6 Roll back only the changed switch and show a toast when preference save fails.
- [x] 6.7 Ensure saved preferences are available to the notification center and home unread red dot after returning from settings.

## 7. Notification Center Page

- [x] 7.1 Add `pages/notifications/index` to `br-app/src/pages.json`.
- [x] 7.2 Create `br-app/src/pages/notifications/index.vue`.
- [x] 7.3 Build the page header and filter tabs for `all`, `booking`, `activity`, `report`, and `arrival`.
- [x] 7.4 Load notification preferences and notification list when the page opens.
- [x] 7.5 Implement list loading, empty, error, retry, and pull-to-refresh states.
- [x] 7.6 Implement type filtering by calling the backend list API with the selected type.
- [x] 7.7 Show unread markers and read styling based on `is_read`.
- [x] 7.8 Implement mark-all-read for the current filter scope.
- [x] 7.9 Show a disabled-type hint when the selected type is turned off, while still allowing historical messages to display.
- [x] 7.10 Implement click behavior: call `markNotificationRead(id)` first, update local read state after success, then route to `target_url` or the type default page.
- [x] 7.11 Keep the message unread, show a toast, and do not navigate when mark-read fails.
- [x] 7.12 Ensure `booking`, `activity`, `report`, and `arrival` default targets resolve to existing app pages.

## 8. Home Page Integration

- [x] 8.1 Inspect current notification bell markup and `onTapBell` behavior in `br-app/src/pages/index/index.vue`.
- [x] 8.2 Update `onTapBell` to navigate to `/pages/notifications/index`.
- [x] 8.3 Load unread summary with `getNotificationUnreadSummary()` on page show.
- [x] 8.4 Refresh unread summary during home pull refresh if the page already supports pull refresh.
- [x] 8.5 Show the red dot only when `total_unread > 0`.
- [x] 8.6 Hide the red dot and keep the homepage usable when unread summary loading fails.
- [x] 8.7 Refresh unread state after returning from notification center or settings.

## 9. Verification and Cleanup

- [x] 9.1 Run focused backend notification tests from `br-server`.
- [x] 9.2 Run the existing backend test subset most likely to be affected by auth, users, and route registration.
- [x] 9.3 Run `pnpm run build:h5` from `br-app`.
- [x] 9.4 Manually verify homepage bell navigation and red dot behavior.
- [x] 9.5 Manually verify notification center filtering, empty state, error retry, pull refresh, read state, mark-all-read, disabled-type hint, and target navigation.
- [x] 9.6 Manually verify settings preference load, save, failure rollback, and return-to-home red dot refresh.
- [x] 9.7 Confirm `docs/api.md` and OpenSpec stay aligned with implemented endpoint paths and field names.
- [x] 9.8 Run `git diff --check`.
- [x] 9.9 Confirm no unrelated files are staged or modified before commit.

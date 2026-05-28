## 1. Backend Data Model and Migration

- [ ] 1.1 Inspect existing SQLAlchemy model conventions in `br-server/app/models/*.py`, especially user ownership, timestamps, enum/string fields, and relationship imports.
- [ ] 1.2 Create `br-server/app/models/notification.py` with `NotificationType`, `Notification`, and `NotificationPreference`.
- [ ] 1.3 Add `NotificationType` values `booking`, `activity`, `report`, and `arrival`.
- [ ] 1.4 Add `notifications` table fields: `id`, `user_id`, `type`, `title`, `content`, `target_url`, `target_type`, `target_id`, `is_read`, `created_at`, and `read_at`.
- [ ] 1.5 Add `notifications` indexes for current-user list and unread summary queries: `user_id`, `user_id/type`, `user_id/is_read`, and `user_id/created_at`.
- [ ] 1.6 Add `notification_preferences` table fields: `id`, `user_id`, `booking_enabled`, `activity_enabled`, `report_enabled`, `arrival_enabled`, and `updated_at`.
- [ ] 1.7 Add a unique constraint/index on `notification_preferences.user_id`.
- [ ] 1.8 Import the notification models from `br-server/app/models/__init__.py` so Alembic metadata and tests can discover them.
- [ ] 1.9 Create an Alembic migration in `br-server/alembic/versions/` for both tables.
- [ ] 1.10 Ensure the migration downgrade drops indexes and tables in reverse dependency order.

## 2. Backend Schemas and Service

- [ ] 2.1 Inspect existing Pydantic schema conventions in `br-server/app/schemas/*.py` for response model naming and ORM serialization style.
- [ ] 2.2 Create `br-server/app/schemas/notification.py` with schemas for notification list item, paginated list response, unread summary, preferences response, and preferences update request.
- [ ] 2.3 Validate schema field names match the OpenSpec contract: `total_unread`, per-type counts, `is_read`, `created_at`, `read_at`, and enabled flags.
- [ ] 2.4 Create `br-server/app/services/notification_service.py`.
- [ ] 2.5 Add service method to get or create default preferences with all four types enabled.
- [ ] 2.6 Add service method to list current-user notifications with optional `type`, `page`, and `page_size`.
- [ ] 2.7 Add service method to calculate unread summary while excluding disabled notification types from `total_unread`.
- [ ] 2.8 Add service method to mark one current-user notification as read and set `read_at`.
- [ ] 2.9 Add service method to mark all current-user notifications as read, optionally limited by type.
- [ ] 2.10 Add service method to update preferences for the current user.
- [ ] 2.11 Add `create_notification(...)` service method for future backend producers, with type validation and default unread state.

## 3. Backend Routes and API Documentation

- [ ] 3.1 Inspect existing authenticated route patterns in `br-server/app/api/routes/*.py` and current-user dependency usage in `br-server/app/api/dependencies.py`.
- [ ] 3.2 Create `br-server/app/api/routes/notification.py` with authenticated user routes.
- [ ] 3.3 Add `GET /api/v1/notifications` with `type?`, `page`, and `page_size` query parameters.
- [ ] 3.4 Add `GET /api/v1/notifications/unread-summary`.
- [ ] 3.5 Add `POST /api/v1/notifications/{id}/read`.
- [ ] 3.6 Add `POST /api/v1/notifications/read-all` with optional `type`.
- [ ] 3.7 Add `GET /api/v1/notifications/preferences`.
- [ ] 3.8 Add `PUT /api/v1/notifications/preferences`.
- [ ] 3.9 Register the notification router in `br-server/app/main.py`.
- [ ] 3.10 Confirm every route derives `user_id` from the authenticated current user and does not accept client-supplied `user_id`.
- [ ] 3.11 Update `docs/api.md` with request parameters, response fields, auth requirement, and failure behavior for all notification endpoints.

## 4. Backend Tests

- [ ] 4.1 Inspect existing API test fixtures in `br-server/tests/conftest.py` and current authenticated client patterns.
- [ ] 4.2 Add `br-server/tests/test_notification_service.py` for service-level behavior.
- [ ] 4.3 Test default preferences are all enabled when no preference row exists.
- [ ] 4.4 Test updating preferences persists all four enabled flags.
- [ ] 4.5 Test unread summary excludes disabled types from `total_unread`.
- [ ] 4.6 Test `create_notification(...)` creates an unread notification for the target user.
- [ ] 4.7 Add `br-server/tests/test_api_notifications.py` for route-level behavior.
- [ ] 4.8 Test `GET /api/v1/notifications` returns only the current user's messages.
- [ ] 4.9 Test notification list type filtering and pagination.
- [ ] 4.10 Test `POST /api/v1/notifications/{id}/read` marks only current-user notification IDs.
- [ ] 4.11 Test `POST /api/v1/notifications/read-all` marks all or one filtered type for the current user only.
- [ ] 4.12 Test cross-user notification IDs cannot be read or modified.
- [ ] 4.13 Run focused backend tests: `pytest tests/test_notification_service.py tests/test_api_notifications.py -v` from `br-server`.

## 5. Frontend Notification API and Shared Types

- [ ] 5.1 Inspect existing br-app API wrappers in `br-app/src/api/*.js` and request helper behavior in `br-app/src/utils/request.js`.
- [ ] 5.2 Create a shared notification type config in an appropriate frontend module, with keys, labels, setting labels, color/icon metadata, and default target routes.
- [ ] 5.3 Add `br-app/src/api/notifications.js`.
- [ ] 5.4 Implement API wrapper methods: `getNotifications`, `getNotificationUnreadSummary`, `markNotificationRead`, `markAllNotificationsRead`, `getNotificationPreferences`, and `updateNotificationPreferences`.
- [ ] 5.5 Ensure all page code imports notification API methods instead of duplicating request paths.
- [ ] 5.6 Ensure frontend field names match backend schemas exactly, especially enabled flags and unread summary fields.

## 6. Settings Integration

- [ ] 6.1 Inspect current settings switch state and save behavior in `br-app/src/pages/settings/index.vue`.
- [ ] 6.2 Refactor notification switches in `br-app/src/pages/settings/index.vue` to render from the shared 4-type config.
- [ ] 6.3 Load preferences with `getNotificationPreferences()` when the settings page opens.
- [ ] 6.4 Show a non-blocking loading state for notification preferences without preventing other settings content from rendering.
- [ ] 6.5 Save changed preferences with `updateNotificationPreferences(payload)` when a switch changes.
- [ ] 6.6 Roll back only the changed switch and show a toast when preference save fails.
- [ ] 6.7 Ensure saved preferences are available to the notification center and home unread red dot after returning from settings.

## 7. Notification Center Page

- [ ] 7.1 Add `pages/notifications/index` to `br-app/src/pages.json`.
- [ ] 7.2 Create `br-app/src/pages/notifications/index.vue`.
- [ ] 7.3 Build the page header and filter tabs for `all`, `booking`, `activity`, `report`, and `arrival`.
- [ ] 7.4 Load notification preferences and notification list when the page opens.
- [ ] 7.5 Implement list loading, empty, error, retry, and pull-to-refresh states.
- [ ] 7.6 Implement type filtering by calling the backend list API with the selected type.
- [ ] 7.7 Show unread markers and read styling based on `is_read`.
- [ ] 7.8 Implement mark-all-read for the current filter scope.
- [ ] 7.9 Show a disabled-type hint when the selected type is turned off, while still allowing historical messages to display.
- [ ] 7.10 Implement click behavior: call `markNotificationRead(id)` first, update local read state after success, then route to `target_url` or the type default page.
- [ ] 7.11 Keep the message unread, show a toast, and do not navigate when mark-read fails.
- [ ] 7.12 Ensure `booking`, `activity`, `report`, and `arrival` default targets resolve to existing app pages.

## 8. Home Page Integration

- [ ] 8.1 Inspect current notification bell markup and `onTapBell` behavior in `br-app/src/pages/index/index.vue`.
- [ ] 8.2 Update `onTapBell` to navigate to `/pages/notifications/index`.
- [ ] 8.3 Load unread summary with `getNotificationUnreadSummary()` on page show.
- [ ] 8.4 Refresh unread summary during home pull refresh if the page already supports pull refresh.
- [ ] 8.5 Show the red dot only when `total_unread > 0`.
- [ ] 8.6 Hide the red dot and keep the homepage usable when unread summary loading fails.
- [ ] 8.7 Refresh unread state after returning from notification center or settings.

## 9. Verification and Cleanup

- [ ] 9.1 Run focused backend notification tests from `br-server`.
- [ ] 9.2 Run the existing backend test subset most likely to be affected by auth, users, and route registration.
- [ ] 9.3 Run `pnpm run build:h5` from `br-app`.
- [ ] 9.4 Manually verify homepage bell navigation and red dot behavior.
- [ ] 9.5 Manually verify notification center filtering, empty state, error retry, pull refresh, read state, mark-all-read, disabled-type hint, and target navigation.
- [ ] 9.6 Manually verify settings preference load, save, failure rollback, and return-to-home red dot refresh.
- [ ] 9.7 Confirm `docs/api.md` and OpenSpec stay aligned with implemented endpoint paths and field names.
- [ ] 9.8 Run `git diff --check`.
- [ ] 9.9 Confirm no unrelated files are staged or modified before commit.

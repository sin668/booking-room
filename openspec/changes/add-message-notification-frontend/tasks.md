## 1. Backend Data Model and Migration

- [ ] 1.1 Add br-server notification type enum for `booking`, `activity`, `report`, and `arrival`.
- [ ] 1.2 Add `notifications` model/table with current-user ownership, type, title, content, target fields, read state, timestamps, and indexes for `user_id/type/is_read/created_at`.
- [ ] 1.3 Add `notification_preferences` model/table with four enabled flags and one row per user.
- [ ] 1.4 Add database migration for both tables with safe defaults and rollback.

## 2. Backend REST API

- [ ] 2.1 Add notification schemas for list items, paginated list response, unread summary, preferences, and preference update request.
- [ ] 2.2 Add notification service methods for list pagination, unread summary filtered by enabled preferences, mark read, mark all read, get/update preferences, and `create_notification(...)`.
- [ ] 2.3 Add authenticated routes for `GET /api/v1/notifications`, `GET /api/v1/notifications/unread-summary`, `POST /api/v1/notifications/{id}/read`, and `POST /api/v1/notifications/read-all`.
- [ ] 2.4 Add authenticated routes for `GET /api/v1/notifications/preferences` and `PUT /api/v1/notifications/preferences`.
- [ ] 2.5 Ensure all routes derive `user_id` from the current user and reject or ignore any cross-user access.
- [ ] 2.6 Update `docs/api.md` with the notification API contract.

## 3. Backend Tests

- [ ] 3.1 Test notification list returns only current user's messages with type filter and pagination.
- [ ] 3.2 Test unread summary counts only enabled notification types.
- [ ] 3.3 Test single notification read and all-read operations are scoped to the current user.
- [ ] 3.4 Test preference defaults, updates, and save/read round trip.
- [ ] 3.5 Test cross-user notification IDs cannot be read or modified.

## 4. Frontend Notification Contracts

- [ ] 4.1 Define shared notification type config for `booking`, `activity`, `report`, and `arrival` labels, icons, colors, and setting keys.
- [ ] 4.2 Add `br-app/src/api/notifications.js` with `getNotifications`, `getNotificationUnreadSummary`, `markNotificationRead`, `markAllNotificationsRead`, `getNotificationPreferences`, and `updateNotificationPreferences`.
- [ ] 4.3 Keep all page components behind the API wrapper and avoid direct request-path duplication.

## 5. Settings Integration

- [ ] 5.1 Refactor `pages/settings/index.vue` notification switches to use the shared 4-type config.
- [ ] 5.2 Load notification preferences from `GET /api/v1/notifications/preferences` when the settings page opens.
- [ ] 5.3 Save notification preferences through `PUT /api/v1/notifications/preferences`.
- [ ] 5.4 Roll back the changed switch and show a toast when preference save fails.
- [ ] 5.5 Ensure preference updates are reflected by the notification center and home unread red dot.

## 6. Notification Center Page

- [ ] 6.1 Add `pages/notifications/index` route to `br-app/src/pages.json`.
- [ ] 6.2 Build the notification center page with header, filter tabs, list, unread markers, and mark-all-read action.
- [ ] 6.3 Implement loading, empty, error, retry, and pull-to-refresh states.
- [ ] 6.4 Implement type filtering for all, booking, activity, report, and arrival.
- [ ] 6.5 Respect disabled notification preferences by showing a type-disabled hint and excluding disabled types from active unread prompting.
- [ ] 6.6 Implement click behavior to mark individual notifications as read and route to `target_url` or the type default page after read succeeds.
- [ ] 6.7 Keep the message unread when mark-read fails and show a toast without navigating.

## 7. Home Page Integration

- [ ] 7.1 Update `pages/index/index.vue` notification bell click to navigate to `/pages/notifications/index`.
- [ ] 7.2 Load unread summary on home page show and pull refresh.
- [ ] 7.3 Show the red dot only when enabled notification types have unread messages.
- [ ] 7.4 Hide the red dot without blocking homepage rendering when unread summary loading fails.
- [ ] 7.5 Refresh unread state after returning from the notification center.

## 8. Review, Refactor, and Verification

- [ ] 8.1 Review code layering to keep page components, API calls, backend services, and notification type config separated.
- [ ] 8.2 Remove duplicated notification label/type logic across home, settings, and notification pages.
- [ ] 8.3 Run focused br-server notification tests.
- [ ] 8.4 Run `pnpm run build:h5` in `br-app`.
- [ ] 8.5 Manually verify home red dot, notification filtering, mark-read behavior, settings preference save/rollback, disabled-type hint, and type jump behavior.
- [ ] 8.6 Confirm no unrelated files are modified and prepare implementation notes for review.

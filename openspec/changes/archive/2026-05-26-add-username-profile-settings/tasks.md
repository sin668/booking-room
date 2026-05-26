## 1. Data Model and Migration

- [x] 1.1 Audit current username-related schema and indexes in `br-server/app/models/user.py`, `br-server/alembic/versions/`, `br-server/tests/test_unified_user_model.py`, and admin/app user creation services; record whether the existing `ix_users_username` already behaves as global non-null unique or needs migration changes.
- [x] 1.2 Add Alembic migration under `br-server/alembic/versions/` for `users.username_updated_at` as nullable `DateTime`, with downgrade support that drops only this new column.
- [x] 1.3 If audit shows username uniqueness is still admin-only in an active migration path, update migration history with a forward migration that replaces admin-only username uniqueness with global non-null uniqueness; otherwise leave existing global `ix_users_username` unchanged and document that no index migration is required in the migration file or task notes.
- [x] 1.4 Add migration backfill for existing app users with NULL username using the same random-English-name + 5-digit generator format, checking existing usernames before writing each value.
- [x] 1.5 Update `br-server/app/models/user.py` to include `username_updated_at` and keep `username` index metadata aligned with the migration.
- [x] 1.6 Review `br-server/app/services/seed_admin.py` and `br-server/app/services/admin_user_service.py` to ensure admin/app user creation remains compatible with global username uniqueness and app users without explicit username get one before insert.
- [x] 1.7 Verify migration chain with `cd br-server && alembic heads` and, where local database state allows, `cd br-server && alembic upgrade head`.

## 2. Backend Username Generation

- [x] 2.1 Create focused username generation/validation service in `br-server/app/services/username_service.py` with responsibilities limited to format validation, random candidate generation, uniqueness probing, and retry exhaustion.
- [x] 2.2 Enforce editable username format in the service: `^[A-Za-z0-9_]{6,32}$`; keep registration candidate format as random English name + 5 random digits.
- [x] 2.3 Add bounded collision retry for registration username generation and define the failure behavior as HTTP 503 or a service exception mapped to HTTP 503.
- [x] 2.4 Update `br-server/app/services/auth_service.py` registration flow so every new app user is persisted with a generated unique username before flush/commit.
- [x] 2.5 Update `br-server/app/services/admin_user_service.py` app-user creation flow so admin-created app users also receive a generated unique username when none is provided.
- [x] 2.6 Add unit tests in `br-server/tests/test_username_service.py` for generated format, edit-format acceptance/rejection, collision retry, uniqueness lookup, and retry exhaustion.
- [x] 2.7 Run `cd br-server && pytest tests/test_username_service.py -q` and keep failures local to this service before moving to profile API work.

## 3. Backend Profile API

- [x] 3.1 Extend `br-server/app/schemas/user.py` with profile update/read fields: `username`, `username_updated_at`, `nickname`, `avatar`, and a response shape that can expose remaining cooldown metadata when needed.
- [x] 3.2 Add `br-server/app/services/user_profile_service.py` to own current-user profile reads, safe profile updates, duplicate username checks, protected-field filtering, and rolling 24-hour username cooldown enforcement.
- [x] 3.3 Implement cooldown logic in the profile service: if `username_updated_at` is within the last 24 hours and the submitted username differs from current username, reject with HTTP 429 and include remaining seconds.
- [x] 3.4 Keep nickname/avatar updates independent of username cooldown; cooldown applies only to username changes.
- [x] 3.5 Update `br-server/app/api/routes/user.py` to keep `GET /api/v1/users/me` and add `PATCH /api/v1/users/me`, delegating business rules to `UserProfileService`.
- [x] 3.6 Decide whether `br-server/app/api/routes/auth.py::GET /api/v1/auth/me` remains as compatibility alias only; ensure it returns the same `UserResponse` fields as `/api/v1/users/me`.
- [x] 3.7 Ensure duplicate username update returns HTTP 409 with “该用户名已存在”, invalid username returns HTTP 422, cooldown returns HTTP 429 with remaining cooldown data, and unauthenticated requests still return HTTP 401.
- [x] 3.8 Add API tests in `br-server/tests/test_api_user_profile.py` for current profile read, successful username update, `username_updated_at` write, 24-hour cooldown rejection, cooldown-expired update, duplicate rejection, invalid format rejection, nickname/avatar update, and protected-field blocking.
- [x] 3.9 Add or update auth tests in `br-server/tests/test_api_auth.py` and `br-server/tests/test_auth_service.py` to assert registration creates a non-null username matching random-English-name + 5-digit format.
- [x] 3.10 Run `cd br-server && pytest tests/test_username_service.py tests/test_api_user_profile.py tests/test_api_auth.py tests/test_auth_service.py tests/test_unified_user_model.py -q`.

## 4. Frontend API and Store

- [x] 4.1 Add a focused profile API module at `br-app/src/api/userProfile.js` using existing request helpers for `GET /api/v1/users/me` and `PATCH /api/v1/users/me`.
- [x] 4.2 Add or expose a `patch` helper in `br-app/src/utils/request.js` if no PATCH helper exists, preserving existing token refresh behavior.
- [x] 4.3 Update `br-app/src/store/modules/user.js` getters for `username`, `avatar`, and `usernameUpdatedAt`.
- [x] 4.4 Update `fetchUserInfo()` in `br-app/src/store/modules/user.js` to use the profile API module or otherwise standardize on `/api/v1/users/me` while keeping login/register behavior unchanged.
- [x] 4.5 Add `updateProfile(payload)` action in `br-app/src/store/modules/user.js` that calls the profile update API, refreshes `userInfo`, and rethrows API errors for page-level messaging.
- [x] 4.6 Verify frontend API errors preserve HTTP 409/422/429 response bodies so the settings page can show duplicate, invalid-format, and cooldown messages.

## 5. Frontend Settings Page

- [x] 5.1 Register `pages/settings/index` in `br-app/src/pages.json` with custom or standard navigation matching the existing app style and `prototype/settings.html`.
- [x] 5.2 Create `br-app/src/pages/settings/index.vue` with the prototype-aligned structure: top nav, avatar/name card, personal profile group, account/security group, notification group, general group, about group, and logout confirmation.
- [x] 5.3 Populate the profile card and personal profile rows from `useUserStore()`: nickname, username, masked phone, avatar fallback, and safe placeholders for unsupported fields.
- [x] 5.4 Implement username row tap behavior that opens an edit modal/sheet/input state with current username, format hint, and “用户名修改后 24 小时内不可再次修改” prompt.
- [x] 5.5 Add client-side username validation for 6-32 characters and letters/numbers/underscore only before calling the API.
- [x] 5.6 On successful username save, call `userStore.updateProfile({ username })`, close the editor, and refresh the displayed username and cooldown state.
- [x] 5.7 On HTTP 429, keep the editor open or return to the row state with a clear message using remaining cooldown time, e.g. “用户名修改冷却中，请在 X 小时 Y 分钟后再试”.
- [x] 5.8 On HTTP 409, show “该用户名已存在”; on HTTP 422, show “用户名仅支持 6-32 位字母、数字或下划线”.
- [x] 5.9 Implement nickname/avatar display and safe stubs for non-scope rows so unsupported settings do not navigate to missing pages.
- [x] 5.10 Wire logout confirmation to existing `userStore.logout()` and navigate/reLaunch to `/pages/login/login`.
- [x] 5.11 Confirm existing profile page links in `br-app/src/pages/profile/index.vue` now resolve to the registered settings route.

## 6. Documentation

- [x] 6.1 Update `docs/api.md` registration response/current-user examples to include `username` and `username_updated_at`.
- [x] 6.2 Update `docs/api.md` `GET /api/v1/users/me` section with the final response fields and clarify it is the preferred app profile endpoint.
- [x] 6.3 Add `PATCH /api/v1/users/me` documentation with allowed request fields, success response, HTTP 401, 409, 422, and 429 examples.
- [x] 6.4 Document username rules in `docs/api.md`: generated default format, editable format, global uniqueness, and rolling 24-hour cooldown after successful username changes.

## 7. Verification and Review

- [x] 7.1 Run backend targeted tests: `cd br-server && pytest tests/test_username_service.py tests/test_api_user_profile.py tests/test_api_auth.py tests/test_auth_service.py tests/test_unified_user_model.py -q`.
- [x] 7.2 Run broader backend regression for auth/user/admin creation risk: `cd br-server && pytest tests/test_admin_user_management.py tests/test_admin_auth_api.py tests/test_app_default_role.py -q`.
- [x] 7.3 Run frontend validation from `br-app`: use the repository’s available build command, preferring `pnpm run build` if defined; otherwise run the existing project build/check script documented in `package.json`.
- [x] 7.4 Start the app preview/dev server only after implementation is complete and verify `/pages/settings/index` loads without route errors.
- [x] 7.5 Use gstack browser or the available app preview tooling to verify settings page visibility, username row rendering, edit success, duplicate error, cooldown error, masked phone, and logout confirmation.
- [x] 7.6 Review implementation for Clean Architecture boundaries: routes only parse/authenticate, services own username/profile business rules, schemas own validation shape, and frontend pages call API through modules/store.
- [x] 7.7 Refactor duplicated username regex, cooldown formatting, or profile API handling discovered during implementation before final verification.
- [x] 7.8 Update this `tasks.md` by checking completed tasks only after corresponding tests or manual verification pass.

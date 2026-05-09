## 1. Backend Schemas and Token Utilities

- [ ] 1.1 Create booking verification schemas for token response, booking verification detail, and confirmation response.
- [ ] 1.2 Implement a backend-signed token utility using a 5-minute validity window and payload fields for booking id, user id, issued time, and nonce.
- [ ] 1.3 Add explicit errors for no verifiable booking, invalid token, expired token, unauthorized staff access, already verified booking, and non-verifiable booking status.

## 2. Backend Service Layer

- [ ] 2.1 Implement token issuance service that finds the current user's eligible `confirmed` booking and returns token, `expires_at`, `verify_url`, and booking summary.
- [ ] 2.2 Implement token inspection service that validates token signature/expiry, loads booking, seat, room, and safe user display fields, and returns `can_verify`.
- [ ] 2.3 Implement confirmation service that revalidates token and booking state, updates `confirmed -> completed`, flushes the transaction, and blocks duplicate or invalid verification.
- [ ] 2.4 Keep booking verification logic in a dedicated service module and reuse existing booking response helpers only when doing so does not blur permission boundaries.

## 3. Backend Routes and API Documentation

- [ ] 3.1 Add `br-server/app/api/routes/booking_verification.py` with `POST /api/v1/booking-verifications/token`, `GET /api/v1/booking-verifications/{token}`, and `POST /api/v1/booking-verifications/{token}/confirm`.
- [ ] 3.2 Wire route dependencies so token issuance requires the current user and token inspection/confirmation require staff or administrator authorization.
- [ ] 3.3 Register the booking verification router in `br-server/app/main.py`.
- [ ] 3.4 Update `docs/api.md` with request parameters, response examples, authentication requirements, and error codes for all booking verification endpoints.

## 4. Backend Tests

- [ ] 4.1 Add service tests for successful token issuance, no eligible booking, expired token, invalid token, confirmed-to-completed verification, completed duplicate verification, and cancelled booking rejection.
- [ ] 4.2 Add API integration tests for user token issuance, staff token inspection, staff confirmation, unauthenticated rejection, non-staff rejection, expired token response, and repeated confirmation response.
- [ ] 4.3 Verify existing booking API tests still pass after adding the `completed` transition through verification.

## 5. Frontend API Layer

- [ ] 5.1 Add `br-app/src/api/bookingVerifications.js` with methods for issuing token, inspecting token, and confirming verification.
- [ ] 5.2 Ensure API methods follow the existing `br-app/src/api/*.js` request helper patterns and surface backend error messages to pages.

## 6. User QR Page

- [ ] 6.1 Register `pages/qrcode/index` in `br-app/src/pages.json` with `navigationBarTitleText: "我的学习码"`.
- [ ] 6.2 Add a `我的学习码` menu item in `br-app/src/pages/profile/index.vue`, placed under the member service area and navigating to `/pages/qrcode/index`.
- [ ] 6.3 Create `br-app/src/pages/qrcode/index.vue` using `prototype/qrcode.html` as the visual reference and existing app SCSS conventions.
- [ ] 6.4 Render backend `verify_url` as a scannable QR code, with booking summary, countdown, refresh action, safety tip, loading state, empty state, and retry state.
- [ ] 6.5 Remove or de-emphasize long-term save/share actions so users are not encouraged to preserve expired dynamic codes.

## 7. Staff H5 Verification Page

- [ ] 7.1 Register `pages/verify-booking/index` in `br-app/src/pages.json` with a clear verification title.
- [ ] 7.2 Create `br-app/src/pages/verify-booking/index.vue` that reads `token` from the URL, inspects booking details, and renders loading, unauthorized, expired, invalid, already verified, cancelled, and success states.
- [ ] 7.3 Implement the `确认核销` action with duplicate-submit protection and success-state locking.
- [ ] 7.4 Verify the page works when opened from a WeChat-scanned H5 URL format.

## 8. Review and Verification

- [ ] 8.1 Run backend tests for booking verification and existing booking behavior.
- [ ] 8.2 Run the available frontend verification command for `br-app` (lint/build/type check as supported by the project).
- [ ] 8.3 Manually verify the end-to-end flow: user opens QR page, employee scans URL, booking details display, employee confirms, booking becomes `completed`, and repeated confirmation fails.
- [ ] 8.4 Review implementation for Clean Architecture boundaries, permission enforcement, duplicated booking mapping logic, and token security assumptions.

# Personal Booking Verification QR Design

## Summary

Build a dynamic booking verification QR flow. A user opens `我的学习码` to display a backend-issued QR code for their current verifiable booking. A store staff member scans the QR code in WeChat, opens an H5 verification page, reviews booking details, and taps `确认核销` to mark the booking `completed`.

## Decisions

- QR content is a backend-issued H5 `verify_url`, not a frontend-generated static user code.
- The token is valid for five minutes and is bound to one booking.
- Staff or administrators perform verification; normal users only present the QR code.
- The scanned page is H5 for simplest WeChat compatibility.
- Token inspection and confirmation both require staff/admin authentication because booking details include user and purchase information.
- Confirmation updates only `confirmed` bookings to `completed`; `cancelled` and `completed` bookings cannot be verified.
- The user QR page focuses on countdown and refresh. Save/share actions are not core because the token is short-lived.

## Architecture

### User QR Page

- Route: `/pages/qrcode/index`
- Entry: profile page menu item `我的学习码`
- API: `POST /api/v1/booking-verifications/token`
- UI: user identity, QR code, booking summary, countdown, refresh, safety tip, loading, empty, retry, and login-required states

### Staff Verification Page

- Route: `/pages/verify-booking/index?token=...`
- API:
  - `GET /api/v1/booking-verifications/{token}`
  - `POST /api/v1/booking-verifications/{token}/confirm`
- UI: booking detail, unauthorized state, expired/invalid/already-verified/cancelled states, confirm action, success lock

### Backend

- New route module: `booking_verification.py`
- New service module: `booking_verification_service.py`
- New schemas: token response, verification detail, confirmation response
- Token implementation: backend-signed payload containing booking id, user id, issued time, and nonce, with a five-minute expiry
- State transition: `confirmed -> completed`

## Data Flow

1. User opens QR page.
2. Frontend requests token.
3. Backend finds the user's current verifiable `confirmed` booking.
4. Backend returns token, expiry, verify URL, and booking summary.
5. Frontend renders verify URL as QR code.
6. Staff scans QR code in WeChat and opens the H5 verification page.
7. H5 page inspects token through backend with staff/admin auth.
8. Backend returns booking information and `can_verify`.
9. Staff taps `确认核销`.
10. Backend revalidates token and booking status, then marks booking `completed`.

## Error Handling

- No verifiable booking: user QR page shows `暂无可核销预约`.
- Expired token: staff page shows expired state and blocks confirmation.
- Invalid token: staff page shows invalid state.
- Unauthenticated staff: staff page shows login-required or unauthorized state.
- Non-staff user: backend rejects inspection and confirmation.
- Completed booking: backend rejects duplicate verification and staff page shows already verified.
- Cancelled booking: backend rejects verification and staff page shows unavailable.

## Testing Scope

- Backend service tests for token issue, no booking, invalid token, expired token, successful confirmation, duplicate confirmation, and cancelled booking rejection.
- Backend API tests for user token issuance, staff inspection, staff confirmation, unauthenticated rejection, non-staff rejection, expired token, and repeated confirmation.
- Frontend verification for user QR rendering, countdown refresh, empty state, staff detail page, confirmation success, and error states.

## OpenSpec Artifacts

This design updates `openspec/changes/add-personal-qr-frontend`:

- `proposal.md`
- `design.md`
- `specs/personal-qr-ui/spec.md`
- `specs/booking-verification-api/spec.md`
- `specs/booking-verification-ui/spec.md`
- `tasks.md`

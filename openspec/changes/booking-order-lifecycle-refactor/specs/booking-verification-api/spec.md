## MODIFIED Requirements

### Requirement: Issue booking verification token
The system SHALL issue a short-lived backend-signed token for the current user's verifiable booking. A booking is verifiable when its `status` is `in_progress` (renamed from `confirmed`), **or** when its `status` is `pending_start` (renamed from `pending`) **and** its `payment_status` is `paid`.

The `in_progress` value here refers to `bookings.status` in the booking domain. It SHALL NOT be confused with `lesson_schedules.schedule_status` or `course_schedules.schedule_status`, which use the same literal in the scheduling domain and carry different semantics. Likewise `payment_status='pending'` means "awaiting payment" and is unrelated to `status='pending_start'` which means "awaiting start".

The booking summary returned with the token SHALL include a `can_verify` flag computed by the same verifiability rule.

#### Scenario: Token issued for confirmed booking
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）；旧状态值 `confirmed` 已重命名为 `in_progress`。实测可核销前置不止一个状态，`paid` 的 `pending_start` 同样可核销（见下一个 Scenario）。
- **GIVEN** an authenticated user has a booking whose `status` is `in_progress`
- **WHEN** the user requests a booking verification token
- **THEN** the system SHALL return a token, expiration timestamp, verify URL, and booking summary with `can_verify` true

#### Scenario: Token issued for paid pending-start booking
- **GIVEN** an authenticated user has a booking whose `status` is `pending_start` and whose `payment_status` is `paid`
- **WHEN** the user requests a booking verification token
- **THEN** the system SHALL return a token, expiration timestamp, verify URL, and booking summary with `can_verify` true

#### Scenario: Unpaid pending-start booking is not verifiable
- **GIVEN** an authenticated user has a booking whose `status` is `pending_start` and whose `payment_status` is `pending` (awaiting payment)
- **WHEN** the user requests a booking verification token
- **THEN** the system SHALL return an error indicating that no verifiable booking is available

#### Scenario: No confirmed booking available
> 标题沿用主 spec 原名；该 Scenario 覆盖“无任何可核销订单”的通用错误分支。
- **GIVEN** an authenticated user has no booking eligible for verification
- **WHEN** the user requests a booking verification token
- **THEN** the system SHALL return an error indicating that no verifiable booking is available

#### Scenario: Token expires after five minutes
- **GIVEN** the system issues a booking verification token
- **WHEN** the token is inspected
- **THEN** the system SHALL make the token valid for no longer than five minutes

### Requirement: Confirm booking verification
The system SHALL allow authenticated staff or administrators to confirm verification of a valid token and advance the booking status. Verification SHALL be rejected when the bound booking's `status` is `completed`, or when its `status` is neither `in_progress` nor a `paid` `pending_start`.

On successful verification the new status SHALL be `in_progress` when the current booking-local time is still at or before the booking's end time (`date` + `end_time`), and `completed` otherwise. Re-verifying a booking that is already `in_progress` while still within its time window SHALL be rejected as already verified, which makes "already verified within the window" an implicit idempotency marker.

#### Scenario: Confirm verification succeeds
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）。主 spec 原写“确认后置为 `completed`”不完整：实测核销后状态取决于时间窗口——未过 `date + end_time` 时置 `in_progress`，已过时置 `completed`（见下一个 Scenario）。
- **GIVEN** an authenticated staff or administrator has a valid token for a booking whose `status` is `pending_start`, whose `payment_status` is `paid`, and whose end time has not passed
- **WHEN** they confirm verification
- **THEN** the system SHALL update the booking status to `in_progress` and return the verified booking information

#### Scenario: Confirm verification after the booking window
- **GIVEN** an authenticated staff or administrator has a valid token for a verifiable booking whose end time has already passed
- **WHEN** they confirm verification
- **THEN** the system SHALL update the booking status to `completed` and return the verified booking information

#### Scenario: Re-verification within the window is rejected
- **GIVEN** a booking whose `status` is already `in_progress` and whose end time has not passed
- **WHEN** staff attempts to confirm verification again
- **THEN** the system SHALL reject the request as already verified

#### Scenario: Completed booking cannot be verified again
- **GIVEN** a token references a booking whose status is already `completed`
- **WHEN** staff attempts to confirm verification
- **THEN** the system SHALL reject the request as already verified

#### Scenario: Cancelled booking cannot be verified
- **GIVEN** a token references a booking whose status is `cancelled`
- **WHEN** staff attempts to confirm verification
- **THEN** the system SHALL reject the request as not verifiable

#### Scenario: Pending confirmation booking cannot be verified
- **GIVEN** a token references a booking whose status is `pending_confirm`
- **WHEN** staff attempts to confirm verification
- **THEN** the system SHALL reject the request as not verifiable

#### Scenario: Concurrent verification updates only one row
- **GIVEN** two staff members confirm verification of the same token at the same time
- **WHEN** the conditional UPDATE matched by the verifiability rule affects zero rows for the second request
- **THEN** the system SHALL reject the second request as already verified when the refreshed status is `completed`, and as not verifiable otherwise

#### Scenario: Token cannot verify another booking
- **GIVEN** a token was issued for one booking
- **WHEN** staff confirms verification
- **THEN** the system SHALL only update the booking bound to that token

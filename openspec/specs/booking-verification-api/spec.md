## ADDED Requirements

### Requirement: Issue booking verification token
The system SHALL issue a short-lived backend-signed token for the current user's verifiable booking.

#### Scenario: Token issued for confirmed booking
- **GIVEN** an authenticated user has a current `confirmed` booking that can be verified
- **WHEN** the user requests a booking verification token
- **THEN** the system SHALL return a token, expiration timestamp, verify URL, and booking summary

#### Scenario: No confirmed booking available
- **GIVEN** an authenticated user has no booking eligible for verification
- **WHEN** the user requests a booking verification token
- **THEN** the system SHALL return an error indicating that no verifiable booking is available

#### Scenario: Token expires after five minutes
- **GIVEN** the system issues a booking verification token
- **WHEN** the token is inspected
- **THEN** the system SHALL make the token valid for no longer than five minutes

### Requirement: Inspect booking verification token
The system SHALL allow authenticated staff or administrators to inspect a valid verification token and view booking information.

#### Scenario: Staff inspects valid token
- **GIVEN** an authenticated staff or administrator has a valid unexpired token
- **WHEN** they inspect the token
- **THEN** the system SHALL return user-safe booking information, room information, seat information, booking status, and whether the booking can be verified

#### Scenario: Unauthenticated token inspection denied
- **GIVEN** a request has no valid staff or administrator authentication
- **WHEN** it attempts to inspect a verification token
- **THEN** the system SHALL reject the request

#### Scenario: Expired token rejected
- **GIVEN** a token is older than its five-minute validity window
- **WHEN** staff attempts to inspect it
- **THEN** the system SHALL reject the token as expired

### Requirement: Confirm booking verification
The system SHALL allow authenticated staff or administrators to confirm verification of a valid token and mark the booking completed.

#### Scenario: Confirm verification succeeds
- **GIVEN** an authenticated staff or administrator has a valid token for a `confirmed` booking
- **WHEN** they confirm verification
- **THEN** the system SHALL update the booking status to `completed` and return the verified booking information

#### Scenario: Completed booking cannot be verified again
- **GIVEN** a token references a booking whose status is already `completed`
- **WHEN** staff attempts to confirm verification
- **THEN** the system SHALL reject the request as already verified

#### Scenario: Cancelled booking cannot be verified
- **GIVEN** a token references a booking whose status is `cancelled`
- **WHEN** staff attempts to confirm verification
- **THEN** the system SHALL reject the request as not verifiable

#### Scenario: Token cannot verify another booking
- **GIVEN** a token was issued for one booking
- **WHEN** staff confirms verification
- **THEN** the system SHALL only update the booking bound to that token

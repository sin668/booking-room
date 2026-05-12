## ADDED Requirements

### Requirement: Staff verification page route
The system SHALL provide an H5-compatible verification page that can be opened from a WeChat-scanned verification URL.

#### Scenario: Verification URL opens page
- **GIVEN** staff scans a QR code whose content is a verification URL
- **WHEN** the URL opens in WeChat
- **THEN** the system SHALL render the booking verification page and read the token from the URL

### Requirement: Display booking verification details
The system SHALL display booking details after staff authentication and token inspection.

#### Scenario: Valid token displays booking information
- **GIVEN** authenticated staff opens the verification page with a valid token
- **WHEN** the page loads
- **THEN** the system SHALL display booking user information, room, seat, date, time range, price, status, and verification eligibility

#### Scenario: Staff not authenticated
- **GIVEN** unauthenticated staff opens the verification page
- **WHEN** the page attempts to inspect the token
- **THEN** the system SHALL show a login-required or unauthorized state

#### Scenario: Invalid token state
- **GIVEN** staff opens the verification page with an expired, cancelled, completed, or invalid token
- **WHEN** the page loads
- **THEN** the system SHALL show a clear state explaining why confirmation is unavailable

### Requirement: Staff confirms verification
The system SHALL provide a confirmation action that verifies the booking exactly once.

#### Scenario: Confirm button verifies booking
- **GIVEN** authenticated staff is viewing a valid and verifiable booking
- **WHEN** they tap `确认核销`
- **THEN** the system SHALL call the confirmation API and show a success state when the booking is marked completed

#### Scenario: Confirm button prevents duplicate submit
- **GIVEN** staff has tapped `确认核销`
- **WHEN** the confirmation request is in progress or has succeeded
- **THEN** the system SHALL disable repeated confirmation attempts

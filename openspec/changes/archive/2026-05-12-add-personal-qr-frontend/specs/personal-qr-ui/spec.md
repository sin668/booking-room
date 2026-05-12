## ADDED Requirements

### Requirement: Personal QR page route
The system SHALL provide a mobile page route for users to view their personal dynamic booking verification QR code.

#### Scenario: Route opens QR page
- **GIVEN** the user is using the mobile app
- **WHEN** the app navigates to `/pages/qrcode/index`
- **THEN** the system SHALL render the personal learning QR code page with title `我的学习码`

#### Scenario: Page is reachable from profile
- **GIVEN** the user is on the profile page
- **WHEN** the user taps the `我的学习码` entry
- **THEN** the system SHALL navigate to `/pages/qrcode/index`

### Requirement: Dynamic verification QR code
The system SHALL request a backend-issued booking verification token and render the returned verify URL as a scannable QR code.

#### Scenario: QR generated for verifiable booking
- **GIVEN** the user is logged in and has a current `confirmed` booking that can be verified
- **WHEN** the QR page loads
- **THEN** the system SHALL call the booking verification token API and render the returned `verify_url` as a QR code

#### Scenario: QR expiration countdown
- **GIVEN** the QR page has received a token with an expiration time
- **WHEN** the QR code is displayed
- **THEN** the system SHALL display a countdown or expiration indicator showing that the code is short-lived

#### Scenario: QR refresh
- **GIVEN** the current token is expired or close to expiration
- **WHEN** the page refreshes the code automatically or the user taps refresh
- **THEN** the system SHALL request a new token and update the QR code

### Requirement: Personal QR visual layout
The system SHALL implement the QR page visual hierarchy from `prototype/qrcode.html`, adapted for dynamic booking verification.

#### Scenario: Logged-in page content
- **GIVEN** the user is logged in and has a verifiable booking
- **WHEN** the QR page loads successfully
- **THEN** the system SHALL display the user's identity, VIP badge or member marker, QR code area, booking summary, safety tip, countdown, and refresh action

#### Scenario: Prototype style consistency
- **GIVEN** the QR page is displayed on a mobile viewport
- **WHEN** the user views the page
- **THEN** the system SHALL use the light gray page background, white rounded cards, blue primary accents, compact typography, and spacing consistent with `prototype/qrcode.html` and existing `br-app` profile styles

### Requirement: QR page empty and error states
The system SHALL handle unavailable, expired, and failed QR token states without breaking the page.

#### Scenario: No verifiable booking
- **GIVEN** the user is logged in but has no current verifiable booking
- **WHEN** the QR token API reports no available booking
- **THEN** the system SHALL show a clear empty state such as `暂无可核销预约`

#### Scenario: Token generation failure
- **GIVEN** the token API request fails
- **WHEN** the QR page cannot load a verification token
- **THEN** the system SHALL show a retry affordance and a non-blocking failure message

#### Scenario: Unauthenticated QR access
- **GIVEN** the user is not logged in
- **WHEN** the QR page loads
- **THEN** the system SHALL show a login-required state or redirect the user to the login page

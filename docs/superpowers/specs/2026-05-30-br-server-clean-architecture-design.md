# br-server Clean Architecture Refactor Design

## Goal

Refactor `br-server` service-layer code toward Clean Architecture without changing external API behavior. The first implementation phase targets the highest-risk business services: booking, wallet, payment, and booking verification.

## Current State

`br-server` already has a useful coarse structure:

- `app/api/routes`: FastAPI HTTP adapters.
- `app/schemas`: request and response DTOs.
- `app/models`: SQLAlchemy persistence models.
- `app/services`: business logic and integrations.
- `app/core`: configuration, database, security, and infrastructure setup.
- `tests`: strong service and API coverage for booking, wallet, authentication, coupons, payment, and verification.

The main maintainability issue is that several service modules combine too many responsibilities:

- `wallet_service.py` mixes wallet domain rules, recharge order lifecycle, WeChat callback handling, transaction persistence, and promo code redemption.
- `booking_service.py` mixes booking validation, seat availability, coupon mutation, wallet payment, conflict checks, and response assembly.
- `booking_payment_service.py` and `booking_verification_service.py` are closer to domain services but still couple domain rules directly to SQLAlchemy queries and framework-facing data shapes.
- Route files are mostly adapters, but some still understand too much business workflow detail.

## Architecture Direction

Keep the existing FastAPI and SQLAlchemy stack. Do not introduce a new framework or a heavy abstraction layer.

Move toward four explicit layers inside `br-server/app`:

1. **API adapters**
   - FastAPI routes parse requests, apply auth dependencies, call use cases, and map exceptions to HTTP responses.
   - Routes must not perform business decisions.

2. **Application use cases**
   - Orchestrate a complete business workflow, such as creating a booking or handling a wallet recharge callback.
   - Own transaction boundaries where the existing code already requires atomic behavior.
   - Depend on domain services and repository interfaces.

3. **Domain services**
   - Hold pure or near-pure business rules: booking time validation, cancellation policy, wallet balance checks, coupon applicability, payment status transitions, verification token rules.
   - Prefer plain functions or small classes with explicit inputs and outputs.

4. **Infrastructure adapters**
   - SQLAlchemy repositories, external clients, storage providers, and WeChat/SMS integrations.
   - Hide query and SDK details behind focused methods.

## Initial Refactor Scope

The first implementation plan should cover `br-server` only.

### Included

- Extract shared money and transaction helpers from wallet and booking payment paths.
- Extract booking conflict and time-window rules from `booking_service.py`.
- Extract wallet ledger operations from `wallet_service.py`.
- Extract verification token encode/decode and validation policy from `booking_verification_service.py` where useful.
- Introduce repository interfaces only where they remove current duplication or make tests cleaner.
- Keep existing public route behavior and response payloads stable.
- Add or preserve tests before each behavior-affecting refactor.

### Excluded

- No database schema changes.
- No API path, response, or auth contract changes.
- No frontend changes in this phase.
- No broad deletion of `br-admin` template code.
- No global formatting churn.
- No rewrite of all services into classes if simple functions already work.

## Proposed Module Shape

Target structure for the first phase:

```text
br-server/app/
  application/
    booking_use_cases.py
    wallet_use_cases.py
    verification_use_cases.py
  domain/
    booking_rules.py
    wallet_rules.py
    payment_rules.py
    verification_rules.py
  repositories/
    booking_repository.py
    wallet_repository.py
    coupon_repository.py
    seat_repository.py
  services/
    booking_service.py
    wallet_service.py
    booking_payment_service.py
    booking_verification_service.py
```

The existing `services` modules can remain as compatibility facades during migration. This reduces route churn and allows small commits.

## Refactor Sequence

1. **Baseline verification**
   - Run focused tests for wallet, booking, payment, and verification.
   - Record current failures or warnings before code changes.

2. **Extract pure rules**
   - Move deterministic validation and formatting logic into `app/domain`.
   - Add unit tests for these rules first.
   - Update existing services to call extracted rules.

3. **Extract repository adapters**
   - Start with read/write clusters that are duplicated or deeply nested.
   - Keep SQLAlchemy session ownership unchanged unless a test proves the boundary needs adjustment.

4. **Introduce application use cases**
   - Move orchestration out of oversized service classes/functions.
   - Keep existing public service function names as wrappers if routes or tests already depend on them.

5. **Clean up compatibility layer**
   - Remove duplicate private helpers only after tests prove the new path is used.
   - Keep public exports stable until callers are migrated.

## Testing Strategy

Use TDD for each extraction:

- Write a focused test for the extracted rule or use case.
- Verify it fails before implementation.
- Move minimal logic.
- Run the focused test.
- Run the existing affected service/API tests.

Recommended baseline commands:

```powershell
python -m pytest tests/test_booking_payment_service.py -q
python -m pytest tests/test_wallet_service.py -q
python -m pytest tests/test_booking_verification_service.py -q
python -m pytest tests/test_api_booking.py -q
python -m pytest tests/test_api_wallet.py -q
```

Full backend verification:

```powershell
python -m pytest
```

## Risks

- Booking and wallet flows mutate multiple tables. Refactors must preserve transaction ordering and rollback behavior.
- Coupon usage and restoration are coupled to booking create/cancel paths. These need targeted regression tests.
- WeChat payment callbacks require idempotency and signature handling. Avoid changing callback semantics in the first pass.
- Existing tests are broad and valuable but large. Small focused tests should be added around extracted rules to keep feedback fast.

## Success Criteria

- Existing backend tests for booking, wallet, payment, and verification pass.
- New domain modules have focused tests.
- Route behavior is unchanged.
- Largest business services are reduced by moving pure rules and persistence clusters into named modules.
- No unrelated frontend or admin changes are included.


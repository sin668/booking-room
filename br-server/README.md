# br-server

FastAPI backend service for the booking-room project.

## Admin RBAC Seed

The admin RBAC dynamic settings migration separates schema changes from default business data. Run Alembic first, then run the idempotent seed command:

```bash
cd br-server
alembic upgrade head
python -m app.services.seed_admin
```

The seed command initializes the default administrator, `super_admin` role, default menu tree, button permissions, and system settings. It must be safe to run more than once without duplicating records.

Development defaults:

- Username: `admin`
- Password: `123456`

Supported environment overrides:

```bash
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=change-me
ADMIN_DEFAULT_EMAIL=admin@example.com
```

Production must set `ADMIN_DEFAULT_PASSWORD` explicitly. The seed command should refuse to create a weak default administrator in production when that variable is missing.

## Admin Auth Migration

New admin APIs use bearer authentication:

```http
Authorization: Bearer <admin access token>
```

The bearer token is issued by `POST /api/v1/admin/auth/login` and read by protected admin APIs through the admin context dependency. Legacy `X-Admin-Token` remains only as a temporary compatibility and emergency super-admin path while br-admin and existing management APIs finish migrating.

Target permission behavior:

- Missing credentials return HTTP 401.
- A valid admin bearer token resolves the current admin, roles, and permission codes.
- Super administrators bypass permission-code checks.
- Non-super administrators need the route-specific permission code.
- A valid legacy `X-Admin-Token` is treated as a temporary super-admin context.
- Invalid legacy tokens return HTTP 401.

## Verification Commands

```bash
cd br-server
pytest
python -m app.services.seed_admin
python -m app.services.seed_admin
```

After the seed command exists, compare admin RBAC table counts before and after the second seed run to confirm idempotency.

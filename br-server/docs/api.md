# Booking Room API Documentation

This documents the API endpoints and schema changes for the booking-room project.

## User Authentication API

### App User Login (`POST /api/v1/auth/login`)

**Schema Change (unified-user-access):** The `UserLogin` schema now accepts both `phone` and `username` fields for login. At least one field must be provided.

#### Request Body

```json
{
  "phone": "13800138000",  // Optional, for app users
  "username": "user123",  // Optional, for admin or app users
  "password": "password123"
}
```

**Validation Rules:**
- At least one of `phone` or `username` must be provided
- Both fields can be provided (the system checks both)
- If both provided, either can match for successful login

#### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "phone": "13800138000",
    "username": "user123",
    "nickname": "User Name",
    "user_source": "app",
    "user_type": "normal-user",
    "status": "active",
    "avatar": null,
    "balance": 1000
  }
}
```

### Admin User Login (`POST /api/v1/admin/auth/login`)

**Schema Change (unified-user-access):** The `AdminLoginRequest` schema now accepts both `username` and `phone` fields for login. At least one field must be provided.

#### Request Body

```json
{
  "username": "admin",  // Optional, for admin users
  "phone": "13800138000",  // Optional, for app users (if they have admin role)
  "password": "password123"
}
```

**Validation Rules:**
- At least one of `username` or `phone` must be provided
- Both fields can be provided (the system checks both)
- The user must have admin privileges (user_type='super-admin' or has admin roles)

#### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "admin",
    "phone": "13800138000",
    "nickname": "Admin User",
    "user_source": "admin",
    "user_type": "super-admin",
    "status": "active",
    "roles": [
      {"id": 1, "name": "超级管理员", "code": "super_admin"}
    ]
  }
}
```

## User Model Changes

### Unified User Model

**Schema Change (unified-user-access):** The `User` and `AdminUser` models have been unified into a single `User` model.

**Key Constraints:**
- `phone` must be unique across all users (regardless of user_source)
- `username` must be unique across all users (regardless of user_source)
- `user_source` field tracks registration source but is not used for auth filtering

**Fields:**
- `id`: UUID primary key
- `phone`: Optional, unique, used for app user login
- `username`: Optional, unique, used for admin user login
- `password_hash`: Hashed password (bcrypt)
- `nickname`: Display name
- `user_source`: Either "app" or "admin" (CHECK constraint ck_users_user_source)
- `status`: "active", "banned", or "disabled"
- `balance`: Decimal wallet balance
- `user_type`: Either "super-admin" or "normal-user" (CHECK constraint ck_users_user_type); app-source users are always "normal-user"
- `roles`: Many-to-many relationship with AdminRole

## Data Migration Notes

When migrating from the old separate `User` and `AdminUser` models to the unified `User` model:

1. **Run the uniqueness check script:**
   ```bash
   cd br-server
   psql $DATABASE_URL -f scripts/check_user_uniqueness.sql
   ```

2. **If duplicates exist, manual cleanup is required** before the unified model constraints can be enforced

3. **After cleanup, run Alembic migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Seed the default admin:**
   ```bash
   python -m app.services.seed_admin
   ```

## User Type Usage Guidelines

The `user_source` field is **not used for authentication filtering**. Instead, it serves these purposes:

### Valid Uses:
- **Admin UI filtering** - Filter user lists by type in admin management screens
- **User creation defaults** - Set appropriate type when creating users via admin API
- **Analytics/reporting** - Track user registration sources
- **Model validation** - CHECK constraint ensures only "app" or "admin" values

The `user_type` field ("super-admin"/"normal-user") controls admin privilege level: super admins get all menus and data scope; normal users follow role-based menus and creator-owned data scope.

### Invalid Uses (DO NOT):
- **Auth/login query filters** - Never use `User.user_source == X` in login or registration queries
- **Permission checks** - Use roles and permissions system instead
- **User lookup** - Lookup by phone/username directly without type filter

## Testing

The unified user model is tested in `tests/test_unified_user_model.py`:

- Phone uniqueness constraint
- Username uniqueness constraint
- User type defaults (app users default to "app", admin users explicitly set "admin")
- Invalid user type rejection (CHECK constraint)
- Role relationships

Run tests:
```bash
cd br-server
pytest tests/test_unified_user_model.py -v
```
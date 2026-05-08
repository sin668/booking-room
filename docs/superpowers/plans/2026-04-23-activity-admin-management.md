# Activity Admin Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement admin CRUD management for activities in br-server (FastAPI) and br-admin (Vue3 + NaiveUI), with fixed-token auth and local file upload.

**Architecture:** Backend adds admin routes under `/api/v1/admin/` with `X-Admin-Token` header auth. New schemas extend existing activity models. Frontend adds activity list page using existing BasicTable/Modal patterns. File upload stores to local `uploads/` directory.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy, Pydantic, pytest (backend) / Vue3, NaiveUI, Alova, TypeScript (frontend)

---

### Task 1: Add ADMIN_TOKEN config

**Files:**
- Modify: `br-server/app/core/config.py:4-5`

- [ ] **Step 1: Add ADMIN_TOKEN setting**

```python
# Add after line 5 (after ALIYUN_CAPTCHA_SCENE_ID)
    # Admin
    ADMIN_TOKEN: str = ""
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/core/config.py
git commit -m "feat(config): add ADMIN_TOKEN setting"
```

---

### Task 2: Add admin auth dependency

**Files:**
- Modify: `br-server/app/api/dependencies.py`

- [ ] **Step 1: Add get_current_admin dependency**

Append to end of file:

```python
from fastapi import Header


async def get_current_admin(x_admin_token: str | None = Header(None)) -> None:
    """Validate admin token from X-Admin-Token header."""
    if not settings.ADMIN_TOKEN or x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的管理员凭证",
        )
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/api/dependencies.py
git commit -m "feat(auth): add get_current_admin dependency with fixed token"
```

---

### Task 3: Add admin activity schemas

**Files:**
- Modify: `br-server/app/schemas/activity.py`

- [ ] **Step 1: Write schemas**

Replace entire file with:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ActivityResponse(BaseModel):
    id: int
    title: str
    description: str | None
    cover_image: str | None
    participant_count: int

    model_config = ConfigDict(from_attributes=True)


class ActivityCreate(BaseModel):
    title: str = Field(..., max_length=100, description="活动标题")
    description: str | None = Field(None, max_length=500, description="活动描述")
    cover_image: str | None = Field(None, max_length=512, description="封面图 URL")
    participant_count: int = Field(default=0, ge=0, description="参与人数")
    sort_order: int = Field(default=0, description="排序值")
    is_active: bool = Field(default=True, description="是否上架")


class ActivityUpdate(BaseModel):
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    cover_image: str | None = Field(None, max_length=512)
    participant_count: int | None = Field(None, ge=0)
    sort_order: int | None = None
    is_active: bool | None = None


class ActivityAdminResponse(BaseModel):
    id: int
    title: str
    description: str | None
    cover_image: str | None
    participant_count: int
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ActivityAdminResponse]


class ActivityStatusUpdate(BaseModel):
    is_active: bool


class UploadResponse(BaseModel):
    url: str
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/schemas/activity.py
git commit -m "feat(schemas): add admin activity and upload schemas"
```

---

### Task 4: Add admin activity service methods

**Files:**
- Modify: `br-server/app/services/activity_service.py`

- [ ] **Step 1: Write admin service methods**

Replace entire file with:

```python
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity


async def list_active_activities(db: AsyncSession) -> list[Activity]:
    """Return all active activities ordered by sort_order ascending."""
    result = await db.execute(
        select(Activity)
        .where(Activity.is_active.is_(True))
        .order_by(Activity.sort_order.asc())
    )
    return list(result.scalars().all())


async def list_activities(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    is_active: bool | None = None,
) -> dict:
    """Return paginated activity list with optional keyword search and status filter."""
    query = select(Activity)
    count_query = select(func.count(Activity.id))

    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            Activity.title.ilike(pattern) | Activity.description.ilike(pattern)
        )
        count_query = count_query.where(
            Activity.title.ilike(pattern) | Activity.description.ilike(pattern)
        )

    if is_active is not None:
        query = query.where(Activity.is_active.is_(is_active))
        count_query = count_query.where(Activity.is_active.is_(is_active))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size
    if offset > total and total > 0:
        offset = (total_pages - 1) * page_size

    query = query.order_by(Activity.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {"total": total, "page": page, "page_size": page_size, "items": items}


async def get_activity_by_id(db: AsyncSession, activity_id: int) -> Activity | None:
    """Return a single activity by ID, or None if not found."""
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    return result.scalar_one_or_none()


async def create_activity(db: AsyncSession, data: dict) -> Activity:
    """Create a new activity."""
    activity = Activity(**data)
    db.add(activity)
    await db.flush()
    await db.refresh(activity)
    return activity


async def update_activity(db: AsyncSession, activity: Activity, data: dict) -> Activity:
    """Update an existing activity with the given fields."""
    for key, value in data.items():
        if value is not None:
            setattr(activity, key, value)
    await db.flush()
    await db.refresh(activity)
    return activity


async def delete_activity(db: AsyncSession, activity: Activity) -> None:
    """Delete an activity."""
    await db.delete(activity)
    await db.flush()


async def toggle_activity_status(db: AsyncSession, activity: Activity, is_active: bool) -> Activity:
    """Toggle activity active status."""
    activity.is_active = is_active
    await db.flush()
    await db.refresh(activity)
    return activity
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/services/activity_service.py
git commit -m "feat(service): add admin activity CRUD and pagination methods"
```

---

### Task 5: Create admin activity routes

**Files:**
- Create: `br-server/app/api/routes/admin_activity.py`

- [ ] **Step 1: Write admin activity router**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.schemas.activity import (
    ActivityAdminResponse,
    ActivityCreate,
    ActivityListResponse,
    ActivityStatusUpdate,
    ActivityUpdate,
)
from app.services import activity_service

router = APIRouter(prefix="/api/v1/admin/activities", tags=["admin-activities"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> ActivityListResponse:
    return await activity_service.list_activities(db, page=page, page_size=page_size, keyword=keyword, is_active=is_active)


@router.post("", response_model=ActivityAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(data: ActivityCreate, db: AsyncSession = Depends(get_db)) -> ActivityAdminResponse:
    activity = await activity_service.create_activity(db, data.model_dump())
    return activity


@router.get("/{activity_id}", response_model=ActivityAdminResponse)
async def get_activity(activity_id: int, db: AsyncSession = Depends(get_db)) -> ActivityAdminResponse:
    activity = await activity_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    return activity


@router.put("/{activity_id}", response_model=ActivityAdminResponse)
async def update_activity(activity_id: int, data: ActivityUpdate, db: AsyncSession = Depends(get_db)) -> ActivityAdminResponse:
    activity = await activity_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    return await activity_service.update_activity(db, activity, data.model_dump(exclude_unset=True))


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(activity_id: int, db: AsyncSession = Depends(get_db)) -> None:
    activity = await activity_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    await activity_service.delete_activity(db, activity)


@router.patch("/{activity_id}/status", response_model=ActivityAdminResponse)
async def toggle_status(activity_id: int, data: ActivityStatusUpdate, db: AsyncSession = Depends(get_db)) -> ActivityAdminResponse:
    activity = await activity_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    return await activity_service.toggle_activity_status(db, activity, data.is_active)
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/api/routes/admin_activity.py
git commit -m "feat(routes): add admin activity CRUD routes"
```

---

### Task 6: Create file upload route

**Files:**
- Create: `br-server/app/api/routes/upload.py`

- [ ] **Step 1: Write upload router**

```python
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pathlib import Path

from app.api.dependencies import get_current_admin
from app.schemas.activity import UploadResponse

router = APIRouter(prefix="/api/v1/admin", tags=["admin-upload"], dependencies=[Depends(get_current_admin)])

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="缺少文件")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="仅支持图片文件")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="文件大小不能超过5MB")

    today = datetime.now().strftime("%Y/%m/%d")
    dir_path = UPLOAD_DIR / today
    dir_path.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = dir_path / filename

    with open(file_path, "wb") as f:
        f.write(content)

    return UploadResponse(url=f"/uploads/{today}/{filename}")
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/api/routes/upload.py
git commit -m "feat(routes): add file upload endpoint"
```

---

### Task 7: Register new routes and static files in main.py

**Files:**
- Modify: `br-server/app/main.py`

- [ ] **Step 1: Register routes and static file serving**

Add these imports at the top (after existing imports):

```python
from fastapi.staticfiles import StaticFiles
from app.api.routes.admin_activity import router as admin_activity_router
from app.api.routes.upload import router as upload_router
```

Add these lines before `# Include routers` section:

```python
# Static files for uploads
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
```

Add these lines in the `# Include routers` section:

```python
app.include_router(upload_router)
app.include_router(admin_activity_router)
```

Also add `from pathlib import Path` at the top imports.

- [ ] **Step 2: Commit**

```bash
git add br-server/app/main.py
git commit -m "feat(main): register admin routes and upload static files"
```

---

### Task 8: Write admin activity API tests

**Files:**
- Create: `br-server/tests/test_api_admin_activity.py`

- [ ] **Step 1: Write tests**

```python
"""Integration tests for admin activity API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.schemas.activity import ActivityCreate

ADMIN_TOKEN = "test-admin-token"


@pytest.fixture
def admin_headers():
    return {"X-Admin-Token": ADMIN_TOKEN}


@pytest.fixture
async def seed_activities(db_session: AsyncSession):
    db_session.add(Activity(title="Active Activity 1", description="Desc 1", participant_count=100, sort_order=1, is_active=True))
    db_session.add(Activity(title="Active Activity 2", participant_count=200, sort_order=2, is_active=True))
    db_session.add(Activity(title="Inactive Activity", is_active=False))
    await db_session.flush()


class TestAdminAuth:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client: AsyncClient, seed_activities):
        resp = await client.get("/api/v1/admin/activities")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_token_returns_401(self, client: AsyncClient, seed_activities):
        resp = await client.get("/api/v1/admin/activities", headers={"X-Admin-Token": "wrong"})
        assert resp.status_code == 401


class TestAdminListActivities:
    @pytest.mark.asyncio
    async def test_list_all_activities(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities?page=1&page_size=2", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_keyword_search(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities?keyword=Inactive", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Inactive Activity"

    @pytest.mark.asyncio
    async def test_filter_by_active_true(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities?is_active=true", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_filter_by_active_false(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities?is_active=false", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_empty_result(self, client: AsyncClient, admin_headers):
        resp = await client.get("/api/v1/admin/activities", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestAdminCreateActivity:
    @pytest.mark.asyncio
    async def test_create_activity(self, client: AsyncClient, admin_headers):
        resp = await client.post(
            "/api/v1/admin/activities",
            json={"title": "New Activity", "description": "Test desc", "participant_count": 50, "sort_order": 3},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Activity"
        assert data["is_active"] is True
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_create_with_defaults(self, client: AsyncClient, admin_headers):
        resp = await client.post("/api/v1/admin/activities", json={"title": "Minimal"}, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["participant_count"] == 0
        assert data["sort_order"] == 0
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_missing_title(self, client: AsyncClient, admin_headers):
        resp = await client.post("/api/v1/admin/activities", json={}, headers=admin_headers)
        assert resp.status_code == 422


class TestAdminGetActivity:
    @pytest.mark.asyncio
    async def test_get_activity(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities/1", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Active Activity 1"
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.get("/api/v1/admin/activities/999", headers=admin_headers)
        assert resp.status_code == 404


class TestAdminUpdateActivity:
    @pytest.mark.asyncio
    async def test_update_activity(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.put(
            "/api/v1/admin/activities/1",
            json={"title": "Updated Title"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.put("/api/v1/admin/activities/999", json={"title": "X"}, headers=admin_headers)
        assert resp.status_code == 404


class TestAdminDeleteActivity:
    @pytest.mark.asyncio
    async def test_delete_activity(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.delete("/api/v1/admin/activities/1", headers=admin_headers)
        assert resp.status_code == 204

        resp = await client.get("/api/v1/admin/activities/1", headers=admin_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.delete("/api/v1/admin/activities/999", headers=admin_headers)
        assert resp.status_code == 404


class TestAdminToggleStatus:
    @pytest.mark.asyncio
    async def test_toggle_to_inactive(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.patch("/api/v1/admin/activities/1/status", json={"is_active": False}, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_toggle_to_active(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.patch("/api/v1/admin/activities/3/status", json={"is_active": True}, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_toggle_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.patch("/api/v1/admin/activities/999/status", json={"is_active": True}, headers=admin_headers)
        assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd br-server && python -m pytest tests/test_api_admin_activity.py -v`

Note: This requires adding `ADMIN_TOKEN=test-admin-token` to the test environment. The conftest needs an override for `get_current_admin`. Add to `conftest.py`:

```python
from unittest.mock import patch
from app.api.dependencies import get_current_admin

# In the client fixture, after existing overrides:
app.dependency_overrides[get_current_admin] = lambda: None
```

Then run tests again — they should pass.

- [ ] **Step 3: Commit**

```bash
git add br-server/tests/test_api_admin_activity.py br-server/tests/conftest.py
git commit -m "test: add admin activity API integration tests"
```

---

### Task 9: Write file upload tests

**Files:**
- Create: `br-server/tests/test_api_upload.py`

- [ ] **Step 1: Write tests**

```python
"""Integration tests for file upload API endpoint."""

import io

import pytest
from httpx import AsyncClient

ADMIN_TOKEN = "test-admin-token"


@pytest.fixture
def admin_headers():
    return {"X-Admin-Token": ADMIN_TOKEN}


class TestUploadAPI:
    @pytest.mark.asyncio
    async def test_upload_image(self, client: AsyncClient, admin_headers, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        fake_file = io.BytesIO(b"\x89PNG\r\n\x1a\nfake-png-content")
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("photo.png", fake_file, "image/png")},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"].startswith("/uploads/")
        assert data["url"].endswith(".png")

    @pytest.mark.asyncio
    async def test_upload_non_image_returns_422(self, client: AsyncClient, admin_headers):
        fake_file = io.BytesIO(b"not-an-image")
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("script.exe", fake_file, "application/octet-stream")},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        assert "仅支持图片文件" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_oversized_file_returns_422(self, client: AsyncClient, admin_headers):
        large_content = b"x" * (5 * 1024 * 1024 + 1)
        fake_file = io.BytesIO(b"\x89PNG\r\n\x1a\n" + large_content)
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("big.png", fake_file, "image/png")},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        assert "文件大小不能超过5MB" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_no_token_returns_401(self, client: AsyncClient):
        fake_file = io.BytesIO(b"\x89PNG\r\n\x1a\n")
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("photo.png", fake_file, "image/png")},
        )
        assert resp.status_code == 401
```

- [ ] **Step 2: Run tests**

Run: `cd br-server && python -m pytest tests/test_api_upload.py -v`

- [ ] **Step 3: Commit**

```bash
git add br-server/tests/test_api_upload.py
git commit -m "test: add file upload API integration tests"
```

---

### Task 10: Run full backend test suite

**Files:** None

- [ ] **Step 1: Run all tests**

Run: `cd br-server && python -m pytest tests/ -v --tb=short`

Expected: All tests pass (existing + new admin activity + upload tests).

- [ ] **Step 2: Fix any failures and re-run**

---

### Task 11: Create frontend activity API module

**Files:**
- Create: `br-admin/src/api/activity/index.ts`

- [ ] **Step 1: Write activity API functions**

```typescript
import { Alova } from '@/utils/http/alova/index';

export interface ActivityItem {
  id: number;
  title: string;
  description: string | null;
  cover_image: string | null;
  participant_count: number;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ActivityListResult {
  total: number;
  page: number;
  page_size: number;
  items: ActivityItem[];
}

export interface ActivityFormParams {
  title: string;
  description?: string | null;
  cover_image?: string | null;
  participant_count?: number;
  sort_order?: number;
  is_active?: boolean;
}

export function getActivityList(params: Record<string, any>) {
  return Alova.Get<ActivityListResult>('/api/v1/admin/activities', { params });
}

export function createActivity(data: ActivityFormParams) {
  return Alova.Post<ActivityItem>('/api/v1/admin/activities', data);
}

export function getActivityById(id: number) {
  return Alova.Get<ActivityItem>(`/api/v1/admin/activities/${id}`);
}

export function updateActivity(id: number, data: Partial<ActivityFormParams>) {
  return Alova.Put<ActivityItem>(`/api/v1/admin/activities/${id}`, data);
}

export function deleteActivity(id: number) {
  return Alova.Delete(`/api/v1/admin/activities/${id}`);
}

export function toggleActivityStatus(id: number, is_active: boolean) {
  return Alova.Patch<ActivityItem>(`/api/v1/admin/activities/${id}/status`, { is_active });
}

export function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return Alova.Post<{ url: string }>('/api/v1/admin/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add br-admin/src/api/activity/
git commit -m "feat(api): add activity admin and upload API functions"
```

---

### Task 12: Create activity list page

**Files:**
- Create: `br-admin/src/views/activity/list/columns.ts`
- Create: `br-admin/src/views/activity/list/index.vue`

- [ ] **Step 1: Write column definitions**

```typescript
// br-admin/src/views/activity/list/columns.ts
import { h } from 'vue';
import { NAvatar, NTag, NImage } from 'naive-ui';
import { BasicColumn } from '@/components/Table';
import type { ActivityItem } from '@/api/activity';

export const columns: BasicColumn<ActivityItem>[] = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '标题', key: 'title', width: 180, ellipsis: { tooltip: true } },
  { title: '描述', key: 'description', width: 200, ellipsis: { tooltip: true } },
  {
    title: '封面图',
    key: 'cover_image',
    width: 100,
    render(row) {
      return row.cover_image
        ? h(NImage, { src: row.cover_image, width: 60, height: 40, objectFit: 'cover', previewDisabled: true }, null)
        : h('span', { style: 'color: #999' }, '暂无');
    },
  },
  { title: '参与人数', key: 'participant_count', width: 90 },
  { title: '排序', key: 'sort_order', width: 70 },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render(row) {
      return h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, { default: () => (row.is_active ? '已上架' : '已下架') });
    },
  },
  { title: '创建时间', key: 'created_at', width: 170 },
];
```

- [ ] **Step 2: Write list page**

```vue
<!-- br-admin/src/views/activity/list/index.vue -->
<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <BasicForm @register="register" @submit="handleSubmit" @reset="handleReset" />
    </n-card>
    <n-card :bordered="false">
      <BasicTable
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row: ActivityItem) => row.id"
        ref="actionRef"
        :actionColumn="actionColumn"
        :scroll-x="1100"
        :striped="true"
      >
        <template #tableTitle>
          <n-button type="primary" @click="handleCreate">
            <template #icon><n-icon><PlusOutlined /></n-icon></template>
            新建活动
          </n-button>
        </template>
      </BasicTable>

      <ActivityEditModal
        v-model:show="showModal"
        :editData="editData"
        @success="handleSuccess"
      />
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, reactive, ref } from 'vue';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import { columns } from './columns';
  import ActivityEditModal from './ActivityEditModal.vue';
  import {
    getActivityList,
    deleteActivity,
    toggleActivityStatus,
    type ActivityItem,
  } from '@/api/activity';
  import { PlusOutlined } from '@vicons/antd';
  import type { FormSchema } from '@/components/Form';

  const schemas: FormSchema[] = [
    { field: 'keyword', component: 'NInput', label: '关键词', componentProps: { placeholder: '搜索标题或描述' } },
    {
      field: 'is_active',
      component: 'NSelect',
      label: '状态',
      componentProps: {
        placeholder: '全部',
        options: [
          { label: '全部', value: '' },
          { label: '已上架', value: 'true' },
          { label: '已下架', value: 'false' },
        ],
      },
    },
  ];

  const actionRef = ref();
  const showModal = ref(false);
  const editData = ref<ActivityItem | null>(null);

  const [register, { getFieldsValue, resetFields }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas,
  });

  const loadDataTable = async (params: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...params };
    if (queryParams.is_active === '') {
      delete queryParams.is_active;
    } else if (queryParams.is_active === 'true') {
      queryParams.is_active = true;
    } else if (queryParams.is_active === 'false') {
      queryParams.is_active = false;
    }
    return await getActivityList(queryParams);
  };

  const actionColumn = reactive({
    width: 200,
    title: '操作',
    key: 'action',
    fixed: 'right',
    render(record: ActivityItem) {
      return h(TableAction as any, {
        style: 'button',
        actions: [
          { label: '编辑', onClick: () => handleEdit(record) },
          { label: '删除', onClick: () => handleDelete(record) },
        ],
        dropDownActions: [
          {
            label: record.is_active ? '下架' : '上架',
            onClick: () => handleToggleStatus(record, !record.is_active),
          },
        ],
      });
    },
  });

  function handleCreate() {
    editData.value = null;
    showModal.value = true;
  }

  function handleEdit(record: ActivityItem) {
    editData.value = record;
    showModal.value = true;
  }

  function handleDelete(record: ActivityItem) {
    window['$dialog'].warning({
      title: '确认删除',
      content: `确定要删除活动「${record.title}」吗？此操作不可恢复。`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        await deleteActivity(record.id);
        window['$message'].success('删除成功');
        actionRef.value.reload();
      },
    });
  }

  async function handleToggleStatus(record: ActivityItem, is_active: boolean) {
    await toggleActivityStatus(record.id, is_active);
    window['$message'].success(is_active ? '已上架' : '已下架');
    actionRef.value.reload();
  }

  function handleSuccess() {
    showModal.value = false;
    actionRef.value.reload();
  }

  function handleSubmit() {
    actionRef.value.reload();
  }

  function handleReset() {
    actionRef.value.reload();
  }
</script>
```

- [ ] **Step 3: Commit**

```bash
git add br-admin/src/views/activity/
git commit -m "feat(admin): add activity list page with search, pagination, and actions"
```

---

### Task 13: Create activity edit modal

**Files:**
- Create: `br-admin/src/views/activity/list/ActivityEditModal.vue`

- [ ] **Step 1: Write edit modal component**

```vue
<!-- br-admin/src/views/activity/list/ActivityEditModal.vue -->
<template>
  <n-modal v-model:show="innerShow" :show-icon="false" preset="dialog" :title="editData ? '编辑活动' : '新建活动'" style="width: 600px">
    <n-form ref="formRef" :model="formValues" :rules="rules" label-placement="left" :label-width="80" class="py-4">
      <n-form-item label="标题" path="title">
        <n-input v-model:value="formValues.title" placeholder="请输入活动标题" :maxlength="100" show-count />
      </n-form-item>
      <n-form-item label="描述" path="description">
        <n-input v-model:value="formValues.description" type="textarea" placeholder="请输入活动描述" :maxlength="500" show-count :rows="3" />
      </n-form-item>
      <n-form-item label="封面图" path="cover_image">
        <n-upload
          :max="1"
          accept="image/*"
          :custom-request="handleUpload"
          :show-file-list="false"
        >
          <n-button>上传图片</n-button>
        </n-upload>
        <n-image
          v-if="formValues.cover_image"
          :src="formValues.cover_image"
          width="80"
          height="80"
          object-fit="cover"
          preview-disabled
          style="margin-left: 12px; border-radius: 4px"
        />
      </n-form-item>
      <n-form-item label="参与人数" path="participant_count">
        <n-input-number v-model:value="formValues.participant_count" :min="0" placeholder="0" style="width: 100%" />
      </n-form-item>
      <n-form-item label="排序值" path="sort_order">
        <n-input-number v-model:value="formValues.sort_order" placeholder="0" style="width: 100%" />
      </n-form-item>
      <n-form-item label="是否上架" path="is_active">
        <n-switch v-model:value="formValues.is_active" />
      </n-form-item>
    </n-form>
    <template #action>
      <n-space>
        <n-button @click="innerShow = false">取消</n-button>
        <n-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, reactive, ref, watch } from 'vue';
  import { createActivity, updateActivity, uploadFile, type ActivityFormParams, type ActivityItem } from '@/api/activity';
  import type { FormRules, FormInst, UploadFileInfo } from 'naive-ui';

  const props = defineProps<{ show: boolean; editData: ActivityItem | null }>();
  const emit = defineEmits<{ (e: 'update:show', val: boolean): void; (e: 'success'): void }>();

  const innerShow = computed({
    get: () => props.show,
    set: (val) => emit('update:show', val),
  });

  const formRef = ref<FormInst | null>(null);
  const submitLoading = ref(false);

  const defaultValues: ActivityFormParams = {
    title: '',
    description: '',
    cover_image: '',
    participant_count: 0,
    sort_order: 0,
    is_active: true,
  };

  const formValues = reactive<ActivityFormParams>({ ...defaultValues });

  const rules: FormRules = {
    title: { required: true, message: '标题不能为空', trigger: ['blur', 'input'] },
  };

  watch(() => props.show, (val) => {
    if (val) {
      if (props.editData) {
        Object.assign(formValues, {
          title: props.editData.title,
          description: props.editData.description || '',
          cover_image: props.editData.cover_image || '',
          participant_count: props.editData.participant_count,
          sort_order: props.editData.sort_order,
          is_active: props.editData.is_active,
        });
      } else {
        Object.assign(formValues, { ...defaultValues });
      }
    }
  });

  async function handleUpload({ file, onFinish, onError }: { file: UploadFileInfo; onFinish: () => void; onError: () => void }) {
    try {
      const res = await uploadFile(file.file as File);
      formValues.cover_image = res.url;
      onFinish();
    } catch {
      onError();
      window['$message'].error('上传失败');
    }
  }

  async function handleSubmit() {
    try {
      await formRef.value?.validate();
    } catch {
      return;
    }
    submitLoading.value = true;
    try {
      if (props.editData) {
        await updateActivity(props.editData.id, formValues);
        window['$message'].success('更新成功');
      } else {
        await createActivity(formValues);
        window['$message'].success('创建成功');
      }
      emit('success');
    } catch {
      window['$message'].error('操作失败');
    } finally {
      submitLoading.value = false;
    }
  }
</script>
```

- [ ] **Step 2: Commit**

```bash
git add br-admin/src/views/activity/list/ActivityEditModal.vue
git commit -m "feat(admin): add activity edit modal with image upload"
```

---

### Task 14: Add activity router and menu

**Files:**
- Create: `br-admin/src/router/modules/activity.ts`

- [ ] **Step 1: Write activity router module**

```typescript
import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
import { CalendarOutline } from '@vicons/ionicons5';
import { renderIcon } from '@/utils/index';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/activity',
    name: 'Activity',
    redirect: '/activity/list',
    component: Layout,
    meta: {
      title: '活动管理',
      icon: renderIcon(CalendarOutline),
      sort: 2,
    },
    children: [
      {
        path: 'list',
        name: 'activity_list',
        meta: { title: '活动列表' },
        component: () => import('@/views/activity/list/index.vue'),
      },
    ],
  },
];

export default routes;
```

- [ ] **Step 2: Commit**

```bash
git add br-admin/src/router/modules/activity.ts
git commit -m "feat(router): add activity management route module"
```

---

### Task 15: Verify frontend builds

**Files:** None

- [ ] **Step 1: Run frontend dev build**

Run: `cd br-admin && npm run build`

Expected: Build completes without errors. If there are TypeScript or import errors, fix them and re-run.

- [ ] **Step 2: Fix any build errors and re-run**

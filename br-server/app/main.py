from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.activity import router as activity_router
from app.api.routes.admin_activity import router as admin_activity_router
from app.api.routes.auth import router as auth_router
from app.api.routes.banner import router as banner_router
from app.api.routes.seat import router as seat_router
from app.api.routes.study_room import router as study_room_router
from app.api.routes.upload import router as upload_router
from app.api.routes.user import router as user_router
from app.core.redis import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    await init_redis()
    yield
    # Shutdown
    await close_redis()


app = FastAPI(
    title="Booking Room API",
    description="Backend service for Booking Room application",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include routers
app.include_router(upload_router)
app.include_router(admin_activity_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(banner_router)
app.include_router(activity_router)
app.include_router(seat_router)
app.include_router(study_room_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

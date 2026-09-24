from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.users import router as users_router

app = FastAPI(title="Smart Campus Management Platform API")
app.include_router(health_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

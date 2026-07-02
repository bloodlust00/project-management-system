from app.api.v1.routers import auth, comments, metrics, projects, roles, tasks, users
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(comments.router)
api_router.include_router(roles.router)
api_router.include_router(metrics.router)

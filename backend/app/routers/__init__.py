# 路由模块

from fastapi import APIRouter

from app.routers import user, music, tagging

api_router = APIRouter()

api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(music.router, prefix="/music", tags=["music"])
api_router.include_router(tagging.router, prefix="/tagging", tags=["tagging"])
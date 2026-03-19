from fastapi import APIRouter

from app.features.auth.router import router as auth_router
from app.features.books.router import router as books_router
from app.features.sessions.router import router as sessions_router
from app.features.catalog.router import router as catalog_router
from app.features.stats.router import router as stats_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(books_router)
api_router.include_router(sessions_router)
api_router.include_router(catalog_router)
api_router.include_router(stats_router)

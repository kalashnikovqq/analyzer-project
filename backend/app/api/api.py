from fastapi import APIRouter
import os

from app.api.endpoints import analysis, parsers, reviews, debug
from app.api.endpoints import auth
from app.api.endpoints import user_analysis

api_router = APIRouter()

api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(parsers.router, prefix="/parsers", tags=["parsers"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])

if os.getenv("DEBUG", "false").lower() == "true":
    api_router.include_router(debug.debug_router)

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user_analysis.router, prefix="/analyses", tags=["analyses"])

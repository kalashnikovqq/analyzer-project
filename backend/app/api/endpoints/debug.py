from fastapi import APIRouter

debug_router = APIRouter(prefix="/debug", tags=["Debug"])

@debug_router.get("/health")
async def health_check():
    return {"status": "ok", "message": "API работает"}

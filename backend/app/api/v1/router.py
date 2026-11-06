from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/status")
def api_status():
    return {
        "message": "ServeEaseFlow API v1 is operational",
        "version": "1.0.0"
    }
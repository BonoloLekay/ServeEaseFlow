from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import vehicles
from app.api.v1.endpoints import appointments
from app.api.v1.endpoints import job_cards


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(vehicles.router)
api_router.include_router(appointments.router)
api_router.include_router(job_cards.router)


@api_router.get("/status")
def api_status():
    return {
        "message": "ServeEaseFlow API v1 is operational",
        "version": "1.0.0"
    }
from fastapi import APIRouter

from routes.users_routes import router as users_router
from routes.cases_routes import router as cases_router
from routes.sightings_routes import router as sightings_router

router = APIRouter()

router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(cases_router, prefix="/cases", tags=["Cases"])
router.include_router(sightings_router, prefix="/sightings", tags=["Sightings"])
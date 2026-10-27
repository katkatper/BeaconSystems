# routes/__init__.py
from .alerts_routes import router as alerts_router
from .cases_routes import router as cases_router
from .sightings_routes import router as sightings_router
from .users_routes import router as users_router

__all__ = [
    "alerts_router",
    "cases_router",
    "sightings_router",
    "users_router",
]



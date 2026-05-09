from fastapi import FastAPI
from database.connection import Base, engine
from  contextlib import asynccontextmanager

# import models
from models.user import User
from models.sighting import Sighting
from models.case import Cases
from models.alerts import Alerts
from models.activity_log import Activity
from models.agencies import Agencies
from models.cameras import Cameras
from models.data_matches import Data_Matches
from models.data_sources import Data_Source
from models.evidence import Evidence
from models.leads import Leads
from models.person import Person
from models.timeline_events import Timeline_Event
from models.investigators import Investigators

# import routes
from routes.users_routes import router as users_router
from routes.sightings_routes import router as sightings_router
from routes.cases_routes import router as cases_router
from routes.alerts_routes import router as alerts_router



#  CREATE TABLES ON STARTUP

@asynccontextmanager

async def lifespan(app: FastAPI):
    print("Starting up...")
    # Initialization code here (e.g., database connections)
    yield
    print("Shutting down...")
    # Cleanup code here
app = FastAPI(lifespan=lifespan)


Base.metadata.create_all(bind=engine)


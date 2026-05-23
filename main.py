from fastapi import FastAPI
from database.connection import Base, engine
from  contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from routes import person_routes
from pydantic import BaseModel
from fastapi import APIRouter


# IMPORT MODELS
from models.external_record import ExternalRecord

from models.user import User

from models.sighting import Sighting

from models.case import Cases

from models.alerts import Alerts

from models.activity_log import ActivityLog

from models.agencies import Agencies

from models.cameras import Cameras

from models.data_matches import Data_Matches

from models.data_sources import Data_Source

from models.evidence import Evidence
from models.evidence_chain import EvidenceChain

from models.leads import Leads

from models.person import Person

from models.timeline_events import Timeline_Event

from models.investigators import Investigators

from models.IntegrationSource import IntegrationSource

from models.match import Match

from models.person import Person

from models.case import Cases

from models.alerts import Alerts

from models.activity_log import ActivityLog

# IMPORT ROUTES
from routes.users_routes import router as users_router

from routes.sightings_routes import router as sightings_router

from routes.cases_routes import router as cases_router

from routes.alerts_routes import router as alerts_router
from routes.evidence_routes import router as evidence_router
from routes.admin_user_routes import router as admin_user_router
from routes.dashboard_routes import router as dashboard_router

from routes.admin_log import router as admin_log_router

from routes.person_routes import router as person_router

from routes import integrations_routes

from routes import external_records_routes

from routes import match_routes

from  routes.timeline_events_routes import router as timeline_events_router

from routes.sightings_routes import router as sightings_routes

from routes.alerts_routes import router as alerts_router


router = APIRouter()

class PersonCreate(BaseModel):
    name: str
    age: int

@router.post("/api/add-person")

def add_person(person: PersonCreate):

    return {
        "message": "Person received",
        "name": person.name,
        "age": person.age
    }


#  CREATE TABLES ON STARTUP

@asynccontextmanager

async def lifespan(app: FastAPI):
    print("Starting up...")


    # INITIALIZATION OF CODE

    yield

    print("Shutting down...")


    # CLEANUP CODE
   
app = FastAPI( title="Beacon API",lifespan=lifespan)

app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
    


Base.metadata.create_all(bind=engine)

app.include_router(users_router)

app.include_router(sightings_router)

app.include_router(cases_router)

app.include_router(alerts_router)
app.include_router(evidence_router)
app.include_router(admin_user_router)
app.include_router(dashboard_router)

app.include_router(person_routes.router)

app.include_router(sightings_router)

app.include_router(person_router)

app.include_router(integrations_routes.router)

app.include_router(external_records_routes.router)

app.include_router(match_routes.router)

app.include_router(timeline_events_router)

app.include_router(alerts_router)

@app.get("/health")
def health_check():

    return {"status": "ok"}



@app.get("/")
def read_root():
    return {"message": "Beacon backend is working"}


Base.metadata.create_all(bind=engine) 

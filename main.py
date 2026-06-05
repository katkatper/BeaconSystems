# FastAPI app setup and database bootstrap.

from fastapi import FastAPI
from database.connection import Base, engine
from  contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from routes import person_routes
from pydantic import BaseModel
from fastapi import APIRouter

# Import models before create_all so SQLAlchemy knows which tables belong
# to the application metadata. Alembic migrations should be used for production.
# create_all is helpful for local development only.

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
from models.legal_access_request import LegalAccessRequest
from models.case_access_grant import CaseAccessGrant
from models.case_team_member import CaseTeamMember
from models.leads import Leads
from models.person import Person
from models.timeline_events import Timeline_Event
from models.investigators import Investigators
from models.IntegrationSource import IntegrationSource
from models.partner_intake_record import PartnerIntakeRecord
from models.match import Match
from models.person import Person
from models.case import Cases
from models.alerts import Alerts
from models.activity_log import ActivityLog
from models.bolo_alert import BoloAlert
from models.agency_exchange import AgencyExchange

# Route modules define the API endpoints used by the React frontend.
# Keep sensitive workflows, such as evidence and legal access, behind auth checks
# inside the route modules.

from routes.users_routes import router as users_router
from routes.sightings_routes import router as sightings_router
from routes.cases_routes import router as cases_router
from routes.alerts_routes import router as alerts_router
from routes.evidence_routes import router as evidence_router
from routes.admin_user_routes import router as admin_user_router
from routes.dashboard_routes import router as dashboard_router
from routes.legal_access_routes import router as legal_access_router
from routes.admin_log import router as admin_log_router
from routes.person_routes import router as person_router
from routes import integrations_routes
from routes import external_records_routes
from routes import partner_intake_routes
from routes import match_routes
from  routes.timeline_events_routes import router as timeline_events_router
from routes.sightings_routes import router as sightings_routes
from routes.alerts_routes import router as alerts_router
from routes.bolo_routes import router as bolo_router
from routes.supervisor_routes import router as supervisor_router
from routes.audit_routes import router as audit_router
from routes.agency_exchange_routes import router as agency_exchange_router


# Register API areas. Each router owns one operational workflow such as cases,
# evidence, legal authority, partner sources, BOLO alerts, or supervisor review.

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

@asynccontextmanager

async def lifespan(app: FastAPI):
    print("Starting up...")


    yield

    print("Shutting down...")
   
app = FastAPI( title="Beacon API",lifespan=lifespan)


# CORS allows the local React frontend to call the FastAPI backend during
# development. Production origins should be restricted to approved domains only.

app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
# Local development table bootstrap. In AWS/GovCloud production, use Alembic
# migrations instead so schema changes are reviewed, repeatable, and auditable.

Base.metadata.create_all(bind=engine)
app.include_router(users_router)
app.include_router(sightings_router)
app.include_router(cases_router)
app.include_router(alerts_router)
app.include_router(evidence_router)
app.include_router(admin_user_router)
app.include_router(dashboard_router)
app.include_router(legal_access_router)
app.include_router(person_routes.router)
app.include_router(sightings_router)
app.include_router(person_router)
app.include_router(integrations_routes.router)
app.include_router(external_records_routes.router)
app.include_router(partner_intake_routes.router)
app.include_router(match_routes.router)
app.include_router(timeline_events_router)
app.include_router(alerts_router)
app.include_router(bolo_router)
app.include_router(supervisor_router)
app.include_router(audit_router)
app.include_router(agency_exchange_router)

# Lightweight health endpoint used to confirm the API process is reachable.

@app.get("/health")
def health_check():

    return {"status": "ok"}



@app.get("/")
def read_root():
    return {"message": "Beacon backend is working"}


Base.metadata.create_all(bind=engine) 

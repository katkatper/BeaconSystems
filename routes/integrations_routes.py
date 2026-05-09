from re import I
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from models.IntegrationSource import IntegrationSource

router= APIRouter(

    prefix="/integrations",

    tags=["Integrations"]
) 

@router.post("/")
def create_integration_source(

    name: str,

    source_type: str,

    api_url: str | None = None,

    description: str | None= None,

    db: Session = Depends(get_db)
):

    source = IntegrationSource(

        name=name,

        source_type=source_type,

        api_url=api_url,

        description=description,

        status="pending",

        is_active=True,
        
 )

    db.add(source)
    db.commit()
    db.refresh(source)
    return (source)

    

@router.get("/")
def get_integration_sources(db: Session = Depends(get_db)):

    sources = db.query(IntegrationSource).all()

    return sources



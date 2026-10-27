from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.connection import Base
from models.agencies import Agencies
from models.integration_source import IntegrationSource
from models.integration_source_agency import IntegrationSourceAgency
from routes.integrations_routes import (
    get_integration_sources,
    replace_authorized_agencies,
    serialize_integration_source,
)
from services.pagination import PaginationParams


def test_provider_agency_authorization_is_relational_and_validated():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            Agencies.__table__,
            IntegrationSource.__table__,
            IntegrationSourceAgency.__table__,
        ],
    )

    with Session(engine) as session:
        session.add_all(
            [
                Agencies(agency_id=10, agency_name="Agency Ten"),
                Agencies(agency_id=20, agency_name="Agency Twenty"),
            ]
        )
        source = IntegrationSource(
            name="Regional Toll Feed",
            source_type="toll",
            status="approved",
            is_active=True,
        )
        session.add(source)
        replace_authorized_agencies(session, source, [20, 10, 10])
        session.commit()
        session.refresh(source)

        assert serialize_integration_source(source)["authorized_agency_ids"] == [10, 20]

        with pytest.raises(HTTPException, match="Unknown authorized agency"):
            replace_authorized_agencies(session, source, [999])

    engine.dispose()


def test_agencies_only_list_sources_explicitly_authorized_for_them():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            Agencies.__table__,
            IntegrationSource.__table__,
            IntegrationSourceAgency.__table__,
        ],
    )

    with Session(engine) as session:
        session.add_all(
            [
                Agencies(agency_id=10, agency_name="Agency Ten"),
                Agencies(agency_id=20, agency_name="Agency Twenty"),
            ]
        )
        allowed = IntegrationSource(
            name="Allowed Feed",
            source_type="toll",
            status="approved",
            is_active=True,
        )
        other = IntegrationSource(
            name="Other Agency Feed",
            source_type="camera",
            status="approved",
            is_active=True,
        )
        session.add_all([allowed, other])
        replace_authorized_agencies(session, allowed, [10])
        replace_authorized_agencies(session, other, [20])
        session.commit()

        visible = get_integration_sources(
            response=Response(),
            pagination=PaginationParams(limit=50, offset=0, cursor=None),
            db=session,
            current_user=SimpleNamespace(role="agency_admin", agency_id=10),
        )

        assert [source["name"] for source in visible] == ["Allowed Feed"]

    engine.dispose()

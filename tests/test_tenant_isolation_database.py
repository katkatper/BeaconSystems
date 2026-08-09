import unittest

from fastapi import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from models.IntegrationSource import IntegrationSource
from models.agencies import Agencies
from models.case import Cases
from models.external_record import ExternalRecord
from models.partner_intake_record import PartnerIntakeRecord
from models.person import Person
from models.user import User
from security.tenant_scope import (
    apply_partner_intake_agency_scope,
    apply_person_agency_scope,
)
from services.pagination import PaginationParams, paginate_query


class TenantIsolationDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(
            cls.engine,
            tables=[
                Agencies.__table__,
                User.__table__,
                Person.__table__,
                Cases.__table__,
                IntegrationSource.__table__,
                ExternalRecord.__table__,
                PartnerIntakeRecord.__table__,
            ],
        )
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.db = self.Session()
        self.db.add_all([
            Agencies(agency_id=101, agency_name="Agency A"),
            Agencies(agency_id=202, agency_name="Agency B"),
            User(
                user_id=1001,
                username="supervisor-a",
                email="supervisor-a@example.test",
                password_hash="test",
                role="supervisor",
                agency_id=101,
                is_active=True,
            ),
            User(
                user_id=2002,
                username="supervisor-b",
                email="supervisor-b@example.test",
                password_hash="test",
                role="supervisor",
                agency_id=202,
                is_active=True,
            ),
        ])
        self.db.flush()

        self.db.add_all([
            Person(person_id=11, first_name="Alice", last_name="AgencyA"),
            Person(person_id=22, first_name="Bob", last_name="AgencyB"),
        ])
        self.db.flush()

        self.db.add_all([
            Cases(
                case_id=111,
                case_number="A-111",
                title="Agency A Case",
                person_id=11,
                agency_id=101,
            ),
            Cases(
                case_id=222,
                case_number="B-222",
                title="Agency B Case",
                person_id=22,
                agency_id=202,
            ),
            IntegrationSource(
                id=1,
                name="Test Source",
                source_type="other",
                status="approved",
                is_active=True,
            ),
        ])
        self.db.flush()

        self.db.add_all([
            PartnerIntakeRecord(
                intake_id=1,
                agency_id=101,
                integration_source_id=1,
                record_type="tip",
                summary="Agency A intake",
            ),
            PartnerIntakeRecord(
                intake_id=2,
                agency_id=202,
                integration_source_id=1,
                record_type="tip",
                summary="Agency B intake",
            ),
        ])
        self.db.commit()
        self.supervisor_a = self.db.get(User, 1001)
        self.supervisor_b = self.db.get(User, 2002)

    def tearDown(self):
        self.db.close()
        with self.engine.begin() as connection:
            for table in reversed([
                PartnerIntakeRecord.__table__,
                Cases.__table__,
                Person.__table__,
                User.__table__,
                IntegrationSource.__table__,
                Agencies.__table__,
            ]):
                connection.execute(table.delete())

    def test_person_scope_excludes_the_other_agency(self):
        agency_a_people = apply_person_agency_scope(
            self.db.query(Person),
            self.supervisor_a,
        ).all()
        agency_b_people = apply_person_agency_scope(
            self.db.query(Person),
            self.supervisor_b,
        ).all()

        self.assertEqual([person.person_id for person in agency_a_people], [11])
        self.assertEqual([person.person_id for person in agency_b_people], [22])

    def test_partner_intake_scope_excludes_the_other_agency(self):
        agency_a_intake = apply_partner_intake_agency_scope(
            self.db.query(PartnerIntakeRecord),
            self.supervisor_a,
        ).all()
        agency_b_intake = apply_partner_intake_agency_scope(
            self.db.query(PartnerIntakeRecord),
            self.supervisor_b,
        ).all()

        self.assertEqual([item.intake_id for item in agency_a_intake], [1])
        self.assertEqual([item.intake_id for item in agency_b_intake], [2])

    def test_admin_scope_can_cross_agencies(self):
        admin = User(
            user_id=9999,
            username="national-admin",
            email="national-admin@example.test",
            password_hash="test",
            role="admin",
            is_active=True,
        )

        people = apply_person_agency_scope(self.db.query(Person), admin).all()
        intake = apply_partner_intake_agency_scope(
            self.db.query(PartnerIntakeRecord),
            admin,
        ).all()

        self.assertEqual({person.person_id for person in people}, {11, 22})
        self.assertEqual({item.intake_id for item in intake}, {1, 2})

    def test_pagination_contract_is_bounded_and_reports_more_rows(self):
        response = Response()
        page = paginate_query(
            self.db.query(PartnerIntakeRecord).order_by(
                PartnerIntakeRecord.intake_id.asc()
            ),
            PaginationParams(limit=1, offset=0),
            response,
        )

        self.assertEqual([item.intake_id for item in page], [1])
        self.assertEqual(response.headers["X-Page-Limit"], "1")
        self.assertEqual(response.headers["X-Page-Offset"], "0")
        self.assertEqual(response.headers["X-Has-More"], "true")


if __name__ == "__main__":
    unittest.main()

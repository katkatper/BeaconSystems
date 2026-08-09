import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def route_source(file_name: str) -> str:
    source = (REPOSITORY_ROOT / "routes" / file_name).read_text(encoding="utf-8-sig")
    ast.parse(source)
    return source


class AuthorizationContractTests(unittest.TestCase):
    def test_supervisor_actions_exclude_investigators_and_scope_by_case_agency(self):
        source = route_source("supervisor_routes.py")

        self.assertIn(
            'require_role("admin", "agency_admin", "supervisor")',
            source,
        )
        self.assertNotIn(
            'require_role("admin", "agency_admin", "supervisor", "investigator")',
            source,
        )
        self.assertIn("CaseAccessGrant.case_id.in_", source)
        self.assertIn('grant.status != "pending"', source)

    def test_person_records_are_scoped_through_agency_cases(self):
        source = route_source("person_routes.py")
        tenant_scope_source = (
            REPOSITORY_ROOT / "security" / "tenant_scope.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Person.cases.any(Cases.agency_id == current_user.agency_id)",
            tenant_scope_source,
        )
        self.assertIn("apply_person_agency_scope(db.query(Person)", source)
        self.assertIn("Photo not found or access denied", source)

    def test_other_supervisor_data_sources_retain_agency_filters(self):
        legal_source = route_source("legal_access_routes.py")
        user_source = route_source("admin_user_routes.py")
        bolo_source = route_source("bolo_routes.py")

        self.assertIn(
            "LegalAccessRequest.agency_id == current_user.agency_id",
            legal_source,
        )
        self.assertIn("User.agency_id == current_user.agency_id", user_source)
        self.assertIn("apply_related_case_access_filter", bolo_source)

    def test_matching_is_authenticated_bounded_and_tenant_scoped(self):
        source = route_source("match_routes.py")

        self.assertIn(
            'require_role("admin", "agency_admin", "supervisor")',
            source,
        )
        self.assertIn("apply_person_agency_scope", source)
        self.assertIn("apply_related_case_access_filter", source)
        self.assertIn("le=500", source)

    def test_partner_intake_has_explicit_tenant_ownership(self):
        source = route_source("partner_intake_routes.py")
        model_source = (
            REPOSITORY_ROOT / "models" / "partner_intake_record.py"
        ).read_text(encoding="utf-8")

        self.assertIn("apply_partner_intake_agency_scope", source)
        self.assertIn("agency_id=agency_id", source)
        self.assertIn("intake.agency_id != target_case.agency_id", source)
        self.assertIn("agency_id = Column", model_source)

    def test_integration_configuration_is_admin_only(self):
        source = route_source("integrations_routes.py")

        self.assertIn('current_user: User = Depends(require_role("admin"))', source)
        self.assertNotIn(
            'require_role("admin", "agency_admin")',
            source,
        )
        self.assertIn('IntegrationSource.status == "approved"', source)

    def test_high_volume_collections_use_the_shared_pagination_contract(self):
        pagination_source = (
            REPOSITORY_ROOT / "services" / "pagination.py"
        ).read_text(encoding="utf-8")

        self.assertIn("MAX_PAGE_SIZE = 200", pagination_source)
        self.assertIn('response.headers["X-Has-More"]', pagination_source)

        for route_name in [
            "admin_log.py",
            "alerts_routes.py",
            "bolo_routes.py",
            "cases_routes.py",
            "evidence_routes.py",
            "external_records_routes.py",
            "integrations_routes.py",
            "legal_access_routes.py",
            "partner_intake_routes.py",
            "person_routes.py",
            "sightings_routes.py",
            "timeline_events_routes.py",
            "admin_user_routes.py",
            "agency_exchange_routes.py",
            "users_routes.py",
        ]:
            self.assertIn("paginate_query", route_source(route_name), route_name)


if __name__ == "__main__":
    unittest.main()

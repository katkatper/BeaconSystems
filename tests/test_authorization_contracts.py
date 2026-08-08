import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def route_source(file_name: str) -> str:
    source = (REPOSITORY_ROOT / "routes" / file_name).read_text(encoding="utf-8")
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

        self.assertIn(
            "Person.cases.any(Cases.agency_id == current_user.agency_id)",
            source,
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


if __name__ == "__main__":
    unittest.main()

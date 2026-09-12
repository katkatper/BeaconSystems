import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def route_source(file_name: str) -> str:
    source = (REPOSITORY_ROOT / "routes" / file_name).read_text(encoding="utf-8-sig")
    ast.parse(source)
    return source


class AuthorizationContractTests(unittest.TestCase):
    def test_authenticated_sessions_establish_postgres_tenant_context(self):
        auth_source = (
            REPOSITORY_ROOT / "security" / "auth.py"
        ).read_text(encoding="utf-8-sig")
        context_source = (
            REPOSITORY_ROOT / "database" / "tenant_context.py"
        ).read_text(encoding="utf-8-sig")

        self.assertIn("configure_tenant_session(", auth_source)
        self.assertIn('@event.listens_for(Session, "after_begin")', context_source)
        self.assertIn("set_config(:key, :value, true)", context_source)

    def test_row_level_security_covers_direct_tenant_tables(self):
        migration_source = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "b28e4f7a93c2_add_tenant_row_level_security.py"
        ).read_text(encoding="utf-8-sig")

        for table_name in [
            "cases",
            "alerts",
            "bolo_alerts",
            "case_access_grants",
            "case_team_members",
            "external_records",
            "legal_access_requests",
            "matches",
            "partner_intake_records",
        ]:
            self.assertIn(f'("{table_name}",', migration_source)

        self.assertIn("ENABLE ROW LEVEL SECURITY", migration_source)
        self.assertIn("WITH CHECK", migration_source)
        self.assertIn("beacon.platform_admin", migration_source)
        self.assertIn("beacon.agency_id", migration_source)

    def test_operational_tenant_owners_are_required(self):
        model_files = {
            "alerts.py": "recipient_agency_id",
            "bolo_alert.py": "agency_id",
            "case_access_grant.py": "agency_id",
            "case_team_member.py": "agency_id",
            "external_record.py": "agency_id",
            "legal_access_request.py": "agency_id",
            "match.py": "agency_id",
            "partner_intake_record.py": "agency_id",
        }

        for file_name, column_name in model_files.items():
            source = (REPOSITORY_ROOT / "models" / file_name).read_text(
                encoding="utf-8-sig"
            )
            tree = ast.parse(source)
            assignments = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == column_name
                    for target in node.targets
                )
            ]
            self.assertEqual(len(assignments), 1, file_name)
            call = assignments[0].value
            nullable = next(
                (
                    keyword.value.value
                    for keyword in call.keywords
                    if keyword.arg == "nullable"
                    and isinstance(keyword.value, ast.Constant)
                ),
                None,
            )
            self.assertIs(nullable, False, file_name)

    def test_supervisor_actions_exclude_investigators_and_scope_by_case_agency(self):
        source = route_source("supervisor_routes.py")

        self.assertIn(
            'require_role("platform_admin", "agency_admin", "supervisor")',
            source,
        )
        self.assertNotIn(
            'require_role("platform_admin", "agency_admin", "supervisor", "investigator")',
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
        self.assertIn("apply_user_management_scope", user_source)
        user_management_source = (
            REPOSITORY_ROOT / "security" / "user_management.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "User.agency_id == current_user.agency_id",
            user_management_source,
        )
        self.assertIn("apply_related_case_access_filter", bolo_source)

    def test_matching_is_authenticated_bounded_and_tenant_scoped(self):
        source = route_source("match_routes.py")

        self.assertIn(
            'require_role("platform_admin", "agency_admin", "supervisor")',
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

        self.assertIn('current_user: User = Depends(require_role("platform_admin"))', source)
        self.assertNotIn(
            'require_role("platform_admin", "agency_admin")',
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

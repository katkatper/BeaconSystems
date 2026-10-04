import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from security.case_access_requests import (
    case_access_code_matches,
    decide_case_access,
)


class CaseAccessRequestTests(unittest.TestCase):
    def setUp(self):
        self.case = SimpleNamespace(case_status="open", agency_id=10)
        self.investigator = SimpleNamespace(role="investigator", agency_id=10)

    @patch("security.case_access_requests.CASE_ACCESS_CODE", "strong-test-code-1234")
    def test_access_code_requires_exact_configured_value(self):
        self.assertTrue(case_access_code_matches("strong-test-code-1234"))
        self.assertFalse(case_access_code_matches("STRONG-TEST-CODE-1234"))

    @patch("security.case_access_requests.CASE_ACCESS_CODE", "")
    def test_missing_access_code_disables_code_access(self):
        self.assertFalse(case_access_code_matches("BEACON-DEMO-CODE"))
        self.assertFalse(case_access_code_matches(""))

    def test_eligible_same_agency_request_receives_bounded_access(self):
        now = datetime(2026, 10, 4, 12, 0, 0)
        decision = decide_case_access(
            self.case,
            self.investigator,
            reason_category="shift_coverage",
            reason="Providing documented overnight shift coverage",
            now=now,
        )

        self.assertTrue(decision.auto_approved)
        self.assertEqual(decision.status, "active")
        self.assertEqual(decision.approval_type, "auto")
        self.assertEqual(decision.expires_at, now + timedelta(hours=24))

    def test_closed_cross_agency_or_vague_requests_require_review(self):
        scenarios = [
            (
                SimpleNamespace(case_status="closed", agency_id=10),
                self.investigator,
                "shift_coverage",
                "Providing documented overnight shift coverage",
            ),
            (
                self.case,
                SimpleNamespace(role="investigator", agency_id=20),
                "shift_coverage",
                "Providing documented overnight shift coverage",
            ),
            (
                self.case,
                self.investigator,
                "other",
                "Providing documented overnight shift coverage",
            ),
            (self.case, self.investigator, "shift_coverage", "Too vague"),
        ]

        for case, user, category, reason in scenarios:
            with self.subTest(category=category, reason=reason):
                decision = decide_case_access(
                    case,
                    user,
                    reason_category=category,
                    reason=reason,
                )
                self.assertFalse(decision.auto_approved)
                self.assertEqual(decision.status, "pending")
                self.assertIsNone(decision.expires_at)


if __name__ == "__main__":
    unittest.main()

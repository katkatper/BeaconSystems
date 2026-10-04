import unittest
from types import SimpleNamespace

from services.partner_matching import score_case_match, split_subject_name, text_tokens


class PartnerMatchingTests(unittest.TestCase):
    def setUp(self):
        self.person = SimpleNamespace(
            first_name="Taylor",
            last_name="Rivera",
            age=17,
            eye_color="brown",
            hair_color="black",
            risk_level="high",
            last_seen_location="Union Station Houston",
            description="Blue jacket",
            scars="crescent scar",
            tattoos=None,
            medical_conditions="asthma",
        )
        self.case = SimpleNamespace(
            person=self.person,
            last_seen_location="Union Station Houston",
            case_number="BC-2026-001",
            title="Missing youth",
            description="Last seen in blue jacket",
            notes="Requires asthma inhaler",
            case_status="open",
        )

    def test_strong_case_match_is_scored_and_explained(self):
        intake = SimpleNamespace(
            subject_name="Taylor Rivera",
            summary="Brown eyes, black hair, blue jacket, asthma",
            location="Union Station",
            raw_data={"age": "17"},
        )

        score, reasons = score_case_match(self.case, intake)

        self.assertEqual(score, 95)
        self.assertIn("full name matched", reasons)
        self.assertIn("age matched", reasons)
        self.assertIn("location overlapped", reasons)
        self.assertIn("description keywords overlapped", reasons)

    def test_invalid_partner_age_does_not_interrupt_scoring(self):
        intake = SimpleNamespace(
            subject_name="Unknown",
            summary="No matching details",
            location="Elsewhere",
            raw_data={"age": "not-a-number"},
        )

        score, reasons = score_case_match(self.case, intake)

        self.assertIsInstance(score, int)
        self.assertNotIn("age matched", reasons)

    def test_name_and_token_helpers_are_reusable(self):
        self.assertEqual(split_subject_name("Taylor Rivera"), ("Taylor", "Rivera"))
        self.assertEqual(split_subject_name("Cher"), ("Cher", None))
        self.assertEqual(split_subject_name("  "), (None, None))
        self.assertEqual(
            text_tokens("Near the Union-Station with Taylor"),
            {"union", "station", "taylor"},
        )


if __name__ == "__main__":
    unittest.main()

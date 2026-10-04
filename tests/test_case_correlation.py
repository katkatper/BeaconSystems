import unittest
from types import SimpleNamespace

from services.case_correlation import (
    associate_name_matches,
    build_case_correlations,
    normalize_correlation_value,
    parse_associate_names,
)


class CaseCorrelationTests(unittest.TestCase):
    def test_normalization_ignores_formatting_but_preserves_identity_text(self):
        self.assertEqual(
            normalize_correlation_value("TX Plate: ABC-1234"),
            "txplateabc1234",
        )
        self.assertEqual(normalize_correlation_value(None), "")

    def test_associate_parser_supports_json_and_legacy_records(self):
        current = '[{"name": "Jordan Lee"}, {"associate": "Alex Smith"}]'
        legacy = "Jordan Lee|friend; Alex Smith|coworker"

        expected = {"jordanlee", "alexsmith"}
        self.assertEqual(parse_associate_names(current), expected)
        self.assertEqual(parse_associate_names(legacy), expected)
        self.assertEqual(parse_associate_names(""), set())

    def test_associate_overlap_detects_shared_and_direct_relationships(self):
        target = SimpleNamespace(
            first_name="Taylor",
            last_name="Rivera",
            known_associates='[{"name": "Jordan Lee"}, {"name": "Morgan Chen"}]',
        )
        other = SimpleNamespace(
            first_name="Jordan",
            last_name="Lee",
            known_associates='[{"name": "Morgan Chen"}, {"name": "Taylor Rivera"}]',
        )

        self.assertEqual(
            associate_name_matches(target, other),
            {"jordanlee", "morganchen", "taylorrivera"},
        )

    def test_correlation_engine_returns_ranked_explainable_matches(self):
        target_case = SimpleNamespace(case_id=1, case_number="BC-001", person_id=11)
        other_case = SimpleNamespace(case_id=2, case_number="BC-002", person_id=22)
        target_person = SimpleNamespace(
            first_name="Taylor",
            last_name="Rivera",
            last_seen_location="Central Station",
            primary_address=None,
            vehicles="Blue Sedan TX ABC-1234",
            known_associates='[{"name": "Jordan Lee"}]',
            scars="crescent scar",
            tattoos=None,
            medical_conditions=None,
            age=17,
        )
        other_person = SimpleNamespace(
            first_name="Jordan",
            last_name="Lee",
            last_seen_location="Elsewhere",
            primary_address=None,
            vehicles="Blue sedan, TX ABC 1234",
            known_associates='[{"name": "Taylor Rivera"}]',
            scars=None,
            tattoos=None,
            medical_conditions=None,
            age=20,
        )
        sightings = [
            SimpleNamespace(case_id=1, location="Union Terminal"),
            SimpleNamespace(case_id=2, location="Union-Terminal"),
        ]
        hospital_record = SimpleNamespace(
            id=9,
            case_id=2,
            record_type="Hospital intake",
            age=17,
            notes="Patient has a crescent scar",
            location="County Hospital",
            geocoded_address=None,
        )

        results = build_case_correlations(
            target_case,
            [target_case, other_case],
            {11: target_person, 22: other_person},
            sightings,
            [hospital_record],
        )

        self.assertEqual(
            {item["type"] for item in results},
            {
                "shared_location",
                "shared_vehicle",
                "shared_associate",
                "hospital_demographic_match",
            },
        )
        self.assertEqual(results[0]["type"], "hospital_demographic_match")
        self.assertEqual(
            [item["confidence"] for item in results],
            sorted((item["confidence"] for item in results), reverse=True),
        )
        self.assertTrue(all(item["evidence"] for item in results))


if __name__ == "__main__":
    unittest.main()

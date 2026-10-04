import unittest

from services.sighting_confidence import calculate_sighting_confidence


class SightingConfidenceTests(unittest.TestCase):
    def test_documented_and_precisely_geocoded_sighting_scores_high(self):
        score = calculate_sighting_confidence(
            "Witness confirmed identity from a photo and saw the same clothes",
            "1200 Travis Street, Houston",
            {"accuracy": "rooftop", "score": 95},
        )

        self.assertEqual(score, 0.95)

    def test_uncertain_short_sighting_is_bounded_at_minimum(self):
        score = calculate_sighting_confidence(
            "maybe rumor unknown unclear unconfirmed similar possible",
            None,
        )

        self.assertEqual(score, 0.1)

    def test_invalid_optional_geocoder_score_does_not_fail_sighting(self):
        score = calculate_sighting_confidence(
            "Witness reported a person matching description near the station",
            "Union Station",
            {"accuracy": "street", "score": "unavailable"},
        )

        self.assertGreater(score, 0.35)
        self.assertLessEqual(score, 0.95)


if __name__ == "__main__":
    unittest.main()

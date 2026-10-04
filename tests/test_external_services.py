import json
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from integrations import police_api
from services import geocoding_service
from services.geocoding_fields import apply_geocode_result, copy_geocode_fields


class _ArcGisResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self._body


class ExternalServiceTests(unittest.TestCase):
    def test_reusable_geocode_field_mapping_can_apply_clear_and_copy(self):
        target = SimpleNamespace(latitude=1, longitude=2, geocoded_at="old")
        result = {
            "latitude": 29.75,
            "longitude": -95.36,
            "provider": "test-provider",
            "accuracy": "rooftop",
            "score": 98,
            "formatted_address": "Houston, TX",
        }
        timestamp = datetime(2026, 10, 4, 12, 0, 0)

        self.assertTrue(
            apply_geocode_result(target, result, timestamp=timestamp)
        )
        self.assertEqual(target.latitude, 29.75)
        self.assertEqual(target.geocode_provider, "test-provider")
        self.assertEqual(target.geocoded_at, timestamp)

        copy = SimpleNamespace()
        copy_geocode_fields(copy, target)
        self.assertEqual(copy.longitude, -95.36)
        self.assertEqual(copy.geocoded_address, "Houston, TX")

        self.assertFalse(
            apply_geocode_result(target, None, clear_when_missing=True)
        )
        self.assertIsNone(target.latitude)
        self.assertIsNone(target.geocoded_at)

    def test_geocode_field_mapping_can_preserve_coordinates(self):
        target = SimpleNamespace(latitude=10, longitude=20)
        result = {
            "latitude": 30,
            "longitude": 40,
            "provider": "test-provider",
            "accuracy": "place",
            "score": 80,
            "formatted_address": "Test Place",
        }

        apply_geocode_result(target, result, include_coordinates=False)

        self.assertEqual((target.latitude, target.longitude), (10, 20))
        self.assertEqual(target.geocode_accuracy, "place")

    @patch("integrations.police_api.requests.get")
    def test_police_api_uses_timeout_and_rejects_http_errors(self, get):
        response = Mock()
        response.json.return_value = {"records": [1]}
        get.return_value = response

        self.assertEqual(police_api.fetch_Beacon_systems(), {"records": [1]})
        get.assert_called_once_with(
            "https://api.police-data.gov/missing",
            timeout=police_api.EXTERNAL_API_TIMEOUT_SECONDS,
        )
        response.raise_for_status.assert_called_once_with()

    def test_geocoder_handles_coordinates_known_places_and_unknown_values(self):
        coordinates = geocoding_service.geocode_address("29.75, -95.36")
        self.assertEqual(coordinates["provider"], "manual")
        self.assertEqual(coordinates["accuracy"], "provided_coordinates")

        known = geocoding_service.geocode_address("Montrose Library")
        self.assertEqual(known["provider"], "local")
        self.assertEqual(known["accuracy"], "known_address")

        city = geocoding_service.geocode_address("Main Street, Houston")
        self.assertEqual(city["accuracy"], "city_estimate")
        self.assertEqual(city, geocoding_service.geocode_address("Main Street, Houston"))

        self.assertIsNone(geocoding_service.geocode_address(""))
        self.assertIsNone(geocoding_service.geocode_address("unknown location"))
        self.assertIsNone(geocoding_service.parse_coordinate_pair("91, 181"))

    @patch.object(geocoding_service, "ARCGIS_GEOCODING_ENABLED", True)
    @patch.object(geocoding_service, "ARCGIS_API_KEY", "test-key")
    @patch.object(geocoding_service, "ARCGIS_GEOCODE_URL", "http://unsafe.example/geocode")
    @patch("services.geocoding_service.urlopen")
    def test_arcgis_rejects_non_https_endpoint_without_requesting_it(self, urlopen):
        self.assertIsNone(geocoding_service._geocode_with_arcgis("Houston"))
        urlopen.assert_not_called()

    @patch.object(geocoding_service, "ARCGIS_GEOCODING_ENABLED", True)
    @patch.object(geocoding_service, "ARCGIS_API_KEY", "test-key")
    @patch.object(
        geocoding_service,
        "ARCGIS_GEOCODE_URL",
        "https://geocode.example/findAddressCandidates",
    )
    @patch("services.geocoding_service.urlopen")
    def test_arcgis_validates_and_returns_first_acceptable_candidate(self, urlopen):
        urlopen.return_value = _ArcGisResponse(
            {
                "candidates": [
                    {
                        "address": "1200 Travis Street, Houston, TX",
                        "score": 99,
                        "location": {"x": -95.3670, "y": 29.7543},
                        "attributes": {"Addr_type": "PointAddress"},
                    }
                ]
            }
        )

        result = geocoding_service._geocode_with_arcgis("1200 Travis Street")

        self.assertEqual(result["provider"], "arcgis")
        self.assertEqual(result["accuracy"], "rooftop")
        requested_url = urlopen.call_args.args[0]
        self.assertTrue(requested_url.startswith("https://geocode.example/"))
        self.assertIn("token=test-key", requested_url)
        self.assertEqual(
            urlopen.call_args.kwargs["timeout"],
            geocoding_service.ARCGIS_GEOCODE_TIMEOUT_SECONDS,
        )

    @patch.object(geocoding_service, "ARCGIS_GEOCODING_ENABLED", True)
    @patch.object(geocoding_service, "ARCGIS_API_KEY", "test-key")
    @patch.object(geocoding_service, "ARCGIS_GEOCODE_URL", "https://geocode.example/find")
    @patch("services.geocoding_service.urlopen", side_effect=TimeoutError)
    def test_arcgis_failure_is_safe(self, _urlopen):
        self.assertIsNone(geocoding_service._geocode_with_arcgis("Houston"))


if __name__ == "__main__":
    unittest.main()

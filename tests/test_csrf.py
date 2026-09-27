import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from security import csrf


class CookieOriginProtectionTests(unittest.TestCase):
    @staticmethod
    def request(origin: str | None):
        headers = {} if origin is None else {"origin": origin}
        return SimpleNamespace(headers=headers)

    def test_approved_origin_is_accepted(self):
        with patch.object(csrf, "IS_PRODUCTION", True), patch.object(
            csrf, "CORS_ORIGINS", ["https://beacon.example.gov"]
        ):
            csrf.validate_cookie_request_origin(
                self.request("https://beacon.example.gov")
            )

    def test_hostile_origin_is_rejected(self):
        with patch.object(csrf, "IS_PRODUCTION", True), patch.object(
            csrf, "CORS_ORIGINS", ["https://beacon.example.gov"]
        ):
            with self.assertRaises(HTTPException) as raised:
                csrf.validate_cookie_request_origin(
                    self.request("https://attacker.example")
                )

        self.assertEqual(raised.exception.status_code, 403)

    def test_local_development_origin_is_accepted(self):
        with patch.object(csrf, "IS_PRODUCTION", False), patch.object(
            csrf, "CORS_ORIGINS", []
        ):
            csrf.validate_cookie_request_origin(
                self.request("http://localhost:5173")
            )

    def test_missing_origin_fails_closed_in_production(self):
        with patch.object(csrf, "IS_PRODUCTION", True):
            with self.assertRaises(HTTPException) as raised:
                csrf.validate_cookie_request_origin(self.request(None))

        self.assertEqual(raised.exception.status_code, 403)

    def test_origin_paths_are_not_accepted(self):
        with patch.object(csrf, "IS_PRODUCTION", True), patch.object(
            csrf, "CORS_ORIGINS", ["https://beacon.example.gov"]
        ):
            with self.assertRaises(HTTPException):
                csrf.validate_cookie_request_origin(
                    self.request("https://beacon.example.gov/unsafe")
                )


if __name__ == "__main__":
    unittest.main()

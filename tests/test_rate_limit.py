import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from security import rate_limit


class AuthenticationRateLimitTests(unittest.TestCase):
    def setUp(self):
        rate_limit._local_counts.clear()
        self.request = SimpleNamespace(client=SimpleNamespace(host="192.0.2.10"))

    def test_local_limiter_rejects_requests_over_the_limit(self):
        with patch.object(rate_limit, "_redis_client", None), patch.object(
            rate_limit.time, "time", return_value=120
        ):
            rate_limit.enforce_rate_limit(
                self.request,
                namespace="login",
                identifier="192.0.2.10:investigator",
                limit=2,
                window_seconds=60,
            )
            rate_limit.enforce_rate_limit(
                self.request,
                namespace="login",
                identifier="192.0.2.10:investigator",
                limit=2,
                window_seconds=60,
            )

            with self.assertRaises(HTTPException) as raised:
                rate_limit.enforce_rate_limit(
                    self.request,
                    namespace="login",
                    identifier="192.0.2.10:investigator",
                    limit=2,
                    window_seconds=60,
                )

        self.assertEqual(raised.exception.status_code, 429)
        self.assertEqual(raised.exception.headers["Retry-After"], "60")

    def test_identifiers_are_hashed_before_storage(self):
        key, _ = rate_limit._rate_limit_key("login", "sensitive-user", 60, 120)

        self.assertNotIn("sensitive-user", key)
        self.assertTrue(key.startswith("beacon:rate-limit:login:"))


if __name__ == "__main__":
    unittest.main()

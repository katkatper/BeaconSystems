import unittest

from security.mfa import (
    build_otpauth_uri,
    generate_mfa_secret,
    generate_totp,
    verify_totp,
)


class MfaTests(unittest.TestCase):
    RFC_TEST_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"

    def test_totp_matches_standard_test_vector_at_six_digits(self):
        self.assertEqual(generate_totp(self.RFC_TEST_SECRET, 59), "287082")

    def test_totp_verification_accepts_adjacent_window_only(self):
        previous_window_code = generate_totp(self.RFC_TEST_SECRET, 30)

        self.assertTrue(
            verify_totp(self.RFC_TEST_SECRET, previous_window_code, at_time=60)
        )
        self.assertFalse(
            verify_totp(self.RFC_TEST_SECRET, previous_window_code, at_time=120)
        )
        self.assertFalse(verify_totp(None, previous_window_code, at_time=60))
        self.assertFalse(verify_totp(self.RFC_TEST_SECRET, "12345", at_time=60))

    def test_enrollment_values_are_well_formed(self):
        secret = generate_mfa_secret()
        self.assertEqual(len(secret), 32)

        uri = build_otpauth_uri("agent@example.com", secret)
        self.assertTrue(uri.startswith("otpauth://totp/Beacon%3Aagent%40example.com"))
        self.assertIn(f"secret={secret}", uri)
        self.assertIn("digits=6", uri)
        self.assertIn("period=30", uri)


if __name__ == "__main__":
    unittest.main()

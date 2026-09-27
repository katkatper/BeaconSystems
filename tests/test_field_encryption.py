import unittest

from security.field_encryption import (
    ENCRYPTED_PREFIX,
    decrypt_mfa_secret,
    encrypt_mfa_secret,
)


class MfaSecretEncryptionTests(unittest.TestCase):
    def test_mfa_secret_round_trip_uses_authenticated_encryption(self):
        secret = "JBSWY3DPEHPK3PXP"
        encrypted = encrypt_mfa_secret(secret)
        decrypted, was_plaintext = decrypt_mfa_secret(encrypted)

        self.assertTrue(encrypted.startswith(ENCRYPTED_PREFIX))
        self.assertNotIn(secret, encrypted)
        self.assertEqual(decrypted, secret)
        self.assertFalse(was_plaintext)

    def test_legacy_plaintext_can_be_detected_for_migration(self):
        decrypted, was_plaintext = decrypt_mfa_secret("JBSWY3DPEHPK3PXP")

        self.assertEqual(decrypted, "JBSWY3DPEHPK3PXP")
        self.assertTrue(was_plaintext)


if __name__ == "__main__":
    unittest.main()

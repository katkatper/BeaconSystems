import unittest
from datetime import datetime, timedelta

from security.sessions import (
    create_auth_session,
    refresh_token_hash,
    revoke_auth_session,
    rotate_refresh_token,
    serialize_auth_session,
)


class SessionTests(unittest.TestCase):
    def test_session_stores_only_hashed_refresh_token_and_bounds_metadata(self):
        issued_at = datetime(2026, 10, 4, 12, 0, 0)
        session, refresh_token = create_auth_session(
            42,
            ip_address="192.0.2.10",
            user_agent="a" * 600,
            now=issued_at,
        )

        self.assertEqual(session.user_id, 42)
        self.assertNotEqual(session.refresh_token_hash, refresh_token)
        self.assertEqual(session.refresh_token_hash, refresh_token_hash(refresh_token))
        self.assertEqual(len(session.refresh_token_hash), 64)
        self.assertEqual(len(session.user_agent), 512)
        self.assertGreater(session.expires_at, issued_at)
        self.assertGreater(session.refresh_expires_at, session.expires_at)

    def test_refresh_rotation_invalidates_old_token_and_updates_activity(self):
        issued_at = datetime(2026, 10, 4, 12, 0, 0)
        session, old_token = create_auth_session(
            42,
            ip_address=None,
            user_agent=None,
            now=issued_at,
        )
        rotated_at = issued_at + timedelta(minutes=5)

        new_token = rotate_refresh_token(session, now=rotated_at)

        self.assertNotEqual(new_token, old_token)
        self.assertNotEqual(session.refresh_token_hash, refresh_token_hash(old_token))
        self.assertEqual(session.refresh_token_hash, refresh_token_hash(new_token))
        self.assertEqual(session.last_seen_at, rotated_at)

    def test_revocation_and_serialization_are_consistent(self):
        issued_at = datetime(2026, 10, 4, 12, 0, 0)
        session, _ = create_auth_session(
            42,
            ip_address=None,
            user_agent=None,
            now=issued_at,
        )
        revoke_auth_session(session, now=issued_at)
        serialized = serialize_auth_session(session, session.session_id)

        self.assertEqual(session.revoked_at, issued_at)
        self.assertTrue(serialized["is_current"])
        self.assertEqual(serialized["session_id"], session.session_id)


if __name__ == "__main__":
    unittest.main()

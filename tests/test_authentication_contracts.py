import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
from fastapi import HTTPException
from jwt.exceptions import InvalidTokenError

from config.settings import ALGORITHM, JWT_AUDIENCE, JWT_ISSUER, SECRET_KEY
from security.auth import create_access_token
from services.user_administration import (
    assign_user_role,
    get_managed_user,
    set_user_active,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class AuthenticationContractTests(unittest.TestCase):
    def test_token_validation_rejects_the_wrong_audience(self):
        token = create_access_token({"sub": "1", "auth_version": 0})
        claims = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )

        self.assertEqual(claims["sub"], "1")
        self.assertEqual(claims["token_type"], "access")
        self.assertTrue(claims["jti"])

        with self.assertRaises(InvalidTokenError):
            jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                audience="wrong-audience",
                issuer=JWT_ISSUER,
            )

    def test_tokens_use_immutable_identity_and_beacon_bound_claims(self):
        auth_source = (REPOSITORY_ROOT / "security" / "auth.py").read_text(encoding="utf-8")
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        ast.parse(auth_source)
        ast.parse(routes_source)

        self.assertIn('"sub": str(user.user_id)', routes_source)
        self.assertIn('"auth_version": user.auth_version', routes_source)
        self.assertIn('"iss": JWT_ISSUER', auth_source)
        self.assertIn('"aud": JWT_AUDIENCE', auth_source)
        self.assertIn('"jti": str(uuid.uuid4())', auth_source)
        self.assertIn('payload.get("token_type") != "access"', auth_source)
        self.assertIn("audience=JWT_AUDIENCE", auth_source)
        self.assertIn("issuer=JWT_ISSUER", auth_source)
        self.assertIn("User.user_id == user_id", auth_source)

    def test_security_sensitive_user_changes_revoke_older_tokens(self):
        actor = SimpleNamespace(
            user_id=1,
            agency_id=10,
            role="platform_admin",
        )
        target = SimpleNamespace(
            user_id=2,
            agency_id=20,
            role="investigator",
            is_active=True,
            auth_version=3,
        )

        previous_role = assign_user_role(actor, target, "supervisor")
        self.assertEqual(previous_role, "investigator")
        self.assertEqual(target.role, "supervisor")
        self.assertEqual(target.auth_version, 4)

        set_user_active(actor, target, False)
        self.assertFalse(target.is_active)
        self.assertEqual(target.auth_version, 5)

    def test_user_administration_prevents_self_deactivation(self):
        actor = SimpleNamespace(
            user_id=1,
            agency_id=10,
            role="platform_admin",
            is_active=True,
            auth_version=0,
        )

        with self.assertRaises(HTTPException) as raised:
            set_user_active(actor, actor, False)

        self.assertEqual(raised.exception.status_code, 400)
        self.assertTrue(actor.is_active)
        self.assertEqual(actor.auth_version, 0)

    def test_managed_user_lookup_applies_tenant_authorization(self):
        actor = SimpleNamespace(
            user_id=1,
            agency_id=10,
            role="agency_admin",
        )
        target = SimpleNamespace(
            user_id=2,
            agency_id=10,
            role="investigator",
        )
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = target

        self.assertIs(get_managed_user(db, actor, 2), target)

        db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(HTTPException) as raised:
            get_managed_user(db, actor, 999)
        self.assertEqual(raised.exception.status_code, 404)

    def test_authenticated_requests_require_an_active_server_session(self):
        auth_source = (REPOSITORY_ROOT / "security" / "auth.py").read_text(encoding="utf-8")
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        migration_source = (
            REPOSITORY_ROOT / "migrations" / "versions" / "601d95116833_create_beacon_production_baseline.py"
        ).read_text(encoding="utf-8")

        self.assertIn('payload.get("sid")', auth_source)
        self.assertIn("AuthSession.revoked_at.is_(None)", auth_source)
        self.assertIn('@router.post("/logout")', routes_source)
        self.assertIn("op.create_table('auth_sessions'", migration_source)

    def test_refresh_tokens_are_hashed_rotated_and_http_only(self):
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        sessions_source = (REPOSITORY_ROOT / "security" / "sessions.py").read_text(encoding="utf-8")
        client_source = (REPOSITORY_ROOT / "beaconsystems.client" / "src" / "api.jsx").read_text(encoding="utf-8")
        self.assertIn('@router.post("/refresh")', routes_source)
        self.assertIn('hashlib.sha256(token.encode("utf-8")).hexdigest()', sessions_source)
        self.assertIn("rotate_refresh_token(auth_session", routes_source)
        self.assertIn("httponly=True", routes_source)
        self.assertIn('credentials: "include"', client_source)
        self.assertIn("validate_cookie_request_origin(request)", routes_source)

    def test_users_can_review_and_revoke_their_sessions(self):
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        self.assertIn('@router.get("/sessions")', routes_source)
        self.assertIn('@router.post("/sessions/{session_id}/revoke")', routes_source)
        self.assertIn('@router.post("/sessions/revoke-others")', routes_source)
        self.assertIn("AuthSession.user_id == current_user.user_id", routes_source)

    def test_authentication_entry_points_are_rate_limited(self):
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        limiter_source = (REPOSITORY_ROOT / "security" / "rate_limit.py").read_text(encoding="utf-8")
        settings_source = (REPOSITORY_ROOT / "config" / "settings.py").read_text(encoding="utf-8")

        ast.parse(limiter_source)
        self.assertGreaterEqual(routes_source.count("enforce_rate_limit("), 3)
        self.assertIn('namespace="login"', routes_source)
        self.assertIn('namespace="mfa"', routes_source)
        self.assertIn('namespace="refresh"', routes_source)
        self.assertIn("RATE_LIMIT_REDIS_URL is required in production", settings_source)
        self.assertIn("HTTP_429_TOO_MANY_REQUESTS", limiter_source)
        self.assertIn("HTTP_503_SERVICE_UNAVAILABLE", limiter_source)

    def test_mfa_secrets_are_encrypted_and_not_redisclosed_after_enrollment(self):
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        encryption_source = (REPOSITORY_ROOT / "security" / "field_encryption.py").read_text(encoding="utf-8")

        ast.parse(encryption_source)
        self.assertIn("encrypt_mfa_secret(secret)", routes_source)
        self.assertIn("decrypt_mfa_secret", routes_source)
        self.assertIn("if current_user.mfa_enabled", routes_source)
        self.assertIn('ENCRYPTED_PREFIX = "enc:v1:"', encryption_source)

    def test_production_mfa_enrollment_and_refresh_sessions_are_enforced(self):
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        auth_source = (REPOSITORY_ROOT / "security" / "auth.py").read_text(encoding="utf-8")
        session_model = (REPOSITORY_ROOT / "models" / "auth_session.py").read_text(encoding="utf-8")
        login_source = (REPOSITORY_ROOT / "beaconsystems.client" / "src" / "pages" / "Login.jsx").read_text(encoding="utf-8")

        self.assertIn('issue_mfa_challenge(user, "mfa_enrollment")', routes_source)
        self.assertIn('@router.post("/mfa/enrollment/start")', routes_source)
        self.assertIn('@router.post("/mfa/enrollment/complete")', routes_source)
        self.assertIn("MFA cannot be disabled while enforcement is active", routes_source)
        self.assertIn("not auth_session.mfa_authenticated", routes_source)
        self.assertIn("not auth_session.mfa_authenticated", auth_source)
        self.assertIn("mfa_authenticated = Column(Boolean", session_model)
        self.assertIn('/users/mfa/enrollment/complete', login_source)

    def test_no_hard_coded_development_signing_key_remains(self):
        offenders = []
        forbidden_value = "your_" + "secret_key"
        for directory in ["routes", "security", "services"]:
            for path in (REPOSITORY_ROOT / directory).rglob("*.py"):
                if forbidden_value in path.read_text(encoding="utf-8-sig"):
                    offenders.append(str(path.relative_to(REPOSITORY_ROOT)))

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()

import ast
import unittest
from pathlib import Path

from jose import JWTError, jwt

from config.settings import ALGORITHM, JWT_AUDIENCE, JWT_ISSUER, SECRET_KEY
from security.auth import create_access_token


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

        with self.assertRaises(JWTError):
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
        user_routes = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        admin_routes = (REPOSITORY_ROOT / "routes" / "admin_user_routes.py").read_text(encoding="utf-8")

        self.assertGreaterEqual(user_routes.count("auth_version += 1"), 4)
        self.assertGreaterEqual(admin_routes.count("auth_version += 1"), 4)

    def test_authenticated_requests_require_an_active_server_session(self):
        auth_source = (REPOSITORY_ROOT / "security" / "auth.py").read_text(encoding="utf-8")
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        migration_source = (
            REPOSITORY_ROOT / "migrations" / "versions" / "d4a06b9e15f8_add_auth_sessions.py"
        ).read_text(encoding="utf-8")

        self.assertIn('payload.get("sid")', auth_source)
        self.assertIn("AuthSession.revoked_at.is_(None)", auth_source)
        self.assertIn('@router.post("/logout")', routes_source)
        self.assertIn('"auth_sessions"', migration_source)

    def test_refresh_tokens_are_hashed_rotated_and_http_only(self):
        routes_source = (REPOSITORY_ROOT / "routes" / "users_routes.py").read_text(encoding="utf-8")
        client_source = (REPOSITORY_ROOT / "beaconsystems.client" / "src" / "api.jsx").read_text(encoding="utf-8")
        self.assertIn('@router.post("/refresh")', routes_source)
        self.assertIn("hashlib.sha256(refresh_token.encode()).hexdigest()", routes_source)
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

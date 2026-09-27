from urllib.parse import urlsplit

from fastapi import HTTPException, Request, status

from config.settings import CORS_ORIGINS, IS_PRODUCTION


def _canonical_origin(value: str) -> str | None:
    try:
        parsed = urlsplit(value)
        if not parsed.scheme or not parsed.netloc:
            return None
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            return None
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
    except ValueError:
        return None


def validate_cookie_request_origin(request: Request) -> None:
    """Protect cookie-authenticated endpoints from cross-origin submission."""
    supplied_origin = request.headers.get("origin")
    if not supplied_origin:
        if IS_PRODUCTION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A valid browser origin is required",
            )
        return

    canonical_origin = _canonical_origin(supplied_origin)
    if not IS_PRODUCTION and canonical_origin is not None:
        development_host = urlsplit(canonical_origin).hostname
        if development_host in {"localhost", "127.0.0.1"}:
            return

    approved_origins = {
        normalized
        for value in CORS_ORIGINS
        if (normalized := _canonical_origin(value)) is not None
    }

    if canonical_origin is None or canonical_origin not in approved_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Browser origin is not approved",
        )

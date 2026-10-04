from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return UTC without timezone metadata for Beacon's existing DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_aware() -> datetime:
    """Return timezone-aware UTC for tokens and external protocols."""
    return datetime.now(timezone.utc)

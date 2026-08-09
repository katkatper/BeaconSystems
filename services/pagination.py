import base64
from dataclasses import dataclass

from fastapi import HTTPException, Query, Response


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


@dataclass(frozen=True)
class PaginationParams:
    limit: int
    offset: int
    cursor: str | None

    def __init__(
        self,
        limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
        offset: int = Query(0, ge=0),
        cursor: str | None = Query(None),
    ):
        object.__setattr__(self, "limit", limit)
        object.__setattr__(self, "offset", offset)
        object.__setattr__(self, "cursor", cursor if isinstance(cursor, str) else None)


def _encode_cursor(value: int) -> str:
    return base64.urlsafe_b64encode(str(value).encode()).decode().rstrip("=")


def _decode_cursor(value: str) -> int:
    try:
        padded = value + "=" * (-len(value) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode()).decode()
        cursor_id = int(decoded)
        if cursor_id < 1:
            raise ValueError
        return cursor_id
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid pagination cursor") from exc


def paginate_query(query, pagination: PaginationParams, response: Response, cursor_column=None):
    """Return a bounded legacy array and publish a consistent page contract."""
    if pagination.cursor:
        if cursor_column is None:
            raise HTTPException(status_code=400, detail="Cursor pagination is not supported for this collection")
        query = query.filter(cursor_column < _decode_cursor(pagination.cursor))

    return paginate_query_values(
        query,
        limit=pagination.limit,
        offset=0 if pagination.cursor else pagination.offset,
        response=response,
        cursor_column=cursor_column,
    )


def paginate_query_values(query, *, limit: int, offset: int, response: Response, cursor_column=None):
    """Apply the page contract to endpoints retaining legacy query defaults."""
    rows = (
        query.offset(offset)
        .limit(limit + 1)
        .all()
    )
    has_more = len(rows) > limit

    response.headers["X-Page-Limit"] = str(limit)
    response.headers["X-Page-Offset"] = str(offset)
    response.headers["X-Has-More"] = "true" if has_more else "false"
    if has_more and cursor_column is not None and rows[:limit]:
        response.headers["X-Next-Cursor"] = _encode_cursor(
            getattr(rows[limit - 1], cursor_column.key)
        )
    response.headers["Access-Control-Expose-Headers"] = (
        "X-Page-Limit, X-Page-Offset, X-Has-More, X-Next-Cursor"
    )

    return rows[:limit]

from dataclasses import dataclass

from fastapi import Query, Response


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


@dataclass(frozen=True)
class PaginationParams:
    limit: int
    offset: int

    def __init__(
        self,
        limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
        offset: int = Query(0, ge=0),
    ):
        object.__setattr__(self, "limit", limit)
        object.__setattr__(self, "offset", offset)


def paginate_query(query, pagination: PaginationParams, response: Response):
    """Return a bounded legacy array and publish a consistent page contract."""
    return paginate_query_values(
        query,
        limit=pagination.limit,
        offset=pagination.offset,
        response=response,
    )


def paginate_query_values(query, *, limit: int, offset: int, response: Response):
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
    response.headers["Access-Control-Expose-Headers"] = (
        "X-Page-Limit, X-Page-Offset, X-Has-More"
    )

    return rows[:limit]

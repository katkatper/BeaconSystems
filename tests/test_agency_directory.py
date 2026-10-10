from types import SimpleNamespace
from unittest.mock import Mock

from security.tenant_scope import apply_agency_directory_scope


def test_platform_admin_can_query_the_full_agency_directory():
    query = Mock()
    user = SimpleNamespace(role="platform_admin", agency_id=1)

    assert apply_agency_directory_scope(query, user) is query
    query.filter.assert_not_called()


def test_non_platform_user_is_restricted_to_their_agency():
    query = Mock()
    query.filter.return_value = query
    user = SimpleNamespace(role="agency_admin", agency_id=42)

    assert apply_agency_directory_scope(query, user) is query
    expression = query.filter.call_args.args[0]
    assert expression.right.value == 42

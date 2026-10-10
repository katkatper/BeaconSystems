from types import SimpleNamespace
from unittest.mock import Mock

from models.case import Cases
from security.case_access import accessible_case_id_query


def test_platform_admin_case_id_query_remains_unrestricted():
    db = Mock()
    query = Mock()
    db.query.return_value = query
    user = SimpleNamespace(role="platform_admin")

    assert accessible_case_id_query(db, user) is query
    db.query.assert_called_once_with(Cases.case_id)
    query.filter.assert_not_called()


def test_agency_case_id_query_applies_agency_boundary():
    db = Mock()
    query = Mock()
    query.filter.return_value = query
    db.query.return_value = query
    user = SimpleNamespace(role="agency_admin", agency_id=42)

    assert accessible_case_id_query(db, user) is query
    expression = query.filter.call_args.args[0]
    assert expression.right.value == 42

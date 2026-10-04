from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user import User
from security.user_management import (
    assert_role_assignment_access,
    assert_user_management_access,
)


def get_managed_user(db: Session, actor: User, user_id: int) -> User:
    """Load a user and enforce the actor's tenant-management boundary."""
    target = db.query(User).filter(User.user_id == user_id).first()
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    assert_user_management_access(actor, target)
    return target


def assign_user_role(actor: User, target: User, role: str) -> str:
    """Authorize and apply a role change, invalidating existing sessions."""
    assert_user_management_access(actor, target)
    assert_role_assignment_access(actor, role)

    previous_role = target.role
    target.role = role
    target.auth_version += 1
    return previous_role


def set_user_active(actor: User, target: User, is_active: bool) -> None:
    """Authorize and apply account status, invalidating existing sessions."""
    assert_user_management_access(actor, target)
    if actor.user_id == target.user_id and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate yourself",
        )

    target.is_active = is_active
    target.auth_version += 1

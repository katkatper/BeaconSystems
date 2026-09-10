from fastapi import HTTPException, status

from models.user import User


USER_MANAGER_ROLES = ("platform_admin", "agency_admin")
ASSIGNABLE_ROLES = {
    "platform_admin",
    "agency_admin",
    "supervisor",
    "investigator",
    "analyst",
    "viewer",
}


def apply_user_management_scope(query, current_user: User):
    if current_user.role == "platform_admin":
        return query

    if current_user.role == "agency_admin":
        return query.filter(User.agency_id == current_user.agency_id)

    return query.filter(User.user_id == -1)


def assert_user_management_access(current_user: User, target_user: User) -> None:
    if current_user.role == "platform_admin":
        return

    if current_user.role != "agency_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage users",
        )

    if target_user.agency_id != current_user.agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot manage users from another agency",
        )

    if target_user.role == "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agency administrators cannot manage platform administrators",
        )


def assert_role_assignment_access(current_user: User, role: str) -> None:
    if role not in ASSIGNABLE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )

    if current_user.role == "agency_admin" and role == "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agency administrators cannot assign platform administrator access",
        )

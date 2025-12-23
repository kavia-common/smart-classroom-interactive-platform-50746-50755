from rest_framework.permissions import BasePermission


def _get_role(user) -> str | None:
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None)


class IsAdmin(BasePermission):
    """
    Allows access to Admin users (superuser/staff or role=ADMIN).
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(user.is_superuser or user.is_staff or _get_role(user) == "ADMIN")


class IsTeacher(BasePermission):
    """
    Allows access to Teacher users (and Admin users).
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff or _get_role(user) == "ADMIN":
            return True
        return _get_role(user) == "TEACHER"


class IsStudent(BasePermission):
    """
    Allows access to Student users (and Admin users).
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff or _get_role(user) == "ADMIN":
            return True
        return _get_role(user) == "STUDENT"

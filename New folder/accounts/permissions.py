from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_in_group(user, group_name: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and user_in_group(request.user, "admin"))


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and user_in_group(request.user, "admin"))


class IsAdminOrAssigned(BasePermission):
    """Allows updates if user is admin or assigned to the object (expects `assigned_user_attr` on view)."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if user_in_group(request.user, "admin"):
            return True
        assigned_attr = getattr(view, "assigned_user_attr", None)
        if assigned_attr and hasattr(obj, assigned_attr):
            return getattr(obj, assigned_attr) == request.user
        return False


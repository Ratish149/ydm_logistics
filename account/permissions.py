from rest_framework.permissions import BasePermission


class HasValidAPIKey(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_active
        )


class IsYDM(BasePermission):
    """Allow access only to users with the YDM role."""

    message = "Only YDM users are allowed to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) == request.user.ROLE_YDM
        )

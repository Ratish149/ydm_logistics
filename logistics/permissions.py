from rest_framework.permissions import BasePermission


class IsOrderOwnerOrYdmForUpdate(BasePermission):
    """
    Object-level permission for OrderDetailAPI:
    - GET (retrieve): any authenticated user.
    - PUT / PATCH (update): only the order owner or a ydm user.
    - DELETE: only the order owner.
    """

    message = "You do not have permission to perform this action on this order."

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        user = request.user
        is_owner = obj.user_id == user.pk

        if request.method in ("PUT", "PATCH"):
            return is_owner or getattr(user, "role", None) == "ydm"

        if request.method == "DELETE":
            return is_owner

        return False

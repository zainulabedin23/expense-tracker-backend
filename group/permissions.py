from rest_framework import permissions

class IsGroupOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only group owners to edit/delete their groups.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True  # Read permissions allowed for any request
        return obj.created_by == request.user  # Only owner can modify

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Only the creator (owner) of an object can access it."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

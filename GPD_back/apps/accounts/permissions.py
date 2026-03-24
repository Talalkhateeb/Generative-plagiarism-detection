"""Custom permissions matching the UML role-based access."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    """Allow access only to users with role='admin'."""
    message = 'Admin role required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')


class IsUserRole(BasePermission):
    """Allow access only to regular users (role='user')."""
    message = 'User role required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'user')


class IsOwnerOrAdmin(BasePermission):
    """Object-level: owner or admin can access."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        owner = getattr(obj, 'user', getattr(obj, 'owner', None))
        return owner == request.user


class IsActiveUser(BasePermission):
    """Reject inactive (blocked) users."""
    message = 'Your account has been deactivated.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.status == 'active')

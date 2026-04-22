"""
UC-9: Admin — Accounts Management
Admin can ONLY change status (active/inactive) as per requirements.
"""
from rest_framework import generics, filters
from .models import User
from .serializers import AdminAccountSerializer
from .permissions import IsAdminRole


class AdminAccountListView(generics.ListAPIView):
    """GET /api/admin/accounts/ — list all users with their info."""
    serializer_class   = AdminAccountSerializer
    permission_classes = [IsAdminRole]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['name', 'email', 'role', 'status']
    ordering_fields    = ['created_at', 'name', 'email']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs = User.objects.select_related('plan').all()
        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class AdminAccountDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/admin/accounts/{id}/ — user detail
    PATCH /api/admin/accounts/{id}/ — change status ONLY
    """
    serializer_class   = AdminAccountSerializer
    permission_classes = [IsAdminRole]
    queryset           = Account.objects.select_related('plan').all()
    http_method_names  = ['get', 'patch', 'head', 'options']

    def perform_update(self, serializer):
        # Only allow status field to be changed (enforced by serializer read_only_fields)
        serializer.save()

"""
UC-8: Plans Management
- GET  /api/plans/       → anyone can list plans (for registration plan selection)
- POST /api/plans/       → admin only
- PATCH/DELETE           → admin only
"""
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Plan
from .serializers import PlanSerializer, PlanCreateUpdateSerializer
from apps.accounts.permissions import IsAdminRole


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return PlanCreateUpdateSerializer
        return PlanSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [AllowAny()]          # Public: for registration page
        return [IsAdminRole()]           # Write: admin only (UC-8)

    def get_queryset(self):
        # Admins see all plans including inactive
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return Plan.objects.all()
        return Plan.objects.filter(is_active=True)

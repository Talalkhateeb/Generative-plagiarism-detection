"""Admin-only endpoints for accounts management (UC-9)."""
from django.urls import path
from .admin_views import AdminAccountListView, AdminAccountDetailView

urlpatterns = [
    path('accounts/',      AdminAccountListView.as_view(),   name='admin-accounts'),
    path('accounts/<int:pk>/', AdminAccountDetailView.as_view(), name='admin-account-detail'),
]

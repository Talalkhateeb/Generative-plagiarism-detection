"""
GPD.AI — Main URL Configuration

URL Structure:
  POST   /api/auth/register/            → Register new user (with plan)
  POST   /api/auth/login/               → Obtain JWT tokens
  POST   /api/auth/token/refresh/       → Refresh access token
  POST   /api/auth/logout/              → Blacklist refresh token
  POST   /api/auth/change-password/     → Change password
  GET    /api/auth/me/                  → Current user profile
  PATCH  /api/auth/me/                  → Update profile

  GET    /api/plans/                    → List plans (public)
  POST   /api/plans/                    → Create plan (admin only)
  GET    /api/plans/{id}/               → Plan detail
  PUT    /api/plans/{id}/               → Update plan (admin only)
  DELETE /api/plans/{id}/               → Delete plan (admin only)

  GET    /api/workspaces/               → List user's workspaces
  POST   /api/workspaces/               → Create workspace
  GET    /api/workspaces/{id}/          → Workspace detail
  PATCH  /api/workspaces/{id}/          → Rename workspace
  DELETE /api/workspaces/{id}/          → Delete workspace
  POST   /api/workspaces/{id}/sources/  → Upload source files
  DELETE /api/workspaces/{id}/sources/{src_id}/ → Remove source
  POST   /api/workspaces/{id}/documents/ → Upload documents
  DELETE /api/workspaces/{id}/documents/{doc_id}/ → Remove document
  POST   /api/workspaces/{id}/submit/   → Submit for analysis (UC-4)
  GET    /api/workspaces/{id}/results/  → Get analysis results
  GET    /api/workspaces/{id}/report/   → Download PDF report

  GET    /api/submissions/history/      → User submission history (UC-10)

  GET    /api/admin/accounts/           → List all users (admin only)
  GET    /api/admin/accounts/{id}/      → User detail (admin only)
  PATCH  /api/admin/accounts/{id}/      → Update user status (admin only)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/',        include('apps.accounts.urls')),
    path('api/plans/',       include('apps.plans.urls')),
    path('api/workspaces/',  include('apps.workspaces.urls')),
    path('api/submissions/', include('apps.submissions.urls')),
    path('api/admin/',       include('apps.accounts.admin_urls')),
    path('api/results/', include('apps.results.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

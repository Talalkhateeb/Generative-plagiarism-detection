from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet

# auto-generate URL patterns for the PlanViewSet
router = DefaultRouter()
router.register('', PlanViewSet, basename='plan')
urlpatterns = [path('', include(router.urls))]

from django.urls import path
<<<<<<< HEAD
from .views import SubmissionHistoryView

urlpatterns = [
    path('history/', SubmissionHistoryView.as_view(), name='submission-history'),
=======
from .views import SubmissionDetailView, SubmissionHistoryView

urlpatterns = [
    path('history/', SubmissionHistoryView.as_view(), name='submission-history'),
    path('<int:pk>/', SubmissionDetailView.as_view(), name='submission-detail'),
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
]

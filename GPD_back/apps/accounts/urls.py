from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, SendOTPView, VerifyOTPView, ResendOTPView,
    LogoutView, MeView, ChangePasswordView,
)

urlpatterns = [
    # UC-1: Login
    path('login/',                   LoginView.as_view(),       name='auth-login'),

    # UC-2: Register — 2-step OTP flow
    path('register/send-otp/',       SendOTPView.as_view(),     name='auth-send-otp'),
    path('register/verify-otp/',     VerifyOTPView.as_view(),   name='auth-verify-otp'),
    path('register/resend-otp/',     ResendOTPView.as_view(),   name='auth-resend-otp'),

    # Session
    path('logout/',                  LogoutView.as_view(),      name='auth-logout'),
    path('token/refresh/',           TokenRefreshView.as_view(), name='token-refresh'),

    # Profile
    path('me/',                      MeView.as_view(),          name='auth-me'),
    path('change-password/',         ChangePasswordView.as_view(), name='change-password'),
]

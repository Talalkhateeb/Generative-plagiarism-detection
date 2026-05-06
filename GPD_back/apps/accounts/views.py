"""
Accounts — Views
UC-1: Log In
UC-2: Sign Up with OTP email verification (2-step flow)
UC-9: Admin account management
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import serializers as drf_serializers

from .models import User as Account, Admin, OTPVerification
from .serializers import (
    SendOTPSerializer, VerifyOTPAndRegisterSerializer,
    UserProfileSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, AdminAccountSerializer,
)
from .permissions import IsAdminRole, IsActiveUser
from .serializers import (
    SendOTPSerializer, VerifyOTPAndRegisterSerializer,
    ResendOTPSerializer,   # ← add this
    UserProfileSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, AdminAccountSerializer,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_token_response(account, http_status=status.HTTP_200_OK):
    """Build the standard JWT response dict returned after login/register."""
    refresh = RefreshToken.for_user(account)
    refresh['name']  = account.name
    refresh['role']  = account.role
    refresh['email'] = account.email
    return Response({
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id':         account.id,
            'name':       account.name,
            'email':      account.email,
            'role':       account.role,
            'status':     account.status,
            'plan':       account.plan.name if account.plan else None,
            'date_joined': account.created_at.strftime('%Y-%m-%d'),
        }
    }, status=http_status)


# ── Custom JWT: add role/name/email to token claims ───────────────────────────

class GPDTokenObtainSerializer(TokenObtainPairSerializer):
    """UC-1: Log In — adds role/name to JWT payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['name']  = user.name
        token['role']  = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.status == 'inactive':
            raise drf_serializers.ValidationError(
                'Your account has been deactivated by an administrator.'
            )
        data['user'] = {
            'id':         self.user.id,
            'name':       self.user.name,
            'email':      self.user.email,
            'role':       self.user.role,
            'status':     self.user.status,
            'plan':       self.user.plan.name if self.user.plan else None,
            'date_joined': self.user.created_at.strftime('%Y-%m-%d'),
        }
        return data


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: { email, password }
    Response: { access, refresh, user }
    """
    serializer_class  = GPDTokenObtainSerializer
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        # Step 1: Check if user exists and is inactive BEFORE simplejwt runs
        # This way we control the error message and status code
        from apps.accounts.models import User
        from rest_framework.response import Response
        from rest_framework import status as drf_status

        email = request.data.get('email', '').strip().lower()
        
        try:
            user = User.objects.get(email__iexact=email)
            if user.status == 'inactive':
                return Response(
                    {'detail': 'Your account has been deactivated by an administrator.'},
                    status=drf_status.HTTP_400_BAD_REQUEST  # your expected status
                )
        except User.DoesNotExist:
            pass  # let simplejwt handle wrong credentials normally

        # Step 2: proceed with normal simplejwt flow
        return super().post(request, *args, **kwargs)

# ── Registration — 2-step OTP flow ────────────────────────────────────────────

class SendOTPView(APIView):
    """
    POST /api/auth/register/send-otp/
    Step 1: Validate form data and email a 6-digit OTP code.
    Body: { name, email, password, confirm_password, plan_id }
    Response: { message: "OTP sent to <email>" }

    The user is NOT created yet — they must verify the OTP first.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            serializer.send_otp()
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}. Check your email settings.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        email = serializer.validated_data['email']
        return Response({'message': f'Verification code sent to {email}. Check your inbox.'})


class VerifyOTPView(APIView):
    """
    POST /api/auth/register/verify-otp/
    Step 2: Verify the OTP code and create the account.
    Body: { name, email, password, plan_id, otp_code }
    Response: { access, refresh, user } — same as login response (auto-login)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPAndRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.create_user()
        return _build_token_response(account, status.HTTP_201_CREATED)

class ResendOTPView(APIView):
     """
    POST /api/auth/register/resend-otp/
    Resend a fresh OTP to the email.
    Body: { name, email, password, plan_id }
    """
     permission_classes = [AllowAny]

     def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)  # ← use new serializer
        serializer.is_valid(raise_exception=True)
        try:
            serializer.send_otp()
        except Exception as e:
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        email = serializer.validated_data['email']
        return Response({'message': f'New verification code sent to {email}.'})
# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except TokenError:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


# ── Profile ───────────────────────────────────────────────────────────────────

class MeView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/auth/me/  → current user profile
    PATCH /api/auth/me/  → update name/email
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UpdateProfileSerializer
        return UserProfileSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [IsAuthenticated, IsActiveUser]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Password changed successfully.'})


class DeleteAccountView(APIView):
    """
    DELETE /api/auth/me/delete/
    User deletes their own account.
    Requires password confirmation for security.
    Body: { password: string }
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def delete(self, request):
        password = request.data.get('password')
        if not password:
            return Response(
                {'error': 'Password is required to delete your account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not request.user.check_password(password):
            return Response(
                {'error': 'Incorrect password.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        request.user.delete()
        return Response({'message': 'Account deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


# ── Upgrade Plan ──────────────────────────────────────────────────────────────

class UpgradePlanView(APIView):
    """
    PATCH /api/auth/me/upgrade-plan/
    User upgrades their subscription plan.
    Body: { plan_id: number }
    Response: { success: true, message: "...", user: {...} }
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def patch(self, request):
        from apps.plans.models import Plan
        
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response(
                {'error': 'plan_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_plan = Plan.objects.get(pk=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {'error': 'Selected plan does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update user's plan
        request.user.plan = new_plan
        request.user.save(update_fields=['plan'])
        
        return Response({
            'success': True,
            'message': f'Plan upgraded to {new_plan.name}.',
            'user': {
                'id':         request.user.id,
                'name':       request.user.name,
                'email':      request.user.email,
                'role':       request.user.role,
                'status':     request.user.status,
                'plan':       new_plan.name,
                'date_joined': request.user.created_at.strftime('%Y-%m-%d'),
            }
        }, status=status.HTTP_200_OK)

"""
Accounts — Serializers
"""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, Admin, Account, OTPVerification
import random, string


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


class SendOTPSerializer(serializers.Serializer):
    """
    Step 1 of registration — validate form data, send OTP to email.
    Does NOT create the user yet.
    """
    name             = serializers.CharField(max_length=150)
    email            = serializers.EmailField()
    password         = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    plan_id          = serializers.IntegerField()

    def validate_email(self, value):
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate_plan_id(self, value):
        from apps.plans.models import Plan
        if not Plan.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Selected plan does not exist.')
        return value

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def send_otp(self):
        """Generate OTP, save it, send the email. Returns the OTP code."""
        from django.core.mail import send_mail
        from django.conf import settings

        email = self.validated_data['email']

        # Invalidate any previous unused OTPs for this email
        OTPVerification.objects.filter(email=email, is_used=False).update(is_used=True)

        code = generate_otp()
        OTPVerification.objects.create(email=email, code=code)

        send_mail(
            subject='Your GPD Verification Code',
            message=(
                f'Hi {self.validated_data["name"]},\n\n'
                f'Your verification code is: {code}\n\n'
                f'This code expires in 10 minutes.\n\n'
                f'If you did not sign up for GPD, please ignore this email.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return code


class VerifyOTPAndRegisterSerializer(serializers.Serializer):
    """
    Step 2 of registration — verify OTP and create the account.
    Receives all original form data + the OTP code.
    """
    name     = serializers.CharField(max_length=150)
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    plan_id  = serializers.IntegerField()
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        email    = data['email']
        otp_code = data['otp_code']

        # Find the latest unused OTP for this email
        otp = OTPVerification.objects.filter(
            email=email, code=otp_code, is_used=False
        ).order_by('-created_at').first()

        if not otp:
            raise serializers.ValidationError({'otp_code': 'Invalid verification code.'})

        if otp.is_expired():
            raise serializers.ValidationError({'otp_code': 'Verification code has expired. Please request a new one.'})

        data['_otp'] = otp
        return data

    def create_user(self):
        """Mark OTP used and create the user account."""
        from apps.plans.models import Plan
        validated = self.validated_data

        otp = validated.pop('_otp')
        otp.is_used = True
        otp.save(update_fields=['is_used'])

        plan    = Plan.objects.get(pk=validated['plan_id'])
        account = Account.objects.create_user(
            email=validated['email'],
            name=validated['name'],
            password=validated['password'],
            plan=plan,
            role='user',
            is_email_verified=True,
        )
        return account


# ── Profile serializers ───────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    plan_name   = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model  = Account
        fields = ['id', 'name', 'email', 'role', 'status', 'plan_name', 'date_joined', 'is_email_verified']
        read_only_fields = ['role', 'status', 'is_email_verified']

    def get_plan_name(self, obj):
        return obj.plan.name if obj.plan else None


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Account
        fields = ['name', 'email']

    def validate_email(self, value):
        user = self.context['request'].user
        if Account.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password     = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class AdminAccountSerializer(serializers.ModelSerializer):
    """UC-9: Admin view/edit user accounts."""
    plan_name   = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model  = Account
        fields = ['id', 'name', 'email', 'role', 'status', 'plan_name', 'date_joined']
        read_only_fields = ['name', 'email', 'role', 'plan_name', 'date_joined']

    def get_plan_name(self, obj):
        return obj.plan.name if obj.plan else None

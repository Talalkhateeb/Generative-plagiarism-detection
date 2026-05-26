"""
Accounts App — Models
Class Diagram: account (base) → user (sibling) + admin (sibling)

Proxy model pattern:
  - Account : one DB table, all shared fields
  - User    : proxy of Account, role='user', user-specific methods
  - Admin   : proxy of Account, role='admin', admin-specific methods

IMPORTANT: AUTH_USER_MODEL = 'accounts.User' (Django requires this to stay
as User for migrations). The User model's DEFAULT manager must NOT filter
by role — otherwise Django auth cannot find admin accounts during login.
Role filtering only happens via User.role_objects and Admin.objects.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# Base Manager — used for AUTH (must see ALL roles) 

class AccountManager(BaseUserManager): 
    """
    Default manager — no role filter.
    Django's authentication backend uses this to look up users by email.
    If we filter by role here, admin accounts become invisible to JWT login.
    """
    def create_user(self, email, name, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        # Remove confirm_password if accidentally passed
        extra.pop('confirm_password', None)
        user = self.model(email=email, name=name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra):
        # Force admin role — do NOT use setdefault, it won't override defaults
        extra['role']             = 'admin'
        extra['is_staff']         = True
        extra['is_superuser']     = True
        extra['status']           = 'active'
        extra['is_email_verified'] = True
        return self.create_user(email, name, password, **extra)


# Role-filtered managers (for querying, NOT for auth) 
class UserRoleManager(AccountManager):
    """Use this when you want ONLY users: User.role_objects.all()"""
    def get_queryset(self):
        return super().get_queryset().filter(role='user')


class AdminRoleManager(AccountManager):
    """Use this when you want ONLY admins: Admin.objects.all()"""
    def get_queryset(self):
        return super().get_queryset().filter(role='admin')


# Account / User model (one DB table) 
class User(AbstractBaseUser, PermissionsMixin):
    """
    Main auth model — named 'User' because AUTH_USER_MODEL = 'accounts.User'
    and this cannot change after migrations.

    Conceptually this IS the 'Account' base class from the class diagram.
    The Admin proxy model below represents the admin sibling.

    Fields: name, id, email, password, status, created_at, role
    """
    ROLE_CHOICES   = [('user', 'User'), ('admin', 'Admin')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive')]

    name              = models.CharField(max_length=150)
    email             = models.EmailField(unique=True)
    role              = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    status            = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    plan              = models.ForeignKey(
        'plans.Plan', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='subscribers'
    )
    created_at        = models.DateTimeField(auto_now_add=True)
    is_email_verified = models.BooleanField(default=False)
    is_staff          = models.BooleanField(default=False)
    is_active         = models.BooleanField(default=True)

    # Default manager — NO role filter (required for Django auth to work)
    objects      = AccountManager()
    # Role-filtered manager — use when you only want regular users
    role_objects = UserRoleManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'User'
        ordering     = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}> [{self.role}]'

    def is_admin(self):
        return self.role == 'admin'

    def display_account(self):
        return {'name': self.name, 'email': self.email, 'role': self.role, 'status': self.status}

    def save(self, *args, **kwargs):
        # Only deactivate if explicitly inactive — never block active accounts
        if self.status == 'inactive':
            self.is_active = False
        else:
            self.is_active = True
        # Admins always get staff access
        if self.role == 'admin':
            self.is_staff = True
        super().save(*args, **kwargs)

    def choose_plan(self, plan_id):
        from plans.models import Plan
        self.plan = Plan.objects.get(pk=plan_id)
        self.save(update_fields=['plan'])


# Keep Account as an alias so imports like "from .models import Account" still work
Account = User


# Admin proxy model 
class Admin(User):
    """
    Class Diagram: admin(-plan p, -account a) — sibling of User, both inherit Account.
    Proxy model: no extra DB table — uses User table, filters role='admin'.
    """
    objects = AdminRoleManager()

    class Meta:
        proxy        = True 
        managed = False  
        verbose_name = 'Admin'
        app_label = 'accounts' 
    def edit_ustate(self, account_id, new_status):
        User.objects.filter(pk=account_id).update(
            status=new_status,
            is_active=(new_status == 'active')
        )


# OTP Verification 
class OTPVerification(models.Model):
    """
    Stores 6-digit OTP codes for email verification during signup.
    Expires after 10 minutes.
    """
    email      = models.EmailField(db_index=True)
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'OTP for {self.email} — used={self.is_used}'
    def is_expired(self):
     from django.utils import timezone
     from datetime import timedelta
     # Ensure both sides are timezone-aware
     now = timezone.now()
     created = self.created_at
    # Safety: if created_at is naive (MSSQL issue), make it aware
     if created.tzinfo is None:
        from django.utils.timezone import make_aware
        created = make_aware(created)
     return now > created + timedelta(minutes=10)
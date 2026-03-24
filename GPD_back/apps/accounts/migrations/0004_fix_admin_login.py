"""
Migration 0004:
- Sets is_active=True and status='active' for all existing accounts
- Sets is_email_verified=True for superusers/admins
- This fixes the admin login issue caused by incorrect is_active values
"""
from django.db import migrations


def fix_admin_accounts(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    # Fix all accounts — make sure active status matches is_active
    User.objects.filter(status='active').update(is_active=True)
    User.objects.filter(status='inactive').update(is_active=False)
    # Fix admins — make sure they have all required flags
    User.objects.filter(is_superuser=True).update(
        role='admin',
        is_staff=True,
        is_active=True,
        status='active',
        is_email_verified=True,
    )
    User.objects.filter(role='admin').update(
        is_staff=True,
        is_active=True,
        status='active',
        is_email_verified=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_account_and_admin_proxy'),
    ]

    operations = [
        migrations.RunPython(fix_admin_accounts, migrations.RunPython.noop),
    ]

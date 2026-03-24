"""
Migration 0003:
- Rename the DB model from 'User' to 'Account'
- Create User proxy model (role='user')
- Create Admin proxy model (role='admin')

The Admin proxy MUST be in the same migration as the rename,
after the rename operation, so its base (Account) exists.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_otp_and_email_verified'),
    ]

    operations = [
        # Step 1: rename User → Account in the DB
        migrations.RenameModel(
            old_name='User',
            new_name='Account',
        ),

        # Step 2: create User proxy (base is now Account)
        migrations.CreateModel(
            name='User',
            fields=[],
            options={
                'proxy': True,
                'verbose_name': 'User',
                'indexes': [],
                'constraints': [],
            },
            bases=('accounts.account',),
        ),

        # Step 3: create Admin proxy (base is now Account)
        migrations.CreateModel(
            name='Admin',
            fields=[],
            options={
                'proxy': True,
                'verbose_name': 'Admin',
                'indexes': [],
                'constraints': [],
            },
            bases=('accounts.account',),
        ),
    ]

"""
Run this script to seed initial data:
  python manage.py shell < seed_data.py

Creates:
  - 3 Plans (Starter, Pro, Enterprise)
  - 1 Admin user (admin@GPD.ai / admin123)
  - 1 Regular user (user@GPD.ai / user123)
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GPD_Back.settings')
django.setup()

from apps.plans.models import Plan
from apps.accounts.models import User

# Plans
plans_data = [
    {'name': 'Starter',    'price': 9,  'checks_per_month': 10, 'max_sources': 5,  'max_documents': 3,  'allowed_formats': ['pdf','txt']},
    {'name': 'Pro',        'price': 29, 'checks_per_month': 50, 'max_sources': 20, 'max_documents': 10, 'allowed_formats': ['pdf','docx','txt']},
    {'name': 'Enterprise', 'price': 99, 'checks_per_month': -1, 'max_sources': -1, 'max_documents': -1, 'allowed_formats': ['pdf','docx','doc','txt']},
]

print('Creating plans...')
for p in plans_data:
    plan, created = Plan.objects.get_or_create(name=p['name'], defaults=p)
    print(f'  {"Created" if created else "Exists"}: {plan}')

enterprise = Plan.objects.get(name='Enterprise')
pro        = Plan.objects.get(name='Pro')

# Admin
if not User.objects.filter(email='admin@gmail.com').exists():
    admin = User.objects.create_superuser(
        email='admin@gmail.com', name='Tala Alkhateeb',
        password='talaispretty', role='admin', plan=enterprise
    )
    print(f'Created admin: {admin}')

# Regular user
if not User.objects.filter(email='user@gmail.com').exists():
    user = User.objects.create_user(
        email='user@gmail.com', name='Farah Alkayyem',
        password='farah123', role='user', plan=pro
    )
    print(f'Created user: {user}')

print('\nSeed complete!')
print('Admin: admin@gmail.com / talaispretty')
print('User:  user@gmail.com  / farah123')

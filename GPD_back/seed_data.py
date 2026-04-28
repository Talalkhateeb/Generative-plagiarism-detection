"""
Backward-compatible seed entrypoint.

Preferred usage:
  python manage.py shell < scripts/seed_data.py
"""

from scripts.seed_data import *  # noqa: F401,F403

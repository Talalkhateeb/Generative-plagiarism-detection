import os

from .settings import *  # noqa: F401,F403


if os.environ.get("CI", "false").lower() == "true":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
else:
    DATABASES["default"]["TEST"] = {
        "NAME": os.environ.get("TEST_DB_NAME", "GPD_test"),
    }

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

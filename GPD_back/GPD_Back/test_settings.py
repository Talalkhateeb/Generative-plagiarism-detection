import os

from .settings import *  # noqa: F401,F403


DATABASES["default"]["TEST"] = {
    "NAME": os.environ.get("TEST_DB_NAME", "GPD_test"),
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

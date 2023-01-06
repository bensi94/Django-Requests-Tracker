import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    "requests_tracker",
    "django.contrib.auth",
    "django.contrib.contenttypes",
]


TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates"}]


DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "test_db"}}

ROOT_URLCONF = "tests.urls"

DEBUG = True

INTERNAL_IPS = ["127.0.0.1"]

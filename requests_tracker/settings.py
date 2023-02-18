from functools import lru_cache
from typing import Any

from django.conf import settings
from django.http import HttpRequest

from requests_tracker import APP_NAME

CONFIG_DEFAULTS = {
    "ENABLE_STACKTRACES": True,
    "ENABLE_STACKTRACES_LOCALS": False,
    "HIDE_IN_STACKTRACES": (
        "socketserver",
        "threading",
        "wsgiref",
        APP_NAME,
        "django.db",
        "django.core.handlers",
        "django.core.servers",
        "django.utils.decorators",
        "django.utils.deprecation",
        "django.utils.functional",
    ),
    "SQL_WARNING_THRESHOLD": 500,  # milliseconds
    "REQUESTS_TRACKER_CONFIG": True,
    "TRACK_SQL": True,
    "IGNORE_SQL_PATTERNS": (),
    "IGNORE_PATHS_PATTERNS": (),
}


@lru_cache()
def get_config() -> dict[str, Any]:
    user_config = getattr(settings, "REQUESTS_TRACKER_CONFIG", {})
    config = CONFIG_DEFAULTS.copy()
    config.update(user_config)
    return config


def debug_application(request: HttpRequest) -> bool:
    requests_tracker_app = get_config()["REQUESTS_TRACKER_CONFIG"]
    return (
        requests_tracker_app
        and settings.DEBUG
        and request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS
    )

from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from requests_tracker import APP_NAME
from requests_tracker.settings import get_config
from requests_tracker.sql.sql_hook import install_sql_hook


class RequestsTrackerConfig(AppConfig):
    name = APP_NAME
    verbose_name = _("Requests tracker")

    def ready(self) -> None:
        requests_tracker_config = get_config()
        if settings.DEBUG and requests_tracker_config.get("TRACK_SQL", True):
            install_sql_hook()

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from requests_tracker import APP_NAME


class RequestsTrackerConfig(AppConfig):
    name = APP_NAME
    verbose_name = _("Requests tracker")

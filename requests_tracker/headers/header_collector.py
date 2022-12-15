from itertools import chain

from django.http import HttpRequest, HttpResponse

from requests_tracker.base_collector import Collector


class HeaderCollector(Collector):
    """
    Collects the request's HTTP headers.
    """

    request_headers: dict[str, str]
    response_headers: dict[str, str]
    environ: dict[str, str]

    # List of environment variables we want to display
    ENVIRON_FILTER = {
        "CONTENT_LENGTH",
        "CONTENT_TYPE",
        "DJANGO_SETTINGS_MODULE",
        "GATEWAY_INTERFACE",
        "QUERY_STRING",
        "PATH_INFO",
        "PYTHONPATH",
        "REMOTE_ADDR",
        "REMOTE_HOST",
        "REQUEST_METHOD",
        "SCRIPT_NAME",
        "SERVER_NAME",
        "SERVER_PORT",
        "SERVER_PROTOCOL",
        "SERVER_SOFTWARE",
        "TZ",
    }

    def __init__(self) -> None:
        self.request_headers = {}
        self.response_headers = {}
        self.environ = {}

    def process_request(self, request: HttpRequest, response: HttpResponse) -> None:
        request_env = sorted(request.META.items())
        self.request_headers = {
            unmangle(key): value for (key, value) in request_env if is_http_header(key)
        }
        self.response_headers = dict(response.items())
        self.environ = {
            key: value for (key, value) in request_env if key in self.ENVIRON_FILTER
        }

    def matches_search_filter(self, search: str) -> bool:
        search = search.lower()
        return next(
            (
                True
                for header_value in chain(
                    self.request_headers.values(),
                    self.response_headers.values(),
                    self.environ.values(),
                )
                if search in header_value.lower()
            ),
            False,
        )

    def generate_statistics(self) -> None:
        ...


def is_http_header(key: str) -> bool:
    # The WSGI spec says that keys should be str objects in the environ dict,
    # but this isn't true in practice. See issues #449 and #482.
    return isinstance(key, str) and key.startswith("HTTP_")


def unmangle(key: str) -> str:
    return key[5:].replace("_", "-").title()

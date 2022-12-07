import pytest
from django.http import HttpRequest, HttpResponse
from django.http.response import ResponseHeaders

from requests_tracker.headers.header_collector import HeaderCollector


@pytest.fixture
def header_collector() -> HeaderCollector:
    return HeaderCollector()


def test_process_request(header_collector: HeaderCollector) -> None:
    request = HttpRequest()
    request.META = {
        "HTTP_ACCEPT": "application/json: text/plain: */*",
        "HTTP_SEC_CH_UA_PLATFORM": "macOS",
        "HTTP_SEC_FETCH_SITE": "same-origin",
        "CONTENT_TYPE": "text/plain",
    }
    response = HttpResponse()
    response.headers = ResponseHeaders(
        {"Allow": "GET, POST, HEAD, OPTIONS", "Vary": "Accept"}
    )

    header_collector.process_request(request, response)

    assert header_collector.request_headers == {
        "Accept": "application/json: text/plain: */*",
        "Sec-Ch-Ua-Platform": "macOS",
        "Sec-Fetch-Site": "same-origin",
    }
    assert header_collector.response_headers == {
        "Allow": "GET, POST, HEAD, OPTIONS",
        "Vary": "Accept",
    }
    assert header_collector.environ == {"CONTENT_TYPE": "text/plain"}


@pytest.mark.parametrize(
    "input_search, expected_result",
    [
        ("macO", True),
        ("INVALID", False),
    ],
)
def test_matches_search_filter(
    header_collector: HeaderCollector,
    input_search: str,
    expected_result: bool,
) -> None:
    request = HttpRequest()
    request.META = {
        "HTTP_SEC_CH_UA_PLATFORM": "macOS",
        "CONTENT_TYPE": "text/plain",
    }

    header_collector.process_request(request, HttpResponse())

    assert header_collector.matches_search_filter(input_search) is expected_result

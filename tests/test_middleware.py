from unittest import mock

import pytest
from django.conf import LazySettings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.test import RequestFactory

from requests_tracker.main_request_collector import MainRequestCollector
from requests_tracker.middleware import (
    is_requests_tracker_request,
    requests_tracker_middleware,
)


@pytest.mark.parametrize(
    "request_path, expected_response",
    [("/__requests-tracker__/", True), ("/some-random-path", False)],
)
def test_is_requests_tracker_request(
    request_factory: RequestFactory,
    request_path: str,
    expected_response: bool,
) -> None:
    request = request_factory.get(request_path)
    assert is_requests_tracker_request(request) is expected_response


def test_middleware_sync_settings_debug(
    request_factory: RequestFactory,
    settings: LazySettings,
) -> None:
    settings.DEBUG = True
    get_response = mock.MagicMock()
    request = request_factory.get("/")
    requests_tracker_request = request_factory.get("/__requests-tracker__/")

    middleware = requests_tracker_middleware(get_response)
    response = middleware(request)
    middleware(requests_tracker_request)

    request_collectors = requests_tracker_request.request_collectors  # type: ignore
    assert get_response.return_value == response
    assert len(request_collectors) == 1
    request_collector: MainRequestCollector = list(request_collectors.values())[0]
    assert request_collector.finished is True
    assert request_collector.django_view == "tests.fake_views.fake_view"


@pytest.mark.asyncio
async def test_middleware_async_settings_debug(
    request_factory: RequestFactory,
    settings: LazySettings,
) -> None:
    settings.DEBUG = True

    async def get_response_async(django_request: WSGIRequest) -> HttpResponse:
        return HttpResponse(f"Fake response from {django_request.path}")

    get_response = get_response_async
    request = request_factory.get("/")
    requests_tracker_request = request_factory.get("/__requests-tracker__/")

    middleware = requests_tracker_middleware(get_response)
    response = await middleware(request)
    await middleware(requests_tracker_request)

    request_collectors = requests_tracker_request.request_collectors  # type: ignore
    assert len(request_collectors) == 1
    assert response.content == b"Fake response from /"
    request_collector: MainRequestCollector = list(request_collectors.values())[0]
    assert request_collector.finished is True
    assert request_collector.django_view == "tests.fake_views.fake_view"

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


@pytest.fixture(autouse=True)
def debug_settings(settings: LazySettings) -> None:
    settings.DEBUG = True


async def get_response_async(django_request: WSGIRequest) -> HttpResponse:
    return HttpResponse(f"Fake response from {django_request.path}")


@pytest.mark.parametrize(
    "request_path, expected_response",
    [("/__requests_tracker__/", True), ("/some-random-path", False)],
)
def test_is_requests_tracker_request(
    request_factory: RequestFactory,
    request_path: str,
    expected_response: bool,
) -> None:
    request = request_factory.get(request_path)
    assert is_requests_tracker_request(request) is expected_response


def test_middleware_sync_settings_debug(request_factory: RequestFactory) -> None:
    get_response = mock.MagicMock()
    request = request_factory.get("/")
    requests_tracker_request = request_factory.get("/__requests_tracker__/")

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
async def test_middleware_async_settings_debug(request_factory: RequestFactory) -> None:
    request = request_factory.get("/")
    requests_tracker_request = request_factory.get("/__requests_tracker__/")

    middleware = requests_tracker_middleware(get_response_async)
    response = await middleware(request)
    await middleware(requests_tracker_request)

    request_collectors = requests_tracker_request.request_collectors  # type: ignore
    assert len(request_collectors) == 1
    assert response.content == b"Fake response from /"
    request_collector: MainRequestCollector = list(request_collectors.values())[0]
    assert request_collector.finished is True
    assert request_collector.django_view == "tests.fake_views.fake_view"


def test_middleware_sync_settings_not_debug(
    request_factory: RequestFactory,
    settings: LazySettings,
) -> None:
    settings.DEBUG = False
    get_response = mock.MagicMock()

    middleware = requests_tracker_middleware(get_response)

    requests_tracker_request = request_factory.get("/__requests_tracker__/")
    middleware(requests_tracker_request)

    assert hasattr(requests_tracker_request, "request_collectors") is False


@pytest.mark.asyncio
async def test_middleware_async_settings_not_debug(
    request_factory: RequestFactory,
    settings: LazySettings,
) -> None:
    settings.DEBUG = False

    middleware = requests_tracker_middleware(get_response_async)

    requests_tracker_request = request_factory.get("/__requests_tracker__/")
    await middleware(requests_tracker_request)

    assert hasattr(requests_tracker_request, "request_collectors") is False


def test_middleware_requests_tracker_clear(request_factory: RequestFactory) -> None:
    get_response = mock.MagicMock()
    requests_tracker_request = request_factory.get("/__requests_tracker__/")

    middleware = requests_tracker_middleware(get_response)
    middleware(request_factory.get("/"))
    middleware(requests_tracker_request)
    middleware(request_factory.delete("/__requests_tracker__/delete"))

    request_collectors = requests_tracker_request.request_collectors  # type: ignore

    assert request_collectors == {}


@pytest.mark.asyncio
async def test_middleware_requests_tracker_clear_async(
    request_factory: RequestFactory,
) -> None:
    requests_tracker_request = request_factory.get("/__requests_tracker__/")

    middleware = requests_tracker_middleware(get_response_async)
    await middleware(request_factory.get("/"))
    await middleware(requests_tracker_request)
    await middleware(request_factory.delete("/__requests_tracker__/delete"))

    request_collectors = requests_tracker_request.request_collectors  # type: ignore

    assert request_collectors == {}

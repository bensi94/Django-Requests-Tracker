import asyncio
from typing import Any
from uuid import UUID

from django.conf import settings
from django.http import HttpRequest
from django.urls import Resolver404, resolve
from django.utils.decorators import sync_and_async_middleware

from requests_tracker import APP_NAME
from requests_tracker.main_request_collector import MainRequestCollector
from requests_tracker.settings import debug_application
from requests_tracker.sql.sql_hook import install_sql_hook
from requests_tracker.sql.sql_tracker import SQLTracker


class RequestWithCollectors(HttpRequest):
    request_collectors: dict[UUID, MainRequestCollector]


def is_requests_tracker_request(request: HttpRequest) -> bool:
    try:
        resolver_match = request.resolver_match or resolve(
            request.path,
            getattr(request, "urlconf", None),
        )
    except Resolver404:
        return False
    return bool(resolver_match.namespaces and resolver_match.namespaces[-1] == APP_NAME)


async def middleware_async(
    request: RequestWithCollectors,
    get_response: Any,
    request_collectors: dict[UUID, MainRequestCollector],
) -> Any:
    if not debug_application(request):
        return await get_response(request)

    if is_requests_tracker_request(request):
        if (
            request.method == "DELETE"
            and request.path == "/__requests_tracker__/delete"
        ):
            request_collectors.clear()
        request.request_collectors = request_collectors
        return await get_response(request)

    request_collector = MainRequestCollector(request)
    request_collectors[request_collector.request_id] = request_collector

    with SQLTracker(request_collector.sql_collector):
        response = await get_response(request)
    request_collector.wrap_up_request(response)

    return response


def middleware_sync(
    request: RequestWithCollectors,
    get_response: Any,
    request_collectors: dict[UUID, MainRequestCollector],
) -> Any:
    if not debug_application(request):
        return get_response(request)

    if is_requests_tracker_request(request):
        if (
            request.method == "DELETE"
            and request.path == "/__requests_tracker__/delete"
        ):
            request_collectors.clear()
        request.request_collectors = request_collectors
        return get_response(request)

    request_collector = MainRequestCollector(request)
    request_collectors[request_collector.request_id] = request_collector

    with SQLTracker(request_collector.sql_collector):
        response = get_response(request)
    request_collector.wrap_up_request(response)

    return response


@sync_and_async_middleware
def requests_tracker_middleware(
    get_response: Any,
) -> Any:
    request_collectors: dict[UUID, MainRequestCollector] = {}

    if settings.DEBUG:
        install_sql_hook()

    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request: RequestWithCollectors) -> Any:
            return await middleware_async(request, get_response, request_collectors)

    else:

        def middleware(request: RequestWithCollectors) -> Any:  # type: ignore
            return middleware_sync(request, get_response, request_collectors)

    return middleware

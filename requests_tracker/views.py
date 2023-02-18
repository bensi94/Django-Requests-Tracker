from datetime import datetime
from typing import Dict, Optional, Tuple, Union
from uuid import UUID

from django.conf import settings
from django.template.response import TemplateResponse
from django.views.debug import get_default_exception_reporter_filter

from requests_tracker.main_request_collector import MainRequestCollector
from requests_tracker.middleware import RequestWithCollectors

RequestsType = Dict[UUID, MainRequestCollector]


def is_htmx_request(request: RequestWithCollectors) -> bool:
    return request.headers.get("HX-Request", "").lower() == "true"


def is_htmx_search_or_sort_request(request: RequestWithCollectors) -> bool:
    return request.headers.get("HX-Target") == "request-list-search-results"


def sort_requests(
    requests: RequestsType,
    requests_sorter: str,
    requests_direction: str,
) -> RequestsType:
    def sort_func(
        item: Tuple[UUID, MainRequestCollector]
    ) -> Optional[Union[str, int, datetime]]:
        _, request = item
        if requests_sorter == "time":
            return request.start_time
        elif requests_sorter == "duration":
            return request.duration
        elif requests_sorter == "name":
            return str(request.request.path)
        elif requests_sorter == "view":
            return request.django_view
        elif requests_sorter == "query_count":
            return request.sql_collector.num_queries
        elif requests_sorter == "duplicate_query_count":
            return request.sql_collector.total_duplicate_queries
        elif requests_sorter == "similar_query_count":
            return request.sql_collector.total_similar_queries
        else:
            return request.start_time

    reverse = requests_direction != "ascending"
    return dict(
        sorted(requests.items(), key=sort_func, reverse=reverse)  # type: ignore
    )


def index(request: RequestWithCollectors) -> TemplateResponse:
    requests_filter = request.GET.get("requests_filter", "")
    requests_sorter = request.GET.get("requests_sorter", "time")
    requests_direction = request.GET.get("requests_direction", "")

    sorted_requests = sort_requests(
        request.request_collectors,
        requests_sorter,
        requests_direction,
    )

    requests = {
        request_id: request_collector.get_as_context()
        for request_id, request_collector in list(sorted_requests.items())
        if not requests_filter
        or request_collector.matches_search_filter(requests_filter)
    }

    template = "index.html"

    if is_htmx_search_or_sort_request(request):
        template = "partials/request_list_only_partial.html"
    elif is_htmx_request(request):
        template = "partials/request_list_partial.html"

    return TemplateResponse(
        request,
        template,
        context={
            "requests": requests,
            "requests_filter": requests_filter,
            "requests_sorter": requests_sorter,
            "requests_direction": requests_direction,
        },
    )


def single_request_item(
    request: RequestWithCollectors, request_id: UUID
) -> TemplateResponse:
    return TemplateResponse(
        request,
        "partials/request_list_item.html",
        context={
            "request": request.request_collectors[request_id],
            "request_id": request_id,
        },
    )


def clear_request_list(request: RequestWithCollectors) -> TemplateResponse:
    return index(request)


def request_details(
    request: RequestWithCollectors,
    request_id: Union[str, UUID],
) -> TemplateResponse:
    template = (
        "partials/request_details_partial.html"
        if is_htmx_request(request)
        else "request_details.html"
    )
    context = request.request_collectors[UUID(str(request_id))].get_as_context()

    return TemplateResponse(request=request, template=template, context=context)


get_safe_settings = get_default_exception_reporter_filter().get_safe_settings


def django_settings(request: RequestWithCollectors) -> TemplateResponse:
    return TemplateResponse(
        request=request,
        template="django_settings.html",
        context={
            "django_settings": dict(sorted(get_safe_settings().items())),
            "django_settings_module": settings.SETTINGS_MODULE,
        },
    )

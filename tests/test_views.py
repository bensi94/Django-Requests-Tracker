from datetime import datetime
from uuid import UUID

import pytest
from django.template.response import TemplateResponse
from django.test import RequestFactory

from requests_tracker.main_request_collector import MainRequestCollector
from requests_tracker.middleware import RequestWithCollectors
from requests_tracker.sql.dataclasses import PerDatabaseInfo
from requests_tracker.sql.sql_collector import SQLCollector
from requests_tracker.views import (
    clear_request_list,
    django_settings,
    index,
    is_htmx_request,
    is_htmx_search_or_sort_request,
    request_details,
    single_request_item,
    sort_requests,
)


@pytest.mark.parametrize(
    "custom_headers, expected_result",
    [
        ({"HTTP_HX-Request": "true"}, True),
        ({"HTTP_HX-Request": "false"}, False),
        ({}, False),
    ],
)
def test_is_htmx_request(
    request_factory: RequestFactory,
    custom_headers: dict[str, str],
    expected_result: bool,
) -> None:
    request: RequestWithCollectors = request_factory.get(
        "/",
        **custom_headers,  # type: ignore
    )
    assert is_htmx_request(request) is expected_result


@pytest.mark.parametrize(
    "custom_headers, expected_result",
    [
        ({"HTTP_HX-Target": "request-list-search-results"}, True),
        ({"HTTP_HX-Target": "invalid"}, False),
        ({}, False),
    ],
)
def test_is_htmx_search_or_sort_request(
    request_factory: RequestFactory,
    custom_headers: dict[str, str],
    expected_result: bool,
) -> None:
    request: RequestWithCollectors = request_factory.get(
        "/",
        **custom_headers,  # type: ignore
    )
    assert is_htmx_search_or_sort_request(request) is expected_result


@pytest.mark.parametrize(
    "requests_sorter, requests_direction, expected_order",
    [
        (
            "time",
            "ascending",
            [UUID(int=5), UUID(int=3), UUID(int=4), UUID(int=2), UUID(int=1)],
        ),
        (
            "time",
            "descending",
            [UUID(int=1), UUID(int=2), UUID(int=4), UUID(int=3), UUID(int=5)],
        ),
        (
            "duration",
            "ascending",
            [UUID(int=1), UUID(int=3), UUID(int=4), UUID(int=2), UUID(int=5)],
        ),
        (
            "duration",
            "descending",
            [UUID(int=5), UUID(int=2), UUID(int=4), UUID(int=3), UUID(int=1)],
        ),
        (
            "name",
            "ascending",
            [UUID(int=3), UUID(int=5), UUID(int=2), UUID(int=1), UUID(int=4)],
        ),
        (
            "name",
            "descending",
            [UUID(int=4), UUID(int=1), UUID(int=2), UUID(int=5), UUID(int=3)],
        ),
        (
            "view",
            "ascending",
            [UUID(int=3), UUID(int=5), UUID(int=2), UUID(int=1), UUID(int=4)],
        ),
        (
            "view",
            "descending",
            [UUID(int=4), UUID(int=1), UUID(int=2), UUID(int=5), UUID(int=3)],
        ),
        (
            "query_count",
            "ascending",
            [UUID(int=1), UUID(int=2), UUID(int=4), UUID(int=3), UUID(int=5)],
        ),
        (
            "query_count",
            "descending",
            [UUID(int=5), UUID(int=3), UUID(int=4), UUID(int=2), UUID(int=1)],
        ),
        (
            "duplicate_query_count",
            "ascending",
            [UUID(int=1), UUID(int=5), UUID(int=2), UUID(int=4), UUID(int=3)],
        ),
        # Descending is not exactly reverse because some values are equal
        (
            "duplicate_query_count",
            "descending",
            [UUID(int=3), UUID(int=2), UUID(int=4), UUID(int=1), UUID(int=5)],
        ),
        (
            "similar_query_count",
            "ascending",
            [UUID(int=1), UUID(int=5), UUID(int=2), UUID(int=4), UUID(int=3)],
        ),
        # Descending is not exactly reverse because some values are equal
        (
            "similar_query_count",
            "descending",
            [UUID(int=3), UUID(int=4), UUID(int=2), UUID(int=1), UUID(int=5)],
        ),
        (
            "",
            "ascending",
            [UUID(int=5), UUID(int=3), UUID(int=4), UUID(int=2), UUID(int=1)],
        ),
        (
            "",
            "descending",
            [UUID(int=1), UUID(int=2), UUID(int=4), UUID(int=3), UUID(int=5)],
        ),
    ],
)
def test_sort_requests(
    requests_sorter: str,
    requests_direction: str,
    expected_order: list[UUID],
    request_factory: RequestFactory,
) -> None:
    main_collector_1 = MainRequestCollector(request_factory.get("/d"))
    main_collector_1.start_time = datetime(2023, 1, 1, 0, 0, 5)
    main_collector_1.end_time = datetime(2023, 1, 1, 0, 0, 6)
    main_collector_1.django_view = "view_d"
    sql_collector_1 = SQLCollector()
    sql_collector_1.num_queries = 0
    sql_collector_1.databases = {"default": PerDatabaseInfo(0, 0, 0, 0)}
    main_collector_1.sql_collector = sql_collector_1

    main_collector_2 = MainRequestCollector(request_factory.get("/c"))
    main_collector_2.start_time = datetime(2023, 1, 1, 0, 0, 4)
    main_collector_2.end_time = datetime(2023, 1, 1, 0, 0, 8)
    main_collector_2.django_view = "view_c"
    sql_collector_2 = SQLCollector()
    sql_collector_2.num_queries = 4
    sql_collector_2.databases = {"default": PerDatabaseInfo(40, 4, 4, 2)}

    main_collector_2.sql_collector = sql_collector_2

    main_collector_3 = MainRequestCollector(request_factory.get("/a"))
    main_collector_3.start_time = datetime(2023, 1, 1, 0, 0, 2)
    main_collector_3.end_time = datetime(2023, 1, 1, 0, 0, 4)
    main_collector_3.django_view = "view_a"
    sql_collector_3 = SQLCollector()
    sql_collector_3.num_queries = 10
    sql_collector_3.databases = {"default": PerDatabaseInfo(90, 10, 10, 10)}
    main_collector_3.sql_collector = sql_collector_3

    main_collector_4 = MainRequestCollector(request_factory.get("/e"))
    main_collector_4.start_time = datetime(2023, 1, 1, 0, 0, 3)
    main_collector_4.end_time = datetime(2023, 1, 1, 0, 0, 6)
    main_collector_4.django_view = "view_e"
    sql_collector_4 = SQLCollector()
    sql_collector_4.num_queries = 7
    sql_collector_4.databases = {"default": PerDatabaseInfo(90, 7, 6, 2)}
    main_collector_4.sql_collector = sql_collector_4

    main_collector_5 = MainRequestCollector(request_factory.get("/b"))
    main_collector_5.start_time = datetime(2023, 1, 1, 0, 0, 1)
    main_collector_5.end_time = datetime(2023, 1, 1, 0, 0, 10)
    main_collector_5.django_view = "view_b"
    sql_collector_5 = SQLCollector()
    sql_collector_5.num_queries = 20
    sql_collector_5.databases = {"default": PerDatabaseInfo(90, 20, 0, 0)}
    main_collector_5.sql_collector = sql_collector_5

    requests = {
        UUID(int=1): main_collector_1,
        UUID(int=2): main_collector_2,
        UUID(int=3): main_collector_3,
        UUID(int=4): main_collector_4,
        UUID(int=5): main_collector_5,
    }

    assert (
        list(sort_requests(requests, requests_sorter, requests_direction).keys())
        == expected_order
    )


@pytest.mark.parametrize(
    "custom_headers, expected_template_name",
    [
        ({"HTTP_HX-Request": "true"}, "partials/request_list_partial.html"),
        (
            {"HTTP_HX-Target": "request-list-search-results"},
            "partials/request_list_only_partial.html",
        ),
        ({}, "index.html"),
    ],
)
def test_index(
    custom_headers: dict[str, str],
    expected_template_name: str,
    request_factory: RequestFactory,
) -> None:
    request: RequestWithCollectors = request_factory.get(
        "/",
        **custom_headers,  # type: ignore
    )
    requests_collectors = {UUID(int=1): MainRequestCollector(request)}
    request.request_collectors = requests_collectors

    response = index(request)

    assert isinstance(response, TemplateResponse)
    assert response.template_name == expected_template_name
    assert response._request == request
    assert response.context_data == {
        "requests": {
            key: collector.get_as_context()
            for key, collector in requests_collectors.items()
        },
        "requests_filter": "",
        "requests_sorter": "time",
        "requests_direction": "",
    }


@pytest.mark.parametrize(
    "custom_headers, expected_template_name",
    [
        ({"HTTP_HX-Request": "true"}, "partials/request_list_partial.html"),
        (
            {"HTTP_HX-Target": "request-list-search-results"},
            "partials/request_list_only_partial.html",
        ),
        ({}, "index.html"),
    ],
)
def test_clear_request_list(
    custom_headers: dict[str, str],
    expected_template_name: str,
    request_factory: RequestFactory,
) -> None:
    """
    This is basically the same as test_index,
    because clear_request_list is only relevant inside the middleware,
    otherwise it calls the index view.
    """
    request: RequestWithCollectors = request_factory.get(
        "/",
        **custom_headers,  # type: ignore
    )
    requests_collectors = {UUID(int=1): MainRequestCollector(request)}
    request.request_collectors = requests_collectors

    response = clear_request_list(request)

    assert isinstance(response, TemplateResponse)
    assert response.template_name == expected_template_name
    assert response._request == request
    assert response.context_data == {
        "requests": {
            key: collector.get_as_context()
            for key, collector in requests_collectors.items()
        },
        "requests_filter": "",
        "requests_sorter": "time",
        "requests_direction": "",
    }


def test_single_request_item(request_factory: RequestFactory) -> None:
    request: RequestWithCollectors = request_factory.get("/")  # type: ignore
    request_collector = MainRequestCollector(request)
    request_id = UUID(int=1)
    requests_collectors = {request_id: request_collector}
    request.request_collectors = requests_collectors

    response = single_request_item(request, request_id)

    assert isinstance(response, TemplateResponse)
    assert response.template_name == "partials/request_list_item.html"
    assert response._request == request
    assert response.context_data == {
        "request": request_collector,
        "request_id": request_id,
    }


@pytest.mark.parametrize(
    "custom_headers, expected_template_name",
    [
        ({"HTTP_HX-Request": "true"}, "partials/request_details_partial.html"),
        ({}, "request_details.html"),
    ],
)
def test_request_details(
    custom_headers: dict[str, str],
    expected_template_name: str,
    request_factory: RequestFactory,
) -> None:
    request: RequestWithCollectors = request_factory.get(
        "/",
        **custom_headers,  # type: ignore
    )
    request_collector = MainRequestCollector(request)
    request_id = UUID(int=1)
    requests_collectors = {request_id: request_collector}
    request.request_collectors = requests_collectors

    response = request_details(request, str(request_id))

    assert isinstance(response, TemplateResponse)
    assert response.template_name == expected_template_name
    assert response._request == request
    assert response.context_data == request_collector.get_as_context()


def test_django_settings(request_factory: RequestFactory) -> None:
    request: RequestWithCollectors = request_factory.get("/")  # type: ignore

    response = django_settings(request)

    assert isinstance(response, TemplateResponse)
    assert response.template_name == "django_settings.html"
    assert response._request == request
    assert "django_settings" in response.context_data  # type: ignore
    assert "django_settings_module" in response.context_data  # type: ignore
    assert (
        response.context_data["django_settings_module"]  # type: ignore
        == "tests.django_settings"
    )

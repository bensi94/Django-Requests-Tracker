from datetime import datetime
from uuid import UUID

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from freezegun import freeze_time

from requests_tracker.main_request_collector import MainRequestCollector
from requests_tracker.sql.dataclasses import SQLQueryInfo


@pytest.fixture()
def fake_request(request_factory: RequestFactory) -> HttpRequest:
    return request_factory.get("/__requests_tracker__/")


@pytest.fixture()
def fake_response() -> HttpResponse:
    return HttpResponse()


@pytest.fixture
@freeze_time("2022-12-14 12:00:00")
def collector(fake_request: HttpRequest) -> MainRequestCollector:
    return MainRequestCollector(fake_request)


def test__init__(collector: MainRequestCollector, fake_request: HttpRequest) -> None:
    assert isinstance(collector.request_id, UUID)
    assert collector.request == fake_request
    assert collector.django_view == "requests_tracker.views.index"
    assert collector.start_time == datetime(2022, 12, 14, 12, 0, 0)
    assert collector.end_time is None
    assert collector.response is None
    assert collector.duration is None
    assert collector.finished is False


@freeze_time("2022-12-14 12:00:00")
def test__init__with_not_found_request(request_factory: RequestFactory) -> None:
    request = request_factory.get("/not-found.html")
    collector = MainRequestCollector(request)

    assert collector.request == request
    assert collector.django_view == "NOT FOUND"
    assert collector.start_time == datetime(2022, 12, 14, 12, 0, 0)
    assert collector.end_time is None
    assert collector.response is None
    assert collector.duration is None
    assert collector.finished is False


@freeze_time("2022-12-14 12:00:01")
def test_wrap_up_request(
    collector: MainRequestCollector,
    fake_response: HttpResponse,
) -> None:
    collector.wrap_up_request(fake_response)

    assert collector.end_time == datetime(2022, 12, 14, 12, 0, 1)
    assert collector.response == fake_response
    assert collector.duration == 1000
    assert collector.finished is True


def test_get_collectors(collector: MainRequestCollector) -> None:
    result = collector.get_collectors()

    assert list(result.keys()) == ["sql_collector", "header_collector"]
    assert result["sql_collector"] == collector.sql_collector
    assert result["header_collector"] == collector.header_collector


@freeze_time("2022-12-14 12:00:01")
def test_get_as_context(
    collector: MainRequestCollector,
    fake_request: HttpRequest,
    fake_response: HttpResponse,
) -> None:
    collector.wrap_up_request(fake_response)

    result = collector.get_as_context()

    assert result == {
        "request": fake_request,
        "request_id": collector.request_id,
        "django_view": "requests_tracker.views.index",
        "start_time": datetime(2022, 12, 14, 12, 0, 0),
        "end_time": datetime(2022, 12, 14, 12, 0, 1),
        "duration": 1000,
        "response": fake_response,
        "finished": True,
        **collector.get_collectors(),
    }


@pytest.mark.parametrize(
    "search, request_path, django_view, sql_query, expected_result",
    [
        ("", "", "", "", True),
        ("hello", "", "", "", False),
        ("hello", "/hello/world", "", "", True),
        ("hello", "", "requests_tracker.view.hello_view", "", True),
        ("hello", "", "", "select * from hello", True),
        (
            "hello",
            "/hello/world",
            "requests_tracker.view.hello_view",
            "select * from hello",
            True,
        ),
        (
            "DOES_NOT_EXIT",
            "/hello/world",
            "requests_tracker.view.hello_view",
            "select * from hello",
            False,
        ),
    ],
)
def test_matches_search_filter(
    collector: MainRequestCollector,
    search: str,
    request_path: str,
    django_view: str,
    sql_query: str,
    expected_result: bool,
) -> None:
    collector.request.path = request_path
    collector.django_view = django_view
    collector.sql_collector.queries = [
        SQLQueryInfo(
            vendor="",
            alias="",
            sql=sql_query,
            duration=10,
            raw_sql=sql_query,
            params="",
            raw_params="",
            stacktrace=[],
            start_time=0,
            stop_time=0,
            is_slow=False,
            is_select=False,
        )
    ]

    result = collector.matches_search_filter(search)

    assert result is expected_result

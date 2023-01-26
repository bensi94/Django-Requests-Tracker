from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.http import HttpRequest, HttpResponse
from django.urls import Resolver404, resolve

from requests_tracker.base_collector import Collector
from requests_tracker.headers.header_collector import HeaderCollector
from requests_tracker.sql.sql_collector import SQLCollector


class MainRequestCollector:
    request_id: UUID
    request: HttpRequest
    django_view: str
    start_time: datetime
    end_time: datetime | None
    response: HttpResponse | None

    sql_collector: SQLCollector
    header_collector: HeaderCollector

    def __init__(self, request: HttpRequest):
        self.request_id = uuid4()
        self.request = request
        try:
            self.django_view = resolve(self.request.path)._func_path
        except Resolver404:
            self.django_view = "NOT FOUND"
        self.start_time = datetime.now()
        self.end_time = None
        self.response = None

        self.sql_collector = SQLCollector()
        self.header_collector = HeaderCollector()

    def wrap_up_request(self, response: HttpResponse) -> None:
        """
        Called after Django has processed the request, before response is returned
        """
        self.set_end_time()
        self.response = response
        self.header_collector.process_request(self.request, self.response)

    @property
    def duration(self) -> int | None:
        """duration in milliseconds"""
        return (
            int((self.end_time - self.start_time).total_seconds() * 1000)
            if self.end_time is not None
            else None
        )

    @property
    def finished(self) -> bool:
        return self.response is not None

    def set_end_time(self) -> None:
        self.end_time = datetime.now()

    def get_collectors(self) -> dict[str, Collector]:
        collectors: dict[str, Collector] = {}

        for attribute_name, attribute_value in self.__dict__.items():
            if isinstance(attribute_value, Collector):
                attribute_value.generate_statistics()
                collectors[attribute_name] = attribute_value

        return collectors

    def get_as_context(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "request_id": self.request_id,
            "django_view": self.django_view,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "response": self.response,
            "finished": self.finished,
            **self.get_collectors(),
        }

    def matches_search_filter(self, search: str) -> bool:
        search = search.lower()
        return (
            search in self.request.path.lower()
            or search in self.django_view.lower()
            or next(
                (
                    True
                    for collector in self.get_collectors().values()
                    if collector.matches_search_filter(search)
                ),
                False,
            )
        )

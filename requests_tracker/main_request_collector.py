from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.http import HttpRequest, HttpResponse
from django.urls import resolve

from requests_tracker.base_collector import Collector
from requests_tracker.sql.sql_collector import SQLCollector


class MainRequestCollector:
    request_id: UUID
    request: HttpRequest
    django_view: str
    start_time: datetime
    end_time: datetime | None
    response: HttpResponse | None = None

    sql_collector: SQLCollector

    def __init__(self, request: HttpRequest):
        self.request_id = uuid4()
        self.request = request
        self.django_view = resolve(self.request.path)._func_path
        self.start_time = datetime.now()
        self.end_time = None

        self.sql_collector = SQLCollector()

    @property
    def duration(self) -> int | None:
        """duration in milliseconds"""
        return (
            int((self.end_time - self.start_time).total_seconds() * 1000)
            if self.end_time is not None
            else None
        )

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

    # def generate_stats(self):
    #     colors = contrasting_color_generator()
    #     trace_colors = defaultdict(lambda: next(colors))
    #     similar_query_groups = defaultdict(list)
    #     duplicate_query_groups = defaultdict(list)
    #
    #     if self.queries:
    #         width_ratio_tally = 0
    #         factor = int(256.0 / (len(self.databases) * 2.5))
    #         for n, db in enumerate(self.databases.values()):
    #             rgb = [0, 0, 0]
    #             color = n % 3
    #             rgb[color] = 256 - n // 3 * factor
    #             nn = color
    #             # XXX: pretty sure this is horrible after so many aliases
    #             while rgb[color] < factor:
    #                 nc = min(256 - rgb[color], 256)
    #                 rgb[color] += nc
    #                 nn += 1
    #                 if nn > 2:
    #                     nn = 0
    #                 rgb[nn] = nc
    #             db.rbg_color = rgb
    #
    #         # the last query recorded for each DB alias
    #         last_by_alias: dict[str, SQLQueryInfo] = {}
    #         for query in self.queries:
    #             alias = query.alias
    #
    #             similar_query_groups[(alias, query.raw_sql)].append(query)
    #             duplicate_query_groups[
    #                 (
    #                     alias,
    #                     (
    #                         query.raw_sql,
    #                         repr(
    #                             (
    #                                 tuple(query.raw_params)
    #                                 if query.raw_params is not None
    #                                 else ()
    #                             )
    #                         ),
    #                     ),
    #                 )
    #             ].append(query)
    #
    #             prev_query = last_by_alias.get(alias, {})
    #             prev_trans_id = prev_query.trans_id
    #
    #             # If two consecutive queries for a given DB alias have different
    #             # transaction ID values, a transaction started, finished, or both, so
    #             # annotate the queries as appropriate.
    #             if query.trans_id != prev_trans_id:
    #                 if prev_trans_id is not None:
    #                     prev_query.ends_trans = True
    #                 if query.trans_id is not None:
    #                     query.stacktrace = True
    #             if query.trans_id is not None:
    #                 query.in_trans = True
    #
    #             if query.iso_level is not None:
    #                 query.iso_level = get_isolation_level_display(
    #                     query.vendor,
    #                     int(query.iso_level),
    #                 )
    #             if query.trans_status is not None:
    #                 query.trans_status = get_transaction_status_display(
    #                     query.vendor,
    #                     int(query.trans_status),
    #                 )
    #
    #             # if query.sql:
    #             #     query.sql = reformat_sql(query.sql, with_toggle=True)
    #             query.rbg_color = self.databases[alias].rbg_color
    #             try:
    #                 query.width_ratio = (query.duration / self.sql_time) * 100
    #             except ZeroDivisionError:
    #                 query.width_ratio = 0
    #             query.start_offset = width_ratio_tally
    #             query.end_offset = query.width_ratio + query.start_offset
    #             width_ratio_tally += query.width_ratio
    #             query["stacktrace"] = render_stacktrace(query["stacktrace"])
    #     #
    #     #         query["trace_color"] = trace_colors[query["stacktrace"]]
    #     #
    #     #         last_by_alias[alias] = query
    #     #
    #     #     # Close out any transactions that were in progress, since there is no
    #     #     # explicit way to know when a transaction finishes.
    #     #     for final_query in last_by_alias.values():
    #     #         if final_query.get("trans_id") is not None:
    #     #             final_query["ends_trans"] = True
    #     #
    #     # group_colors = contrasting_color_generator()
    #     # _process_query_groups(
    #     #     similar_query_groups, self._databases, group_colors, "similar"
    #     # )
    #     # _process_query_groups(
    #     #     duplicate_query_groups, self._databases, group_colors, "duplicate"
    #     # )
    #     #
    #     # self.record_stats(
    #     #     {
    #     #         "databases": sorted(
    #     #             self._databases.items(), key=lambda x: -x[1]["time_spent"]
    #     #         ),
    #     #         "queries": self._queries,
    #     #         "sql_time": self._sql_time,
    #     #     }
    #     # )
    #     #

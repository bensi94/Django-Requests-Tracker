import re
import uuid
from collections import defaultdict

from requests_tracker.base_collector import Collector
from requests_tracker.settings import get_config
from requests_tracker.sql.dataclasses import PerDatabaseInfo, SQLQueryInfo

SimilarQueryGroupsType = dict[tuple[str, str], list[SQLQueryInfo]]
DuplicateQueryGroupsType = dict[tuple[str, tuple[str, str]], list[SQLQueryInfo]]


class SQLCollector(Collector):
    unfiltered_queries: list[SQLQueryInfo]
    databases: dict[str, PerDatabaseInfo]
    sql_time: float
    transaction_ids: dict[str, str | None]

    def __init__(self) -> None:
        self.databases = {}
        self.sql_time = 0
        self.unfiltered_queries = []
        # synthetic transaction IDs, keyed by DB alias
        self.transaction_ids = {}

    @property
    def queries(self) -> list[SQLQueryInfo]:
        config = get_config()
        if ignore_patterns := config.get("IGNORE_SQL_PATTERNS"):
            return [
                query
                for query in self.unfiltered_queries
                if not any(
                    bool(re.match(pattern, query.raw_sql))
                    for pattern in ignore_patterns
                )
            ]

        return self.unfiltered_queries

    @property
    def num_queries(self) -> int:
        return len(self.queries)

    def record(self, sql_query_info: SQLQueryInfo) -> None:
        self.unfiltered_queries.append(sql_query_info)

    def new_transaction_id(self, alias: str) -> str:
        """
        Generate and return a new synthetic transaction ID for the specified DB alias.
        """
        trans_id = uuid.uuid4().hex
        self.transaction_ids[alias] = trans_id
        return trans_id

    def current_transaction_id(self, alias: str) -> str:
        """
        Return the current synthetic transaction ID for the specified DB alias.
        """
        trans_id = self.transaction_ids.get(alias)
        # Sometimes it is not possible to detect the beginning of the first transaction,
        # so current_transaction_id() will be called before new_transaction_id().  In
        # that case there won't yet be a transaction ID. so it is necessary to generate
        # one using new_transaction_id().
        if trans_id is None:
            trans_id = self.new_transaction_id(alias)
        return trans_id

    def generate_statistics(self) -> None:
        similar_query_groups: SimilarQueryGroupsType = defaultdict(list)
        duplicate_query_groups: DuplicateQueryGroupsType = defaultdict(list)

        self.databases = {}
        self.sql_time = 0

        for query in self.queries:
            alias = query.alias
            if alias not in self.databases:
                self.databases[alias] = PerDatabaseInfo(
                    time_spent=query.duration,
                    num_queries=1,
                )
            else:
                self.databases[alias].time_spent += query.duration
                self.databases[alias].num_queries += 1
            self.sql_time += query.duration

            similar_query_groups[(query.alias, query.sql)].append(query)
            duplicate_query_groups[
                (
                    query.alias,
                    (
                        query.raw_sql,
                        repr(tuple(query.raw_params) if query.raw_params else ()),
                    ),
                )
            ].append(query)

        similar_counts: dict[str, int] = defaultdict(int)
        for (alias, _), query_group in similar_query_groups.items():
            count = len(query_group)

            if count > 1:
                for query in query_group:
                    query.similar_count = count
                similar_counts[alias] += count

        duplicate_counts: dict[str, int] = defaultdict(int)
        for (alias, _), query_group in duplicate_query_groups.items():
            count = len(query_group)

            if count > 1:
                for query in query_group:
                    query.duplicate_count = count
                duplicate_counts[alias] += count

        for alias in self.databases:
            self.databases[alias].similar_count = similar_counts[alias]
            self.databases[alias].duplicate_count = duplicate_counts[alias]

    @property
    def total_similar_queries(self) -> int:
        return sum(database.similar_count for database in self.databases.values())

    @property
    def total_duplicate_queries(self) -> int:
        return sum(database.duplicate_count for database in self.databases.values())

    def matches_search_filter(self, search: str) -> bool:
        search = search.lower()
        return next(
            (True for query in self.queries if search in query.raw_sql.lower()),
            False,
        )

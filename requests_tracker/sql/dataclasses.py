from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from requests_tracker.sql.sql_tracker import ExecuteParametersOrSequence
    from requests_tracker.stack_trace import StackTrace


@dataclass
class PerDatabaseInfo:
    time_spent: float
    num_queries: int
    similar_count: int = 0
    duplicate_count: int = 0


@dataclass
class SQLQueryInfo:
    vendor: str
    alias: str
    sql: str
    duration: float
    raw_sql: str
    params: str
    raw_params: "ExecuteParametersOrSequence"
    stacktrace: "StackTrace"
    start_time: float
    stop_time: float
    is_slow: bool
    is_select: bool
    trans_id: Optional[str] = None
    iso_level: Optional[Union[int, str]] = None
    trans_status: Optional[int] = None
    similar_count: int = 0
    duplicate_count: int = 0

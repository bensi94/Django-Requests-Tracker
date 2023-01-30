from typing import Any, Sequence

from requests_tracker.sql.sql_tracker import ExecuteParameters, SQLTracker


def install_sql_hook() -> None:
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.backends.utils import CursorWrapper

    real_execute = CursorWrapper.execute
    real_executemany = CursorWrapper.executemany
    real_call_proc = CursorWrapper.callproc
    real_connect = BaseDatabaseWrapper.connect

    def execute(self: CursorWrapper, sql: str, params: ExecuteParameters = None) -> Any:
        sql_tracker = SQLTracker.current
        sql_tracker.record(
            method=real_execute,
            cursor_self=self,
            sql=sql,
            params=params,
        )

    def executemany(
        self: CursorWrapper,
        sql: str,
        param_list: Sequence[ExecuteParameters],
    ) -> Any:
        sql_tracker = SQLTracker.current
        sql_tracker.record(
            method=real_executemany,
            cursor_self=self,
            sql=sql,
            params=param_list,
            many=True,
        )

    def callproc(
        self: CursorWrapper,
        procname: str,
        params: ExecuteParameters = None,
    ) -> Any:
        sql_tracker = SQLTracker.current
        sql_tracker.record(
            method=real_call_proc,
            cursor_self=self,
            sql=procname,
            params=params,
        )

    def connect(self: BaseDatabaseWrapper) -> Any:
        real_connect(self)
        sql_tracker = SQLTracker.current
        sql_tracker.set_database_wrapper(self)

    CursorWrapper.execute = execute  # type: ignore
    CursorWrapper.executemany = executemany  # type: ignore
    CursorWrapper.callproc = callproc  # type: ignore
    BaseDatabaseWrapper.connect = connect  # type: ignore

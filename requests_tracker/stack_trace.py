import inspect
import linecache
from types import FrameType
from typing import Any, Generator

from asgiref.local import Local

from requests_tracker import settings

_local_data = Local()

# each tuple is: filename, line_no, func_name, source_line, frame_locals
StackTrace = list[tuple[str, int, str, str, dict[str, Any] | None]]


def _stack_frames(*, skip: int = 0) -> Generator[FrameType, None, None]:
    skip += 1  # Skip the frame for this generator.
    frame = inspect.currentframe()
    while frame is not None:
        if skip > 0:
            skip -= 1
        else:
            yield frame
        frame = frame.f_back


def _is_excluded_frame(frame: FrameType, excluded_modules: list[str] | None) -> bool:
    if not excluded_modules:
        return False
    frame_module = frame.f_globals.get("__name__")
    return (
        any(
            frame_module == excluded_module
            or frame_module.startswith(f"{excluded_module}.")
            for excluded_module in excluded_modules
        )
        if isinstance(frame_module, str)
        else False
    )


def get_stack_trace(*, skip: int = 0) -> StackTrace:
    """
    Return a processed stack trace for the current call stack.
    If the ``ENABLE_STACKTRACES`` setting is False, return an empty :class:`list`.
    Otherwise return a :class:`list` of processed stack frame tuples (file name, line
    number, function name, source line, frame locals) for the current call stack.  The
    first entry in the list will be for the bottom of the stack and the last entry will
    be for the top of the stack.
    ``skip`` is an :class:`int` indicating the number of stack frames above the frame
    for this function to omit from the stack trace.  The default value of ``0`` means
    that the entry for the caller of this function will be the last entry in the
    returned stack trace.
    """
    config = settings.get_config()
    if not config["ENABLE_STACKTRACES"]:
        return []
    skip += 1  # Skip the frame for this function.
    stack_trace_recorder = getattr(_local_data, "stack_trace_recorder", None)
    if stack_trace_recorder is None:
        stack_trace_recorder = _StackTraceRecorder()
        _local_data.stack_trace_recorder = stack_trace_recorder
    return stack_trace_recorder.get_stack_trace(
        excluded_modules=config["HIDE_IN_STACKTRACES"],
        include_locals=config["ENABLE_STACKTRACES_LOCALS"],
        skip=skip,
    )


class _StackTraceRecorder:
    def __init__(self) -> None:
        self.filename_cache: dict[str, tuple[str, bool]] = {}

    def get_source_file(self, frame: FrameType) -> tuple[str, bool]:
        frame_filename = frame.f_code.co_filename

        value = self.filename_cache.get(frame_filename)
        if value is None:
            filename = inspect.getsourcefile(frame)
            if filename is None:
                is_source = False
                filename = frame_filename
            else:
                is_source = True
                # Ensure linecache validity the first time this recorder
                # encounters the filename in this frame.
                linecache.checkcache(filename)
            value = (filename, is_source)
            self.filename_cache[frame_filename] = value

        return value

    def get_stack_trace(
        self,
        *,
        excluded_modules: list[str] | None = None,
        include_locals: bool = False,
        skip: int = 0,
    ) -> StackTrace:
        trace = []
        skip += 1  # Skip the frame for this method.
        for frame in _stack_frames(skip=skip):
            if _is_excluded_frame(frame, excluded_modules):
                continue

            filename, is_source = self.get_source_file(frame)

            line_no = frame.f_lineno
            func_name = frame.f_code.co_name

            if is_source:
                module = inspect.getmodule(frame, filename)
                module_globals = module.__dict__ if module is not None else None
                source_line = linecache.getline(
                    filename, line_no, module_globals
                ).strip()
            else:
                source_line = ""

            frame_locals = frame.f_locals if include_locals else None

            trace.append((filename, line_no, func_name, source_line, frame_locals))
        trace.reverse()
        return trace

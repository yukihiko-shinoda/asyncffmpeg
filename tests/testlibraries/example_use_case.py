"""The example use case of FFmpegCoroutine for E2E testing in case of interrupt."""

from __future__ import annotations

from logging import LogRecord
from logging import getLogger
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

from asynccpu import ProcessTaskPoolExecutor

from asyncffmpeg import FFmpegCoroutineFactory
from tests.testlibraries.create_stream_spec_croutine import CreateStreamSpecCoroutineFilter
from tests.testlibraries.keyboardinterrupter.local_socket import LocalSocket

if TYPE_CHECKING:
    import queue
    from pathlib import Path


async def example_use_case_interrupt(
    path_file_input: str,
    path_file_output: str,
    queue_log_record: queue.Queue[LogRecord],
    configurer: Callable[[], Any],
) -> None:
    """The example use case of FFmpegCroutine for E2E testing in case of interrupt."""
    logger = getLogger(__name__)
    logger.info("Example use case interrupt start")
    with ProcessTaskPoolExecutor(
        max_workers=3,
        cancel_tasks_when_shutdown=True,
        queue=queue_log_record,
        configurer=configurer,
    ) as executor:
        ffmpeg_coroutine = FFmpegCoroutineFactory.create()
        coroutine_create_stream_spec_filter = CreateStreamSpecCoroutineFilter(path_file_input, path_file_output)
        future: Any = executor.create_process_task(
            ffmpeg_coroutine.execute,
            coroutine_create_stream_spec_filter.create,
        )
        await future
        msg = "Failed"
        raise Exception(msg)  # noqa: TRY002  # pylint: disable=broad-exception-raised


async def example_use_case(path_file_input: Path, path_file_output: Path) -> None:
    """The example use case of FFmpegCroutine for E2E testing in case of interrupt."""
    with ProcessTaskPoolExecutor(max_workers=1, cancel_tasks_when_shutdown=True) as executor:
        task: Any = executor.create_process_task(
            FFmpegCoroutineFactory.create().execute,
            CreateStreamSpecCoroutineFilter(path_file_input, path_file_output).create,
        )
        LocalSocket.send("Ready")
        await task

"""The example use case of FFmpegCroutine for E2E testing in case of interrupt."""
from logging import getLogger

from asynccpu import ProcessTaskPoolExecutor

from asyncffmpeg import FFmpegCoroutineFactory
from tests.testlibraries.create_stream_spec_croutine import CreateStreamSpecCoroutineFilter
from tests.testlibraries.keyboardinterrupter.local_socket import LocalSocket


async def example_use_case_interrupt(path_file_input, path_file_output, queue, configurer) -> None:
    """The example use case of FFmpegCroutine for E2E testing in case of interrupt."""
    logger = getLogger(__name__)
    logger.info("Example use case interrupt start")
    with ProcessTaskPoolExecutor(
        max_workers=3, cancel_tasks_when_shutdown=True, queue=queue, configurer=configurer
    ) as executor:
        ffmpeg_coroutine = FFmpegCoroutineFactory.create()
        coroutine_create_stream_spec_filter = CreateStreamSpecCoroutineFilter(path_file_input, path_file_output)
        future = executor.create_process_task(ffmpeg_coroutine.execute, coroutine_create_stream_spec_filter.create)
        await future
        raise Exception("Failed")


async def example_use_case(path_file_input, path_file_output):
    """The example use case of FFmpegCroutine for E2E testing in case of interrupt."""
    with ProcessTaskPoolExecutor(max_workers=1, cancel_tasks_when_shutdown=True) as executor:
        task = executor.create_process_task(
            FFmpegCoroutineFactory.create().execute,
            CreateStreamSpecCoroutineFilter(path_file_input, path_file_output).create,
        )
        LocalSocket.send("Ready")
        await task

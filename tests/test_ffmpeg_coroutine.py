"""Tests for FFmpegCoroutine."""
import asyncio
import os
import shutil
import signal
import sys
from concurrent.futures.process import BrokenProcessPool
from logging import DEBUG
from pathlib import Path
from subprocess import Popen
from typing import Dict

import psutil
import pytest
from asynccpu import ProcessTaskPoolExecutor

from asyncffmpeg.exceptions import FFmpegProcessError
from asyncffmpeg.ffmpeg_coroutine_factory import FFmpegCoroutineFactory
from tests.testlibraries import SECOND_SLEEP_FOR_TEST_SHORT
from tests.testlibraries.create_stream_spec_croutine import (
    CreateStreamSpecCoroutineCopy,
    CreateStreamSpecCoroutineFilter,
)
from tests.testlibraries.keyboardinterrupter.local_socket import LocalSocket
from tests.testlibraries.process_pool_executor_simulator import ProcessPoolExecutorSimulator


class StabAfterStart:
    def __init__(self):
        self.is_covered_after_start = False

    async def after_start(self, _ffmpeg_process):
        self.is_covered_after_start = True


class TestFFmpegCoroutine:
    """Tests for FFmpegCoroutine."""

    @staticmethod
    def test_copy(path_file_input, path_file_output):
        """
        The output file should exist.
        Stab method of after start should be called.
        """
        stab_after_start = StabAfterStart()
        coroutine_create_stream_spec_copy = CreateStreamSpecCoroutineCopy(path_file_input, path_file_output)
        ffmpeg_croutine = FFmpegCoroutineFactory.create().execute(
            coroutine_create_stream_spec_copy.create, after_start=stab_after_start.after_start,
        )
        asyncio.run(ffmpeg_croutine)
        assert path_file_output.exists()
        assert stab_after_start.is_covered_after_start

    @staticmethod
    def test_filter(path_file_input, path_file_output):
        coroutine_create_stream_spec_filter = CreateStreamSpecCoroutineFilter(path_file_input, path_file_output)
        asyncio.run(FFmpegCoroutineFactory.create().execute(coroutine_create_stream_spec_filter.create))
        assert path_file_output.exists()
        assert 300000 <= path_file_output.stat().st_size <= 400000

    @staticmethod
    def test_excecption(path_file_input, path_file_output):
        """FFmpegProcessError should be raised when output path already exists and set -n option."""
        shutil.copy(path_file_input, path_file_output)
        coroutine_create_stream_spec_copy = CreateStreamSpecCoroutineCopy(path_file_input, path_file_output)
        with pytest.raises(FFmpegProcessError, match=r"File .* already exists. Exiting\.") as excinfo:
            asyncio.run(FFmpegCoroutineFactory.create().execute(coroutine_create_stream_spec_copy.create))
        assert excinfo.value.exit_code == 1

    # Since Python can't trap signal.SIGINT in Windows.
    # see:
    #     - Windows: signal doc should state certains signals can't be registered
    #     https://bugs.python.org/issue26350
    @pytest.mark.skipif(sys.platform == "win32", reason="test for Linux only")
    def test_keyboard_interrupt(self, path_file_input, path_file_output, caplog, caplog_workaround):
        caplog.set_level(DEBUG, logger="asynccpu.process_task_pool_executor")
        with caplog_workaround():
            asyncio.run(self.keyboard_interrupt_sigint(path_file_input, path_file_output))
        assert "FFmpeg process quit finish" in caplog.text

    @classmethod
    async def keyboard_interrupt_sigint(cls, path_file_input, path_file_output) -> None:
        """Simulates keyboard interrupt by SIGINT."""
        with ProcessTaskPoolExecutor(max_workers=1, cancel_tasks_when_shutdown=True) as executor:
            task = executor.create_process_task(
                FFmpegCoroutineFactory.create().execute,
                CreateStreamSpecCoroutineFilter(path_file_input, path_file_output).create,
            )
            await asyncio.sleep(SECOND_SLEEP_FOR_TEST_SHORT)
            cls.terminate_child_process()
            with pytest.raises(BrokenProcessPool):
                await task
            assert task.done()
        assert not task.cancelled()
        assert isinstance(task.exception(), BrokenProcessPool)
        with pytest.raises(BrokenProcessPool):
            assert task.result()

    # Since coverage.py can't trace asyncio.ProcessPoolExecutor.
    # see: https://github.com/nedbat/coveragepy/issues/481
    @pytest.mark.skipif(sys.platform == "win32", reason="test for Linux only")
    def test_keyboard_interrupt_for_coverage(self, path_file_input, path_file_output, caplog, caplog_workaround):
        with caplog_workaround():
            asyncio.run(self.keyboard_interrupt_sigint_for_coverage(path_file_input, path_file_output))
        assert "FFmpeg process quit finish" in caplog.text

    @classmethod
    async def keyboard_interrupt_sigint_for_coverage(cls, path_file_input, path_file_output) -> None:
        """Simulates keyboard interrupt by SIGINT."""
        process_pool_executor_simulator = ProcessPoolExecutorSimulator(
            FFmpegCoroutineFactory.create().execute,
            CreateStreamSpecCoroutineFilter(path_file_input, path_file_output).create,
        )
        process_pool_executor_simulator.process.start()
        await asyncio.sleep(SECOND_SLEEP_FOR_TEST_SHORT)
        cls.terminate_child_process()
        process_pool_executor_simulator.process.join()

    @staticmethod
    def terminate_child_process():
        current_process = psutil.Process(os.getpid())
        child_processes = current_process.children()
        for child_process in child_processes:
            child_process.send_signal(signal.SIGINT)

    @staticmethod
    @pytest.mark.skipif(sys.platform != "win32", reason="test for Windows only")
    def test_keyboard_interrupt_ctrl_c_new_window(path_file_input, path_file_output) -> None:
        """
        see:
          - Answer: Sending ^C to Python subprocess objects on Windows
            https://stackoverflow.com/a/7980368/12721873
        """
        env: Dict[str, str] = {}
        env.update(os.environ)
        pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(Path(__file__).parent.parent) + (
            "" if pythonpath is None else (os.pathsep + pythonpath)
        )
        command = f"start {sys.executable} tests\\testlibraries\\subprocess_wrapper_windows.py"
        popen = Popen(command, shell=True, env=env)
        LocalSocket.send(str(path_file_input))
        assert LocalSocket.receive() == "Next"
        LocalSocket.send(str(path_file_output))
        assert LocalSocket.receive() == "Test succeed"
        assert popen.wait() == 0

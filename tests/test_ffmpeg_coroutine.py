"""Tests for FFmpegCoroutine."""
import asyncio
import os
import shutil
import signal
import sys
import time
from logging import DEBUG
from multiprocessing.context import Process
from pathlib import Path
from subprocess import Popen
from typing import Callable, ContextManager, Dict, List

import psutil
import pytest
from pytest import LogCaptureFixture

from asyncffmpeg import FFmpegCoroutineFactory, FFmpegProcessError
from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess
from tests.testlibraries import SECOND_SLEEP_FOR_TEST_KEYBOARD_INTERRUPT_CTRL_C_POSIX, SECOND_SLEEP_FOR_TEST_LONG
from tests.testlibraries.create_stream_spec_croutine import (
    CreateStreamSpecCoroutineCopy,
    CreateStreamSpecCoroutineFilter,
)
from tests.testlibraries.example_use_case import example_use_case
from tests.testlibraries.keyboardinterrupter.local_socket import LocalSocket
from tests.testlibraries.process_pool_executor_simulator import ProcessPoolExecutorSimulator


class StabAfterStart:
    def __init__(self) -> None:
        self.is_covered_after_start = False

    async def after_start(self, _ffmpeg_process: FFmpegProcess) -> None:
        self.is_covered_after_start = True


class TestFFmpegCoroutine:
    """Tests for FFmpegCoroutine."""

    @staticmethod
    def test_copy(path_file_input: Path, path_file_output: Path) -> None:
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
    def test_filter(path_file_input: Path, path_file_output: Path) -> None:
        coroutine_create_stream_spec_filter = CreateStreamSpecCoroutineFilter(path_file_input, path_file_output)
        asyncio.run(FFmpegCoroutineFactory.create().execute(coroutine_create_stream_spec_filter.create))
        assert path_file_output.exists()
        assert 300000 <= path_file_output.stat().st_size <= 400000

    @staticmethod
    def test_excecption(path_file_input: Path, path_file_output: Path) -> None:
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
    def test_keyboard_interrupt(
        self,
        path_file_input: Path,
        path_file_output: Path,
        caplog: LogCaptureFixture,
        caplog_workaround: Callable[[], ContextManager[None]],
    ) -> None:
        """FFmpeg coroutine should quit when CTRL + C in POSIX."""
        caplog.set_level(DEBUG, logger="asynccpu.process_task_pool_executor")
        with caplog_workaround():
            self.keyboard_interrupt(path_file_input, path_file_output)
        assert "FFmpeg process quit finish" in caplog.text

    @classmethod
    def keyboard_interrupt(cls, path_file_input: Path, path_file_output: Path) -> None:
        """Test process of keyboard interrupt."""
        process = Process(target=cls.report_raises_keyboard_interrupt, args=(path_file_input, path_file_output))
        process.start()
        assert LocalSocket.receive() == "Ready"
        time.sleep(SECOND_SLEEP_FOR_TEST_KEYBOARD_INTERRUPT_CTRL_C_POSIX)
        cls.simulate_ctrl_c_in_posix(process)
        assert LocalSocket.receive() == "Test succeed"
        psutil_process = psutil.Process(process.pid)
        assert psutil_process.wait() == 0
        # Reason: Requires to enhance types-psutil
        assert not psutil_process.is_running()  # type: ignore

    @staticmethod
    def report_raises_keyboard_interrupt(path_file_input: Path, path_file_output: Path) -> None:
        with pytest.raises(KeyboardInterrupt):
            asyncio.run(example_use_case(path_file_input, path_file_output))
        LocalSocket.send("Test succeed")

    # Since coverage.py can't trace asyncio.ProcessPoolExecutor.
    # see: https://github.com/nedbat/coveragepy/issues/481
    @pytest.mark.skipif(sys.platform == "win32", reason="test for Linux only")
    def test_keyboard_interrupt_for_coverage(
        self,
        path_file_input: Path,
        path_file_output: Path,
        caplog: LogCaptureFixture,
        caplog_workaround: Callable[[], ContextManager[None]],
    ) -> None:
        """FFmpeg process should triger FFmpeg quit."""
        with caplog_workaround():
            asyncio.run(self.keyboard_interrupt_sigint_for_coverage(path_file_input, path_file_output))
        assert "FFmpeg process quit finish" in caplog.text

    @classmethod
    async def keyboard_interrupt_sigint_for_coverage(cls, path_file_input: Path, path_file_output: Path) -> None:
        """Simulates keyboard interrupt by SIGINT."""
        process_pool_executor_simulator = ProcessPoolExecutorSimulator(
            FFmpegCoroutineFactory.create().execute,
            CreateStreamSpecCoroutineFilter(path_file_input, path_file_output).create,
        )
        process_pool_executor_simulator.process.start()
        await asyncio.sleep(SECOND_SLEEP_FOR_TEST_LONG)
        cls.simulate_ctrl_c_in_posix(process_pool_executor_simulator.process)
        # psutil.Process(process_pool_executor_simulator.process.pid).send_signal(signal.SIGINT)
        process_pool_executor_simulator.process.join()

    @staticmethod
    def simulate_ctrl_c_in_posix(process: Process) -> None:
        """
        see:
          - python - Handling keyboard interrupt when using subproccess - Stack Overflow
            https://stackoverflow.com/a/23839524/12721873
          - Answer: c++ - Child process receives parent's SIGINT - Stack Overflow
            https://stackoverflow.com/a/6804155/12721873
        """
        psutil_process = psutil.Process(process.pid)
        child_processes: List[psutil.Process] = psutil_process.children(recursive=True)
        child_processes.append(psutil_process)
        for child_process in child_processes:
            child_process.send_signal(signal.SIGINT)

    @staticmethod
    @pytest.mark.skipif(sys.platform != "win32", reason="test for Windows only")
    def test_keyboard_interrupt_ctrl_c_new_window(path_file_input: Path, path_file_output: Path) -> None:
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
        with Popen(command, shell=True, env=env) as popen:
            LocalSocket.send(str(path_file_input))
            assert LocalSocket.receive() == "Next"
            LocalSocket.send(str(path_file_output))
            assert LocalSocket.receive() == "Test succeed"
            assert popen.wait() == 0

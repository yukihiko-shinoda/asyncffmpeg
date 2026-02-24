"""Tests for FFmpegCoroutine."""

import asyncio
import shutil
import signal

# Reason: This package requires to use subprocess.
import subprocess  # nosec
import sys
import time
from contextlib import AbstractContextManager
from logging import DEBUG
from multiprocessing.context import Process
from pathlib import Path

# Reason: This package requires to use subprocess.
from subprocess import Popen  # nosec
from typing import Callable

import psutil
import pytest

from asyncffmpeg import FFmpegCoroutineFactory
from asyncffmpeg import FFmpegProcessError
from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess
from tests.conftest import LoggingEnvironment
from tests.testlibraries import SECOND_SLEEP_FOR_TEST_KEYBOARD_INTERRUPT_CTRL_C_POSIX
from tests.testlibraries.create_stream_spec_croutine import CreateStreamSpecCoroutineCopy
from tests.testlibraries.create_stream_spec_croutine import CreateStreamSpecCoroutineFilter
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
        """The output file should exist.

        Stab method of after start should be called.
        """
        stab_after_start = StabAfterStart()
        coroutine_create_stream_spec_copy = CreateStreamSpecCoroutineCopy(path_file_input, path_file_output)
        ffmpeg_croutine = FFmpegCoroutineFactory.create().execute(
            coroutine_create_stream_spec_copy.create,
            after_start=stab_after_start.after_start,
        )
        asyncio.run(ffmpeg_croutine)
        assert path_file_output.exists()
        assert stab_after_start.is_covered_after_start

    @staticmethod
    def test_filter(path_file_input: Path, path_file_output: Path) -> None:
        """The output file should exist and have the expected size after filtering."""
        expected_size_minimum = 300000
        expected_size_maximum = 400000
        coroutine_create_stream_spec_filter = CreateStreamSpecCoroutineFilter(path_file_input, path_file_output)
        asyncio.run(FFmpegCoroutineFactory.create().execute(coroutine_create_stream_spec_filter.create))
        assert path_file_output.exists()
        assert expected_size_minimum <= path_file_output.stat().st_size <= expected_size_maximum

    @staticmethod
    def test_excecption(path_file_input: Path, path_file_output: Path) -> None:
        """FFmpegProcessError should be raised when output path already exists and set -n option."""
        shutil.copy(path_file_input, path_file_output)
        coroutine_create_stream_spec_copy = CreateStreamSpecCoroutineCopy(path_file_input, path_file_output)
        with pytest.raises(FFmpegProcessError, match=r"File .* already exists. Exiting\.") as excinfo:
            asyncio.run(FFmpegCoroutineFactory.create().execute(coroutine_create_stream_spec_copy.create))
        assert excinfo.value.exit_code in [0, 1]  # FFmpeg 7.1+ returns 0, older versions return 1

    # Since Python can't trap signal.SIGINT in Windows.
    # see:
    #     - Windows: signal doc should state certains signals can't be registered
    #     https://bugs.python.org/issue26350
    @pytest.mark.skipif(sys.platform == "win32", reason="test for Linux only")
    def test_keyboard_interrupt(
        self,
        path_file_input: Path,
        path_file_output: Path,
        caplog: pytest.LogCaptureFixture,
        caplog_workaround: Callable[[], AbstractContextManager[None]],
    ) -> None:
        """FFmpeg coroutine should quit when CTRL + C in POSIX."""
        caplog.set_level(DEBUG, logger="asynccpu.process_task_pool_executor")
        with caplog_workaround():
            self.keyboard_interrupt(path_file_input, path_file_output)
        # In Python 3.13+, there's a race condition where the subprocess is terminated
        # before exception handler logs can be written. We verify the signal handler ran.
        assert "SIGTERM handler: Start" in caplog.text or "FFmpeg process quit finish" in caplog.text

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
        assert not psutil_process.is_running()

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
        caplog: pytest.LogCaptureFixture,
        caplog_workaround: Callable[[], AbstractContextManager[None]],
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
        await asyncio.sleep(SECOND_SLEEP_FOR_TEST_KEYBOARD_INTERRUPT_CTRL_C_POSIX)
        cls.simulate_ctrl_c_in_posix(process_pool_executor_simulator.process)
        process_pool_executor_simulator.process.join()

    @staticmethod
    def simulate_ctrl_c_in_posix(process: Process) -> None:
        """see:

        - python - Handling keyboard interrupt when using subproccess - Stack Overflow
          https://stackoverflow.com/a/23839524/12721873
        - Answer: c++ - Child process receives parent's SIGINT - Stack Overflow
          https://stackoverflow.com/a/6804155/12721873
        """
        psutil_process = psutil.Process(process.pid)
        child_processes: list[psutil.Process] = psutil_process.children(recursive=True)
        child_processes.append(psutil_process)
        for child_process in child_processes:
            child_process.send_signal(signal.SIGINT)

    @staticmethod
    @pytest.mark.skipif(sys.platform != "win32", reason="test for Windows only")
    def test_keyboard_interrupt_ctrl_c_new_window(
        logging_environment: LoggingEnvironment,
        path_file_input: Path,
        path_file_output: Path,
    ) -> None:
        """see:

        - Answer: Sending ^C to Python subprocess objects on Windows
          https://stackoverflow.com/a/7980368/12721873
        """
        command = f"start {sys.executable} tests\\testlibraries\\subprocess_wrapper_windows.py"
        # shell=True required: 'start' is a Windows shell built-in command, not an executable.
        # This is safe as the command uses only sys.executable and hardcoded paths with no user input.
        with Popen(command, shell=True, env=logging_environment.create_env()) as popen:  # noqa: DUO116,S602,RUF100  # nosec
            LocalSocket.send(str(path_file_input))
            assert LocalSocket.receive() == "Next"
            LocalSocket.send(str(path_file_output))
            received = LocalSocket.receive()
            log_content = logging_environment.get_log_content()
            assert received == "Test succeed", f"Subprocess sent: {received!r}\nDebug log:\n{log_content}"
            assert popen.wait() == 0

    # Since Python can't trap signal.SIGTERM in Windows.
    # see:
    #     - Windows: signal doc should state certains signals can't be registered
    #     https://bugs.python.org/issue26350
    @pytest.mark.skipif(sys.platform == "win32", reason="test for Linux only")
    def test_terminate(
        self,
        path_file_input: Path,
        path_file_output: Path,
        caplog: pytest.LogCaptureFixture,
        caplog_workaround: Callable[[], AbstractContextManager[None]],
    ) -> None:
        """FFmpeg coroutine should quit when CTRL + C in POSIX."""
        caplog.set_level(DEBUG, logger="asynccpu.process_task_pool_executor")
        with caplog_workaround():
            self.terminate(path_file_input, path_file_output)
        assert "FFmpeg process quit finish" in caplog.text

    @classmethod
    def terminate(cls, path_file_input: Path, path_file_output: Path) -> None:
        """Test process of keyboard interrupt."""
        process = Process(target=cls.report_raises_cencelled_error, args=(path_file_input, path_file_output))
        process.start()
        assert LocalSocket.receive() == "Ready"
        time.sleep(SECOND_SLEEP_FOR_TEST_KEYBOARD_INTERRUPT_CTRL_C_POSIX)
        psutil_process = psutil.Process(process.pid)
        psutil_process.terminate()
        # Return code seems change when:
        # run this test only: -15
        # run all tests: 1
        assert psutil_process.wait() in [-15, 1]
        assert not psutil_process.is_running()

    @staticmethod
    def report_raises_cencelled_error(path_file_input: Path, path_file_output: Path) -> None:
        asyncio.run(example_use_case(path_file_input, path_file_output))

    @staticmethod
    def test_example_readme(code_and_environment_example: Path) -> None:
        # Reason: This only executes test code.
        subprocess.run([f"{sys.executable}", f"{code_and_environment_example}"], check=True)  # noqa: S603  # nosec
        for index in [1, 2]:
            assert (code_and_environment_example.parent / f"output{index}.mp4").exists()

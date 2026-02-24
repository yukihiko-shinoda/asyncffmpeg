"""The code to run in dedicated process group for Windows.

There are 2 purposes:

- to prevent Ctrl + C event propagation to subprocess (raw FFmpeg execution)
- to prevent effect of setting ConsoleCtrlHandler to parent process (FFmpeg coroutine)

Process group topology::

    subprocess_wrapper_windows.py  (Console group A)
    ├── Manager process             (Console group A)
    ├── Worker process 1            (Console group A)
    │   └── windows.py subprocess  (NEW process group — CREATE_NEW_PROCESS_GROUP)
    │       └── FFmpeg              (new process group, no CTRL_C_EVENT from group A)
    ├── Worker process 2            (Console group A)
    └── Worker process 3            (Console group A)

When ``os.kill(0, CTRL_C_EVENT)`` is called from subprocess_wrapper_windows.py,
all processes in Console group A receive the event.
windows.py is excluded — CREATE_NEW_PROCESS_GROUP explicitly disables CTRL_C
propagation into the new group, so windows.py keeps running FFmpeg normally.

To stop FFmpeg gracefully, ``FFmpegProcessWindowsWrapper.quit()`` explicitly sends
``CTRL_C_EVENT`` to windows.py's process group (group ID == windows.py's PID) via
``os.kill(self.popen.pid, signal.CTRL_C_EVENT)``.  This triggers windows.py's
``SetConsoleCtrlHandler`` callback and also reaches FFmpeg directly (same group),
causing a graceful shutdown that includes the final muxing-overhead summary line.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

# Reason: This package requires to use subprocess.
# Reason: CREATE_NEW_PROCESS_GROUP is packaged only in Windows
from subprocess import CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]  # nosec
from subprocess import PIPE  # nosec
from subprocess import Popen  # nosec
from subprocess import TimeoutExpired  # nosec

import ffmpeg

from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess


class FFmpegProcessWindowsWrapper(FFmpegProcess):
    """FFmpeg process wrapping Popen object."""

    def create_popen(self) -> Popen[bytes]:
        argument = [
            sys.executable,
            str(Path(__file__).resolve().parent / "windows.py"),
            str(self.time_to_force_termination),
            *ffmpeg.get_args(self.stream_spec),
        ]
        self.logger.debug(argument)
        # Reason:
        #   consider-using-with: This method is instead of ffmpeg.run_async(). pylint: disable=consider-using-with
        #   S603: Imput is limited enough.
        return Popen(argument, creationflags=CREATE_NEW_PROCESS_GROUP, stdout=PIPE, stderr=PIPE)  # noqa: S603  # nosec

    async def quit(self, time_to_force_termination: float | None = None) -> None:
        """Quits the Windows FFmpeg wrapper process.

        Overrides the base class to skip sending the 'q' key via communicate(), because FFmpeg runs inside a child
        Python process launched with CREATE_NEW_PROCESS_GROUP. The communicate()-based graceful shutdown does not work
        reliably across that process boundary.

        Instead, this implementation waits for the child process to finish (suppressing TimeoutExpired), terminates it,
        then drains remaining stdout/stderr from the StringRealtimePipeReader.
        """
        time_to_force_termination = self.get_time_to_force_termination(time_to_force_termination)
        with contextlib.suppress(TimeoutExpired):
            self.popen.wait(time_to_force_termination)
        self.popen.terminate()
        stdout, _return_code = await self.live_popen.wait()
        self.logger.info(stdout)

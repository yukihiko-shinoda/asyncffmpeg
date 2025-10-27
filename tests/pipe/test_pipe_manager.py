"""Test for asyncffmpeg.pipe.pipe_manager."""

from __future__ import annotations

import io
import time

# Reason: This package requires to use subprocess.
from threading import Event

from asyncffmpeg.pipe.pipe_manager import BytesPipeManager
from asyncffmpeg.pipe.pipe_manager import StringPipeManager


class SlowReader(io.BytesIO):
    """BytesIO that reads slowly to allow event checking."""

    def read(self, size: int | None = -1) -> bytes:
        # Sleep a tiny bit to allow event.is_set() to be checked
        time.sleep(0.001)
        return super().read(size)


class SlowLineReader(io.BytesIO):
    """BytesIO that reads lines slowly to allow event checking."""

    def readline(self, size: int | None = -1) -> bytes:
        # Sleep a tiny bit to allow event.is_set() to be checked
        time.sleep(0.001)
        return super().readline(size)


class TestBytesPipeManager:
    """Tests for BytesPipeManager."""

    def test_log_complete_read(self) -> None:
        """Test that BytesPipeManager reads bytes until empty."""
        # Create slow reader with test data
        data = b"test data here"
        pipe = SlowReader(data)
        event = Event()

        # Create the manager (it will start the thread)
        manager = BytesPipeManager(event, pipe, frame_bytes=4)

        # Give thread time to read all data
        time.sleep(0.1)

        # Set event and join thread
        event.set()
        manager.thread.join(timeout=1.0)

        # Should have read the data
        result = manager.read()
        assert isinstance(result, list)
        assert len(result) > 0
        # Verify data was read
        combined = b"".join(result)
        assert combined == b"test data here"

    def test_log_with_event_set_early(self) -> None:
        """Test that BytesPipeManager stops when event is set."""
        # Create slow reader with lots of data
        data = b"x" * 1000
        pipe = SlowReader(data)
        event = Event()

        # Create the manager
        manager = BytesPipeManager(event, pipe, frame_bytes=1)

        # Immediately set event to test early termination path
        time.sleep(0.01)
        event.set()
        manager.thread.join(timeout=1.0)

        # Result should be list (may be empty or partially filled)
        result = manager.read()
        assert isinstance(result, list)


class TestStringPipeManager:
    """Tests for StringPipeManager."""

    def test_log_complete_read(self) -> None:
        """Test that StringPipeManager reads lines until empty."""
        # Create slow line reader with test data
        data = b"line1\nline2\nline3\n"
        pipe = SlowLineReader(data)
        event = Event()

        # Create the manager
        manager = StringPipeManager(event, pipe)

        # Give thread time to read all data
        time.sleep(0.1)

        # Set event and join thread
        event.set()
        manager.thread.join(timeout=1.0)

        # Should have read all lines
        result = manager.read()
        assert isinstance(result, str)
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    def test_log_with_event_set_early(self) -> None:
        """Test that StringPipeManager stops when event is set."""
        # Create slow line reader with many lines
        lines = "".join([f"line{i}\n" for i in range(100)])
        pipe = SlowLineReader(lines.encode())
        event = Event()

        # Create the manager
        manager = StringPipeManager(event, pipe)

        # Set event after a short delay to test early break
        time.sleep(0.01)
        event.set()
        manager.thread.join(timeout=1.0)

        # Should have read some lines
        result = manager.read()
        assert isinstance(result, str)

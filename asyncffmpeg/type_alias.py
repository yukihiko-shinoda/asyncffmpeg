"""Type alias."""

from __future__ import annotations

from typing import Any

# Reason: Maybe, requires to update ffmpeg-python side.
from ffmpeg.nodes import Stream  # type: ignore[import-untyped]

__all__ = ["StreamSpec"]

StreamSpec = None | Stream | list | tuple[Any] | dict

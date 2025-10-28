"""Type alias."""

from __future__ import annotations

from typing import Any
from typing import Union

# Reason: Maybe, requires to update ffmpeg-python side.
from ffmpeg.nodes import Stream  # type: ignore[import-untyped]

__all__ = ["StreamSpec"]

# Note: Using typing.Any for list/dict/tuple elements because this is a runtime type alias
# and needs to match the ffmpeg-python library's flexible type handling
StreamSpec = Union[None, Stream, list[Any], tuple[Any, ...], dict[Any, Any]]

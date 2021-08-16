"""Type alias."""
from typing import Any, Dict, List, Tuple, Union

# Reason: Maybe, requires to update ffmpeg-python side.
from ffmpeg.nodes import Stream  # type: ignore

__all__ = ["StreamSpec"]

StreamSpec = Union[None, Stream, List, Tuple[Any], Dict]

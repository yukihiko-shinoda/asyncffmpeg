"""Type alias."""
from typing import Dict, List, Tuple, Union

from ffmpeg.nodes import Stream

__all__ = ["StreamSpec"]

StreamSpec = Union[None, Stream, List, Tuple, Dict]

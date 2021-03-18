"""Type alias."""
from typing import Dict, List, Tuple, Union

from ffmpeg.nodes import Stream

StreamSpec = Union[None, Stream, List, Tuple, Dict]

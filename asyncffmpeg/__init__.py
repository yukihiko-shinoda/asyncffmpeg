"""Top-level package for Asynchronous FFmpeg."""
from typing import List

from asyncffmpeg.exceptions import *  # noqa
from asyncffmpeg.ffmpeg_coroutine import *  # noqa
from asyncffmpeg.ffmpeg_coroutine_factory import *  # noqa
from asyncffmpeg.ffmpegprocess.interface import *  # noqa
from asyncffmpeg.type_alias import *  # noqa

__author__ = """Yukihiko Shinoda"""
__email__ = "yuk.hik.future@gmail.com"
__version__ = "1.0.1"

__all__: List[str] = []
# pylint: disable=undefined-variable
__all__ += ffmpegprocess.interface.__all__  # type: ignore # noqa
# pylint: disable=undefined-variable
__all__ += exceptions.__all__  # type: ignore # noqa
# pylint: disable=undefined-variable
__all__ += ffmpeg_coroutine_factory.__all__  # type: ignore # noqa
# pylint: disable=undefined-variable
__all__ += ffmpeg_coroutine.__all__  # type: ignore # noqa
# pylint: disable=undefined-variable
__all__ += type_alias.__all__  # type: ignore # noqa

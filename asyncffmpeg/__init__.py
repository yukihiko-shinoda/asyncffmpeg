"""Top-level package for Asynchronous FFmpeg."""

from asyncffmpeg.exceptions import *  # noqa: F403
from asyncffmpeg.ffmpeg_coroutine import *  # noqa: F403
from asyncffmpeg.ffmpeg_coroutine_factory import *  # noqa: F403
from asyncffmpeg.ffmpegprocess.interface import *  # noqa: F403
from asyncffmpeg.type_alias import *  # noqa: F403

__author__ = """Yukihiko Shinoda"""
__email__ = "yuk.hik.future@gmail.com"
__version__ = "1.2.0"

__all__: list[str] = []
__all__ += exceptions.__all__  # type: ignore[name-defined]  # noqa: F405 pylint: disable=undefined-variable
__all__ += ffmpeg_coroutine.__all__  # type: ignore[name-defined]  # noqa: F405 pylint: disable=undefined-variable
__all__ += ffmpeg_coroutine_factory.__all__  # type: ignore[name-defined]  # noqa: F405 pylint: disable=undefined-variable
__all__ += ffmpegprocess.interface.__all__  # type: ignore[name-defined]  # noqa: F405 pylint: disable=undefined-variable
__all__ += type_alias.__all__  # type: ignore[name-defined]  # noqa: F405 pylint: disable=undefined-variable

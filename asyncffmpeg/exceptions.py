"""This module implements exceptions for this package."""

__all__ = ["FFmpegProcessError"]


class Error(Exception):
    """
    Base class for exceptions in this module.
    @see https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions
    """


class FFmpegProcessError(Error):
    """FFmpeg process failed."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code

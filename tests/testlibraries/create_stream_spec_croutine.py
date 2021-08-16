"""Coroutines for creating stream spec."""
from pathlib import Path
from typing import Union

import ffmpeg

# Reason: Following export method in __init__.py from Effective Python 2nd Edition item 85
from asyncffmpeg import StreamSpec  # type: ignore


class CreateStreamSpecCoroutineCopy:
    """Coroutine to create stream spec to copy."""

    def __init__(self, path_file_input: Path, path_file_output: Path) -> None:
        self.path_file_input = path_file_input
        self.path_file_output = path_file_output

    async def create(self) -> StreamSpec:
        stream = ffmpeg.input(self.path_file_input)
        return ffmpeg.output(stream, str(self.path_file_output), c="copy").global_args("-n")


class CreateStreamSpecCoroutineFilter:
    """Coroutine to create stream spec to filter."""

    def __init__(self, path_file_input: Union[Path, str], path_file_output: Union[Path, str]) -> None:
        self.path_file_input = path_file_input
        self.path_file_output = path_file_output

    async def create(self) -> StreamSpec:
        stream = ffmpeg.input(self.path_file_input)
        stream = ffmpeg.filter(stream, "scale", 768, -1)
        return ffmpeg.output(stream, str(self.path_file_output)).global_args("-n")

"""Coroutines for creating stream spec."""
import ffmpeg

from asyncffmpeg import StreamSpec


class CreateStreamSpecCoroutineCopy:
    """Coroutine to create stream spec to copy."""

    def __init__(self, path_file_input, path_file_output):
        self.path_file_input = path_file_input
        self.path_file_output = path_file_output

    async def create(self) -> StreamSpec:
        stream = ffmpeg.input(self.path_file_input)
        return ffmpeg.output(stream, str(self.path_file_output), c="copy").global_args("-n")


class CreateStreamSpecCoroutineFilter:
    """Coroutine to create stream spec to filter."""

    def __init__(self, path_file_input, path_file_output):
        self.path_file_input = path_file_input
        self.path_file_output = path_file_output

    async def create(self) -> StreamSpec:
        stream = ffmpeg.input(self.path_file_input)
        stream = ffmpeg.filter(stream, "scale", 768, -1)
        return ffmpeg.output(stream, str(self.path_file_output)).global_args("-n")

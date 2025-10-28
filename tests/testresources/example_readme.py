"""Example of README.md."""

from __future__ import annotations

import asyncio
from typing import Any

import ffmpeg
from asynccpu import ProcessTaskPoolExecutor

from asyncffmpeg import FFmpegCoroutineFactory
from asyncffmpeg import StreamSpec


async def create_stream_spec_copy() -> StreamSpec:
    stream = ffmpeg.input("input.mp4")
    return ffmpeg.output(stream, "output1.mp4", c="copy")


async def create_stream_spec_filter() -> StreamSpec:
    stream = ffmpeg.input("input.mp4")
    stream = ffmpeg.filter(stream, "scale", 768, -1)
    return ffmpeg.output(stream, "output2.mp4")


async def main() -> None:
    """Main function demonstrating concurrent FFmpeg operations."""
    ffmpeg_coroutine = FFmpegCoroutineFactory.create()

    with ProcessTaskPoolExecutor(max_workers=3, cancel_tasks_when_shutdown=True) as executor:
        awaitables: tuple[Any, ...] = tuple(
            executor.create_process_task(ffmpeg_coroutine.execute, create_stream_spec)
            for create_stream_spec in [create_stream_spec_copy, create_stream_spec_filter]
        )
        await asyncio.gather(*awaitables)


if __name__ == "__main__":
    asyncio.run(main())

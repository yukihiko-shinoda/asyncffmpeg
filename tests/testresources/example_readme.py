import ffmpeg
from asynccpu import ProcessTaskPoolExecutor

from asyncffmpeg import FFmpegCoroutineFactory


async def create_stream_spec_copy():
    stream = ffmpeg.input("input.mp4")
    return ffmpeg.output(stream, "output.mp4", c="copy")


async def create_stream_spec_filter():
    stream = ffmpeg.input("input.mp4")
    stream = ffmpeg.filter(stream, "scale", 768, -1)
    return ffmpeg.output(stream, "output.mp4")


ffmpeg_coroutine = FFmpegCoroutineFactory.create()

with ProcessTaskPoolExecutor(max_workers=3, cancel_tasks_when_shutdown=True) as executor:
    awaitables = {
        executor.create_process_task(ffmpeg_coroutine, create_stream_spec)
        for create_stream_spec in [create_stream_spec_copy, create_stream_spec_filter]
    }
    await asyncio.gather(*awaitables)

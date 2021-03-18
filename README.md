# Asynchronous FFmpeg

[![Test](https://github.com/yukihiko-shinoda/asyncffmpeg/workflows/Test/badge.svg)](https://github.com/yukihiko-shinoda/asyncffmpeg/actions?query=workflow%3ATest)
[![Test Coverage](https://api.codeclimate.com/v1/badges/d0715bdfc5dd7725e0a2/test_coverage)](https://codeclimate.com/github/yukihiko-shinoda/asyncffmpeg/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/d0715bdfc5dd7725e0a2/maintainability)](https://codeclimate.com/github/yukihiko-shinoda/asyncffmpeg/maintainability)
[![Code Climate technical debt](https://img.shields.io/codeclimate/tech-debt/yukihiko-shinoda/asyncffmpeg)](https://codeclimate.com/github/yukihiko-shinoda/asyncffmpeg)
[![Updates](https://pyup.io/repos/github/yukihiko-shinoda/asyncffmpeg/shield.svg)](https://pyup.io/repos/github/yukihiko-shinoda/asyncffmpeg/)
[![Python versions](https://img.shields.io/pypi/pyversions/asyncffmpeg.svg)](https://pypi.org/project/asyncffmpeg)
[![Twitter URL](https://img.shields.io/twitter/url?style=social&url=https%3A%2F%2Fgithub.com%2Fyukihiko-shinoda%2Fasyncffmpeg)](http://twitter.com/share?text=Asynchronous%20FFmpeg&url=https://pypi.org/project/asyncffmpeg/&hashtags=python)

Supports async / await pattern for FFmpeg operations.

## Advantage

1. Support async / await pattern for FFmpeg operations
2. Support Ctrl + C

### 1. Support async / await pattern for FFmpeg operations

This package supports FFmpeg asynchronously invoke with async / await pattern
wrapping [`ffmpeg.run_async()`] of [ffmpeg-python] and returned [`subprocess.Popen`].

The async / await syntax makes asynchronous code as:

- Simple
- Readable

### 2. Support Ctrl + C

User can stop FFmpeg process gracefully by Ctrl + C.
This works as same as sending `q` key to running FFmpeg.
This action is guaranteed by pytest.

## Quickstart

### 1. Install

```console
pip install asyncffmpeg
```

### 2. Implement

`asyncffmpeg.FFmpegCoroutine` class has asynchronous method: `execute()`.
To run concurrently, it requires not multi threading but multi processing
since FFmpeg process is CPU-bound operation.
The package [`asynccpu`] is helpful to simple implement.

Ex:

```python
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
```

#### Why not [`asyncio`] but [`asynccpu`] ?

Unfortunately High-level APIs of [`asyncio`] doesn't support CPU-bound operations
since it works based on not [`ProcessPoolExecutor`] but [`ThreadPoolExecutor`].
When we want to run CPU-bound operations concurrently with [`asyncio`],
we need to use Low-level APIs which need finer control over the event loop behavior.

### Note

The argument of [`Coroutine`] requires not "raw [`Coroutine`] object" but "[`Coroutine`] function"
since raw [`Coroutine`] object is not picklable.

This specification is depend on the one of Python [`multiprocessing`] package:

[multiprocessing — Process-based parallelism]

> Note When an object is put on a queue, the object is pickled
> and a background thread later flushes the pickled data to an underlying pipe.

<!-- markdownlint-disable-next-line no-inline-html -->
See: [Answer: Python multiprocessing PicklingError: Can't pickle <type 'function'> - Stack Overflow]

## API

### FFmpegCoroutineFactory

```python
class FFmpegCoroutineFactory:
    @staticmethod
    def create(
        *,
        time_to_force_termination: int = 8
    ) -> FFmpegCoroutine:
```

#### time_to_force_termination: int = 8

The time limit (second) to wait stopping FFmpeg process gracefully
when send Ctrl + C.
At first, subprocess will try to send `q` key to FFmpeg process.
In case when FFmpeg process doesn't stop gracefully by time limit,
subprocess will terminate process.

### FFmpegCoroutine

```python
class FFmpegCoroutine:
    async def execute(
        self,
        create_stream_spec: Callable[[], Awaitable[StreamSpec]],
        *,
        after_start: Optional[Callable[[FFmpegProcess], Awaitable]] = None
    ) -> None:
```

#### create_stream_spec: Callable[[], Awaitable[StreamSpec]]

[`Coroutine`] function to create [stream spec] for FFmpeg process.
Created [stream spec] will be set the first argument of [`ffmpeg.run_async()`] of [ffmpeg-python] inside of `FFmpegCoroutine`.
[stream spec] is a Stream, list of Streams, or label-to-Stream dictionary mapping
in [ffmpeg-python].

#### after_start: Optional[Callable[[FFmpegProcess], Awaitable]] = None

[`Coroutine`] function to execute after start FFmpeg process.

## Credits

This package was created with [Cookiecutter] and the [yukihiko-shinoda/cookiecutter-pypackage] project template.

[`ffmpeg.run_async()`]: https://kkroening.github.io/ffmpeg-python/#ffmpeg.run_async
[ffmpeg-python]: https://pypi.org/project/ffmpeg-python/
[`subprocess.Popen`]: https://docs.python.org/3/library/subprocess.html#popen-objects
[`asyncio`]: https://docs.python.org/3/library/asyncio.html
[`ProcessPoolExecutor`]: https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor
[`ThreadPoolExecutor`]: https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor
[`asynccpu`]: https://pypi.org/project/asynccpu/
[`Coroutine`]: https://docs.python.org/3/library/asyncio-task.html#coroutines
[`multiprocessing`]: https://docs.python.org/3/library/multiprocessing.html
[multiprocessing — Process-based parallelism]: https://docs.python.org/3/library/multiprocessing.html
<!-- markdownlint-disable-next-line no-inline-html -->
[Answer: Python multiprocessing PicklingError: Can't pickle <type 'function'> - Stack Overflow]: https://stackoverflow.com/a/8805244/12721873
[stream spec]: https://ffmpeg.org/ffmpeg.html#Stream-specifiers-1
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[yukihiko-shinoda/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage

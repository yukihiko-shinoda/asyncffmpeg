"""This module implements fixture of instance."""


# Reason: This class is aggregation. pylint: disable=too-few-public-methods
class InstanceResource:
    """This class implements fixture of instance."""

    # Samples:
    # Debian buster:           "ffmpeg version 4.1.6 Copyright (c) 2000-2020 the FFmpeg developers"
    # Ubuntu 20.04 FFmpeg 4.4: "ffmpeg version 4.4 Copyright (c) 2000-2021 the FFmpeg developers"
    # Windows 10 FFmpeg 4.4:   "ffmpeg version 4.4-essentials_build-www.gyan.dev Copyright (c) 2000-2021 the FFmpeg developers"
    REGEX_STDERR_FFMPEG_FIRSTLINE = (
        r"ffmpeg\sversion\s\d+\.\d+(\.\d+)?"
        r"(\-\d+ubuntu\d+\.\d+)?"
        r"((\-\d{4}\-\d{2}(\-\d{2}?)?)?(\-essentials_build\-www\.gyan\.dev)?)?"
        r"\sCopyright\s\(c\)\s\d{4}\-\d{4}\sthe\sFFmpeg\sdevelopers"
    )
    REGEX_STDERR_FFMPEG_LASTLINE = (
        r"video:\d+kB\saudio:\d+kB\ssubtitle:\d+kB\sother\sstreams:\d+kB\sglobal\sheaders:\d+kB"
        r"\smuxing\soverhead:\s(\d*[.])?\d+%"
    )

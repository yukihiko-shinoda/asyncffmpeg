FROM futureys/claude-code-python-development:20260609002000
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Stable can't be installed due to the following error:
    # 2.675 Some packages could not be installed. This may mean that you have
    # 2.675 requested an impossible situation or if you are using the unstable
    # 2.675 distribution that some required packages have not yet been created
    # 2.675 or been moved out of Incoming.
    # 2.675 The following information may help to resolve the situation:
    # 2.675 
    # 2.675 The following packages have unmet dependencies:
    # 2.675  ffmpeg : Depends: libavcodec61 (>= 7:7.1)
    # 2.675           Depends: libavfilter10 (>= 7:7.0)
    # 2.675           Depends: libavformat61 (>= 7:7.0)
    # 2.675           Depends: libswresample5 (>= 7:7.0) but it is not installable
    # 2.675  libavdevice61 : Depends: libavcodec61 (>= 7:7.1.4)
    # 2.675                  Depends: libavfilter10 (>= 7:7.1.4)
    # 2.675                  Depends: libavformat61 (= 7:7.1.4-0+deb13u1)
    # 2.675                  Depends: libavutil59 (= 7:7.1.4-0+deb13u1) but 7:7.1.3-0+deb13u1 is to be installed
    # 2.675  libpostproc58 : Depends: libavutil59 (>= 7:7.1.4) but 7:7.1.3-0+deb13u1 is to be installed
    # 2.675  libswscale8 : Depends: libavutil59 (= 7:7.1.4-0+deb13u1) but 7:7.1.3-0+deb13u1 is to be installed
    # 2.676 E: Unable to correct problems, you have held broken packages.
    # 2.676 E: The following information from --solver 3.0 may provide additional context:
    # 2.676    Unable to satisfy dependencies. Reached two conflicting decisions:
    # 2.676    1. libavutil59:arm64=7:7.1.4-0+deb13u1 is not selected for install
    # 2.676    2. libavutil59:arm64=7:7.1.4-0+deb13u1 is selected for install because:
    # 2.676       1. ffmpeg:arm64=7:7.1.3-0+deb13u1 is selected for install
    # 2.676       2. ffmpeg:arm64=7:7.1.3-0+deb13u1 Depends libavdevice61 (>= 7:7.0)
    # 2.676       3. libavdevice61:arm64 is available in versions 7:7.1.4-0+deb13u1, 7:7.1.3-0+deb13u1
    # 2.676          [selected libavdevice61:arm64=7:7.1.4-0+deb13u1 for install]
    # 2.676       4. libavdevice61:arm64=7:7.1.4-0+deb13u1 Depends libavutil59 (= 7:7.1.4-0+deb13u1)
    # 2.676       For context, additional choices that could not be installed:
    # 2.676       * In libavdevice61:arm64 is available in versions 7:7.1.4-0+deb13u1, 7:7.1.3-0+deb13u1:
    # 2.676         - libavdevice61:arm64=7:7.1.3-0+deb13u1 is not selected for install
    ffmpeg=7:7.1.4-0+deb13u1 \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml /workspace
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync
COPY . /workspace
CMD ["invoke", "test.coverage"]

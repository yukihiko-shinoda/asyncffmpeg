FROM futureys/claude-code-python-development:20260221145500
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    # To install ruamel-yaml-clib (the dependency of semgrep)
    #   error: command 'cc' failed: No such file or directory
    #   hint: This usually indicates a problem with the package or the build
    #       environment.
    #   help: `ruamel-yaml-clib` (v0.2.14) was included because `asyncffmpeg:dev`
    #         (v1.3.0) depends on `semgrep` (v1.145.0) which depends on
    #         `ruamel-yaml-clib`
    build-essential \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml /workspace
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python 3.13
COPY . /workspace
ENTRYPOINT [ "uv", "run" ]
CMD ["invoke", "test.coverage"]

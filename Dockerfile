FROM futureys/claude-code-python-development:20250915024000
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml /workspace
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync
COPY . /workspace
ENTRYPOINT [ "uv", "run" ]
CMD ["invoke", "test.coverage"]

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**asyncffmpeg** is a Python library that wraps ffmpeg-python to provide async/await pattern support for FFmpeg operations with graceful Ctrl+C handling. It uses multiprocessing (not multithreading) for concurrent FFmpeg operations since FFmpeg is CPU-bound.

## Development Commands

### Running Tests

```bash
# Run fast tests (excludes @pytest.mark.slow tests)
uv run invoke test

# Run all tests including slow ones
uv run invoke test.all

# Run tests with coverage report (opens in browser)
uv run invoke coverage

# Run tests with XML coverage report
uv run invoke coverage --xml

# Run a specific test file
uv run pytest tests/test_ffmpeg_coroutine.py

# Run a specific test
uv run pytest tests/test_ffmpeg_coroutine.py::TestFFmpegCoroutine::test_excecption
```

### Linting and Code Quality

```bash
# Fast linting (xenon, ruff, bandit, dodgy, flake8, pydocstyle)
uv run invoke lint

# Deep linting (mypy, pylint, semgrep) - slower but more thorough
uv run invoke lint.deep

# Individual linters
uv run invoke lint.mypy
uv run invoke lint.pylint
uv run invoke lint.flake8
uv run invoke lint.ruff
uv run invoke lint.bandit
uv run invoke lint.cohesion

# Code complexity analysis
uv run invoke lint.xenon
uv run invoke lint.radon
```

### Code Formatting

```bash
# Format code with docformatter and Ruff
uv run invoke style

# Check formatting without modifying files
uv run invoke style --check
```

### Building and Distribution

```bash
# Build source and wheel packages
uv run invoke dist

# Clean all artifacts
uv run invoke clean
```

## Architecture

### Platform-Specific FFmpeg Process Handling

The library uses a factory pattern to handle platform differences:

- **FFmpegCoroutineFactory**: Creates platform-specific FFmpegCoroutine instances
  - POSIX systems: Uses `FFmpegProcessPosix`
  - Windows: Uses `FFmpegProcessWindowsWrapper` (handles Windows-specific Ctrl+C behavior via pywin32)

### Core Components

1. **FFmpegCoroutine** ([asyncffmpeg/ffmpeg_coroutine.py](asyncffmpeg/ffmpeg_coroutine.py))
   - Main interface for executing FFmpeg operations
   - Handles SIGTERM signals and graceful shutdown
   - Manages the lifecycle: start → optional after_start callback → wait → quit on interruption
   - Time-based forced termination if graceful shutdown fails

2. **FFmpegProcess** ([asyncffmpeg/ffmpegprocess/interface.py](asyncffmpeg/ffmpegprocess/interface.py))
   - Wraps subprocess.Popen for FFmpeg processes
   - Provides `wait()` and `quit()` methods
   - Platform-specific implementations in `posix.py` and `windows.py`

3. **RealtimePipeReader** ([asyncffmpeg/pipe/realtime_pipe_reader.py](asyncffmpeg/pipe/realtime_pipe_reader.py))
   - Non-blocking reader for stdout/stderr pipes using threading
   - Prevents FFmpeg process from blocking on pipe buffers
   - `FFmpegRealtimePipeReader`: FFmpeg-specific implementation
   - `StringRealtimePipeReader`: General string output reader

### Important Patterns

- **Coroutine Functions vs Objects**: Arguments accept coroutine *functions* (not raw coroutine objects) because coroutine objects aren't picklable for multiprocessing
- **Graceful Shutdown**: Sends 'q' key to FFmpeg, waits for timeout, then terminates
- **Error Handling**: Raises `FFmpegProcessError` with stderr and exit code when FFmpeg fails

## Key Design Constraints

1. **Multiprocessing Required**: FFmpeg is CPU-bound, so concurrent operations require ProcessPoolExecutor, not ThreadPoolExecutor. The companion library `asynccpu` is recommended for this.

2. **Picklability**: All objects passed between processes must be picklable. This is why `create_stream_spec` is a coroutine function, not a coroutine object.

3. **Pipe Management**: FFmpeg can block if stdout/stderr pipes aren't read. The RealtimePipeReader runs threads to continuously read pipes and prevent blocking.

4. **Platform Differences**: Windows requires special handling for Ctrl+C interruption using pywin32 (win32api). POSIX systems need to stop the pipe reader before calling quit() to avoid "Bad file descriptor" errors.

## Testing Specifics

- Tests use `caplog_workaround` fixture to capture logs from subprocess
- Coverage runs with `--concurrency=multiprocessing` setting
- Windows-specific code in `asyncffmpeg/ffmpegprocess/windows.py` and `windows_wrapper.py` is excluded from coverage on non-Windows systems
- Tests require `asynccpu`, `psutil`, and `pytest-resource-path` packages
- Sample video file at `tests/testlibraries/resources/sample.mp4` used for testing

## Configuration Notes

- **Line Length**: Flake8 uses max 108 chars (to work with flake8-bugbear B950 which allows 10% over), Ruff/Black use 119
- **Type Checking**: mypy runs in strict mode; ignores missing imports for `ffmpeg`, `win32api`, `win32con`
- **Import Style**: Ruff configured with `force-single-line = true` for imports
- **Docstrings**: Google-style convention, minimum length 7 characters (shorter functions may skip docstrings)

## Code Conventions

- Uses Python 3.9+ type hints throughout
- Line length: 119 characters (configured for Black compatibility)
- Import style: Force single-line imports (ruff configured)
- Documentation: Google docstring style
- Imports are always put at the top of the file, just after any module comments and docstrings, and before module globals and constants.
- Function arguments requires to have type annotations.
- Use Guard Clauses to reduce nesting and improve readability.

### Import Guidelines

#### Import Placement

- **ALL imports MUST be at the top-level of the file**, immediately after any module comments and docstrings, and before module globals and constants
- **NEVER place imports inside functions, methods, or classes** - this violates PEP 8 and makes dependencies unclear
- **NEVER use conditional imports inside functions** unless absolutely necessary for optional dependencies

#### Import Organization

1. Standard library imports
2. Third-party library imports
3. Local application/library imports

#### Prohibited Patterns

```python
# ❌ NEVER DO THIS - imports inside methods
def test_something():
    import os  # WRONG!
    from pathlib import Path  # WRONG!

# ❌ NEVER DO THIS - imports inside classes
class TestClass:
    def method(self):
        import tempfile  # WRONG!

# ✅ CORRECT - all imports at top
import os
import tempfile
from pathlib import Path

def test_something():
    # Use the imports here
```

Exceptions

- Only use local imports when dealing with circular dependencies or optional dependencies that may not be available
- If you must use local imports, document the reason with a comment

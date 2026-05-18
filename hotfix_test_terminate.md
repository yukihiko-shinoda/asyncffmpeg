# Hotfix: test_terminate

## Context

`test_terminate` verifies that when a process running an FFmpeg coroutine receives SIGTERM, the coroutine's `sigterm_handler` runs, cancels the asyncio tasks, and the FFmpeg subprocess is shut down cleanly. The test spawns a `multiprocessing.Process`, waits for a "Ready" socket signal, then calls `psutil.Process.terminate()` (SIGTERM), and asserts both the exit code and that the log contains `"FFmpeg process quit finish"`.

After upgrading dependencies (moving to Python 3.14), this test fails with:

```
AssertionError: assert None in [-15, 1]
 +  where None = wait()
 +    where wait = psutil.Process(pid=11901, status='terminated').wait
```

## Root Cause

**Python 3.14 changed the default `multiprocessing` start method from `fork` to `forkserver` on Linux.**

With `forkserver`, the child is not forked directly by the test process. A long-running forkserver daemon performs the actual fork, so:

- The child's `ppid` equals the forkserver daemon's PID, **not** `os.getpid()` of the test.
- `psutil.Process.wait()` in psutil 7.x calls `os.waitpid()` only for direct children of `os.getpid()`. For non-direct children it returns `None` immediately, matching the documented behavior:

  > "Wait for process to terminate, and if process is a children of `os.getpid()`, also return its exit code, **else None**."

Additionally, `caplog_workaround` relies on the child inheriting a `QueueHandler` that was added to the parent's root logger before `process.start()`. With `forkserver`, child processes start from a clean state and do **not** inherit the parent's logger handlers. Subprocess logs (e.g., `"FFmpeg process quit finish"`) never reach the parent's `logger_queue`, so the caplog assertion would also fail once the exit-code assertion is fixed.

**Confirmed**: Using `multiprocessing.get_context('fork').Process(...)` makes the child a direct child of the test process (`child.ppid() == os.getpid()`), `psutil.wait()` returns the actual exit code (`-15` or `1`), and the `QueueHandler` is inherited via the fork.

## Critical Files

- [tests/test_ffmpeg_coroutine.py](tests/test_ffmpeg_coroutine.py) — `terminate()` classmethod (lines ~204–217)

## Implementation

### Step 1 — Add `import multiprocessing` to `tests/test_ffmpeg_coroutine.py`

`multiprocessing` is not currently a top-level import in the test file (only `from multiprocessing.context import Process` is imported). Add it with the other standard-library imports. *(This step may already be done as part of the `test_keyboard_interrupt` hotfix.)*

### Step 2 — Change `Process(...)` to `multiprocessing.get_context('fork').Process(...)` in `terminate()`

**Before** (`tests/test_ffmpeg_coroutine.py`, `terminate` method):
```python
@classmethod
def terminate(cls, path_file_input: Path, path_file_output: Path) -> None:
    """Test process of keyboard interrupt."""
    process = Process(target=cls.report_raises_cencelled_error, args=(path_file_input, path_file_output))
    process.start()
    ...
```

**After**:
```python
@classmethod
def terminate(cls, path_file_input: Path, path_file_output: Path) -> None:
    """Test process of keyboard interrupt."""
    process = multiprocessing.get_context('fork').Process(
        target=cls.report_raises_cencelled_error, args=(path_file_input, path_file_output)
    )
    process.start()
    ...
```

No other changes to this method are required. The existing `psutil_process.wait() in [-15, 1]` and `psutil_process.is_running()` assertions are correct once the child is a direct fork child.

**Exit code values**:
- `-15` (`-signal.SIGTERM`): process was killed by SIGTERM before its handler could complete
- `1`: `sigterm_handler` ran, cancelled asyncio tasks, `CancelledError` propagated uncaught out of `asyncio.run()`, causing a non-zero exit

## Verification

```bash
# Run only this test:
uv run --no-dev pytest -vv tests/test_ffmpeg_coroutine.py::TestFFmpegCoroutine::test_terminate

# Expected output: PASSED
# Confirm caplog assertion passes too:
#   "FFmpeg process quit finish" in caplog.text

# Run all tests together to confirm no regressions:
uv run --no-dev pytest -vv tests/test_ffmpeg_coroutine.py
# Expected: 5 passed, 1 skipped (Windows-only test)
```

# Hotfix: test_keyboard_interrupt

## Context

`test_keyboard_interrupt` verifies that when Ctrl+C (SIGINT) is sent to a running FFmpeg coroutine process, the process handles `KeyboardInterrupt` gracefully and exits with code 0. The test spawns a `multiprocessing.Process`, sends signals to it, waits for a "Test succeed" socket message, then asserts the exit code and that the log contains the expected shutdown messages.

After upgrading dependencies (moving to Python 3.14), this test fails with:

```
AssertionError: assert None == 0
 +  where None = wait()
 +    where wait = psutil.Process(pid=11872, status='terminated').wait
```

## Root Cause

**Python 3.14 changed the default `multiprocessing` start method from `fork` to `forkserver` on Linux.**

With `forkserver`, when `process.start()` is called, the child is not spawned directly by the test process. Instead, a long-running forkserver daemon forks the child. As a result:

- The child's `ppid` (parent PID) equals the forkserver's PID, **not** `os.getpid()` of the test.
- `psutil.Process.wait()` in psutil 7.x checks whether the target is a direct child of `os.getpid()`. If not, it returns `None` immediately instead of calling `os.waitpid()`.

Additionally, `caplog_workaround` relies on the child inheriting a `QueueHandler` that was added to the parent's root logger before `process.start()`. With `forkserver`, child processes start from a clean state and do **not** inherit the parent's logger handlers. This means subprocess logs (e.g., `"FFmpeg process quit finish"`) never reach the parent's `logger_queue`, and the caplog assertion would also fail.

**Confirmed**: Using `multiprocessing.get_context('fork').Process(...)` makes the child a direct child of the test process (`child.ppid() == os.getpid()`), `psutil.wait()` returns the actual exit code, and the `QueueHandler` is inherited via the fork.

## Critical Files

- [tests/test_ffmpeg_coroutine.py](tests/test_ffmpeg_coroutine.py) — `keyboard_interrupt()` classmethod (lines ~101–117)

## Implementation

### Step 1 — Add `import multiprocessing` to `tests/test_ffmpeg_coroutine.py`

`multiprocessing` is not currently a top-level import in the test file (only `from multiprocessing.context import Process` is imported). Add it with the other standard-library imports.

### Step 2 — Change `Process(...)` to `multiprocessing.get_context('fork').Process(...)` in `keyboard_interrupt()`

**Before** (`tests/test_ffmpeg_coroutine.py`, `keyboard_interrupt` method):
```python
@classmethod
def keyboard_interrupt(cls, path_file_input: Path, path_file_output: Path) -> None:
    """Test process of keyboard interrupt."""
    process = Process(target=cls.report_raises_keyboard_interrupt, args=(path_file_input, path_file_output))
    process.start()
    ...
```

**After**:
```python
@classmethod
def keyboard_interrupt(cls, path_file_input: Path, path_file_output: Path) -> None:
    """Test process of keyboard interrupt."""
    process = multiprocessing.get_context('fork').Process(
        target=cls.report_raises_keyboard_interrupt, args=(path_file_input, path_file_output)
    )
    process.start()
    ...
```

No other changes to this method are required. The existing `psutil_process.wait() == 0` and `psutil_process.is_running()` assertions are correct once the child is a direct fork child.

## Verification

```bash
# Run only this test:
uv run --no-dev pytest -vv tests/test_ffmpeg_coroutine.py::TestFFmpegCoroutine::test_keyboard_interrupt

# Expected output: PASSED
# Confirm caplog assertion passes too:
#   "SIGTERM handler: Start" in caplog.text or "FFmpeg process quit finish" in caplog.text
```

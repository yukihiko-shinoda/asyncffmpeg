# Hotfix: test_keyboard_interrupt_for_coverage

## Context

`test_keyboard_interrupt_for_coverage` exercises the `except KeyboardInterrupt` branch inside `FFmpegCoroutine.execute()` in a way that coverage.py can trace. Direct use of `asyncio.ProcessPoolExecutor` is untraceable by coverage (see [coverage issue #481](https://github.com/nedbat/coveragepy/issues/481)), so the test uses `ProcessPoolExecutorSimulator`: it advances an async coroutine step-by-step via `.send()` calls, each step running in a child `multiprocessing.Process`. This lets the coroutine be interrupted mid-execution via SIGINT.

After upgrading dependencies (moving to Python 3.14), this test fails with:

```
psutil.NoSuchProcess: process PID not found (pid=11978)
```

## Root Cause

**Python 3.14 changed the default `multiprocessing` start method from `fork` to `forkserver` on Linux.**

With `forkserver` (and `spawn`), subprocess arguments are serialized with `pickle` before being sent to the child. `ProcessPoolExecutorSimulator.__init__` stores the process as:

```python
self.process = multiprocessing.Process(target=self.run, args=(corofn, *args), kwargs=kwargs)
```

Inside `ProcessPoolExecutorSimulator.run()`, an `asyncio` coroutine object is created and stored in `CoroutineExecutor.coroutine`. Then `CoroutineExecutor.run_step_in_child_process()` creates a second-level subprocess:

```python
process = multiprocessing.Process(target=self.run_step, args=(arg,))
```

Here `self` is a `CoroutineExecutor` instance whose `coroutine` attribute is an **asyncio coroutine object**. Coroutines cannot be pickled, so the subprocess creation fails immediately:

```
TypeError: cannot pickle 'coroutine' object
when serializing dict item 'coroutine'
when serializing tests.testlibraries.process_pool_executor_simulator.CoroutineExecutor state
```

The process exits before it can do any useful work, and by the time `simulate_ctrl_c_in_posix` tries `psutil.Process(process.pid)`, the PID is already gone → `NoSuchProcess`.

A secondary effect: `caplog_workaround` adds a `QueueHandler` to the parent's root logger before the subprocess is started. With `forkserver`, children start from a clean state and do not inherit this handler. Subprocess logs (e.g., `"FFmpeg process quit finish"`) would never reach the parent's caplog. The final assertion `assert "FFmpeg process quit finish" in caplog.text` would fail even after the pickling issue is fixed, unless `fork` is used.

**Fix**: Use `multiprocessing.get_context('fork').Process(...)` for both the outer process in `ProcessPoolExecutorSimulator` and the inner process in `CoroutineExecutor.run_step_in_child_process()`. With `fork`, the child inherits the parent's memory (including the coroutine state and the `QueueHandler`), eliminating both the pickling failure and the log-capture failure.

## Critical Files

- [tests/testlibraries/process_pool_executor_simulator.py](tests/testlibraries/process_pool_executor_simulator.py)
  - `CoroutineExecutor.run_step_in_child_process()` (line ~51)
  - `ProcessPoolExecutorSimulator.__init__()` (line ~73)

## Implementation

Both changes are in `tests/testlibraries/process_pool_executor_simulator.py`. The `multiprocessing` module is already imported there.

### Change 1 — `CoroutineExecutor.run_step_in_child_process()`

**Before**:
```python
def run_step_in_child_process(self, arg: TypeVarArgument) -> TypeVarReturnValue:
    process = multiprocessing.Process(target=self.run_step, args=(arg,))
    process.start()
    process.join()
    return self.queue.get()
```

**After**:
```python
def run_step_in_child_process(self, arg: TypeVarArgument) -> TypeVarReturnValue:
    process = multiprocessing.get_context('fork').Process(target=self.run_step, args=(arg,))
    process.start()
    process.join()
    return self.queue.get()
```

### Change 2 — `ProcessPoolExecutorSimulator.__init__()`

**Before**:
```python
self.process = multiprocessing.Process(target=self.run, args=(corofn, *args), kwargs=kwargs)
```

**After**:
```python
self.process = multiprocessing.get_context('fork').Process(target=self.run, args=(corofn, *args), kwargs=kwargs)
```

## Verification

```bash
# Run only this test:
uv run --no-dev pytest -vv tests/test_ffmpeg_coroutine.py::TestFFmpegCoroutine::test_keyboard_interrupt_for_coverage

# Expected output: PASSED
# Confirm the key assertion passes:
#   "FFmpeg process quit finish" in caplog.text
```

"""File utilities for English Trainer."""
# Platform-specific imports are done inside functions for cross-platform support.
# pylint: disable=import-outside-toplevel,import-error

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator


@contextmanager
def file_lock(path: Path, timeout: float) -> Generator[None, None, None]:
    """
    Cross-platform file locking context manager.

    Args:
        path: Path to lock file
        timeout: Timeout in seconds

    Yields:
        None

    Raises:
        TimeoutError: If lock cannot be acquired within timeout
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()

    with open(path, "a+", encoding="utf-8") as f:
        try:
            while True:
                try:
                    if os.name == "nt":
                        # Windows
                        import msvcrt

                        # typeshed may not expose the locking constants; ignore attr errors
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]
                    else:
                        # Unix-like systems
                        import fcntl

                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (OSError, IOError) as exc:
                    if time.monotonic() - start >= timeout:
                        raise TimeoutError(
                            f"Could not acquire lock on {path} within {timeout}s"
                        ) from exc
                    time.sleep(0.05)

            yield

        finally:
            try:
                if os.name == "nt":
                    import msvcrt

                    # typeshed may not expose the locking constants; ignore attr errors
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
                else:
                    import fcntl

                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (OSError, IOError):
                pass  # Lock will be released when file is closed


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """
    Atomically write JSON data to file.

    Args:
        path: Target file path
        data: Data to write
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic move
        tmp_path.replace(path)
    except Exception:
        # Clean up temp file on error
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def safe_read_json(path: Path) -> Dict[str, Any]:
    """
    Safely read JSON file with error handling.

    Args:
        path: File path to read

    Returns:
        Parsed JSON data or empty dict if file doesn't exist or is invalid
    """
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}

"""Windows stand-in for the POSIX `fcntl.flock` calls used by the pipeline.

Only imported when `import fcntl` fails (Windows). Provides `fcntl.flock`, `LOCK_EX`,
`LOCK_NB`, `LOCK_UN` with the same behaviour the callers rely on: an exclusive lock on a
lock file, `BlockingIOError` when LOCK_NB is set and another process holds it, and automatic
release when the process exits. Implemented with msvcrt byte-range locks on byte 0.
"""
import msvcrt
import os
import time
from types import SimpleNamespace

LOCK_SH, LOCK_EX, LOCK_NB, LOCK_UN = 1, 2, 4, 8


def _fd(target):
    return target if isinstance(target, int) else target.fileno()


def flock(target, operation):
    fd = _fd(target)
    os.lseek(fd, 0, os.SEEK_SET)  # msvcrt locks from the current position; always lock byte 0
    if operation & LOCK_UN:
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return
    while True:
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return
        except OSError:
            if operation & LOCK_NB:
                raise BlockingIOError('lock is held by another process') from None
            time.sleep(0.1)


fcntl = SimpleNamespace(flock=flock, LOCK_SH=LOCK_SH, LOCK_EX=LOCK_EX, LOCK_NB=LOCK_NB, LOCK_UN=LOCK_UN)

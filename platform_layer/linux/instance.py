"""Single instance на Linux через fcntl.flock()."""
import fcntl
import logging
import os
import tempfile

log = logging.getLogger("FixupX_Watcher")

_LOCK_PATH = os.path.join(tempfile.gettempdir(), "fixupx-watcher.lock")
_LOCK_FD = None


def acquire_single_instance() -> bool:
    """True — мы единственный экземпляр. False — уже запущено."""
    global _LOCK_FD
    try:
        _LOCK_FD = open(_LOCK_PATH, "w")
        fcntl.flock(_LOCK_FD.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _LOCK_FD.write(str(os.getpid()))
        _LOCK_FD.flush()
        return True
    except (IOError, OSError):
        log.info("Программа уже запущена (lock: %s)", _LOCK_PATH)
        return False
import win32api
import win32event
import winerror

_MUTEX_HANDLE = None


def acquire_single_instance() -> bool:
    global _MUTEX_HANDLE
    name = "Local\\FixupX_Watcher_SingleInstance"
    _MUTEX_HANDLE = win32event.CreateMutex(None, False, name)
    return win32api.GetLastError() != winerror.ERROR_ALREADY_EXISTS
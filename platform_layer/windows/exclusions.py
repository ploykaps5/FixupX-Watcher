import logging

log = logging.getLogger("FixupX_Watcher")

try:
    import win32gui
    import win32process
    import psutil
    HAS_EXCLUSIONS = True
except Exception:
    HAS_EXCLUSIONS = False
    log.info("psutil/win32 недоступны — исключения по приложениям выключены")


SUGGESTED_EXCLUSIONS = [
    "keepass.exe", "keepassxc.exe",
    "1password.exe", "1passwordforwindows.exe",
    "bitwarden.exe", "lastpass.exe", "dashlane.exe",
    "nordpass.exe", "protonpass.exe",
]


def get_foreground_app_name():
    if not HAS_EXCLUSIONS:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return None
        proc = psutil.Process(pid)
        return (proc.name() or "").lower()
    except Exception:
        return None


def is_excluded(cfg):
    if not HAS_EXCLUSIONS:
        return False
    app = get_foreground_app_name()
    if not app:
        return False
    excluded = [str(e).lower().strip() for e in cfg.get("excluded_apps", []) if e]
    return app in excluded
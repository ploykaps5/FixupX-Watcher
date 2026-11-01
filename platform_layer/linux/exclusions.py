"""Определение активного приложения на Linux."""
import logging
import os
import shutil
import subprocess

log = logging.getLogger("FixupX_Watcher")

try:
    import psutil
    _PSUTIL_OK = True
except Exception:
    _PSUTIL_OK = False

_IS_WAYLAND = bool(os.environ.get("WAYLAND_DISPLAY"))
_HAS_XDOTOOL = shutil.which("xdotool") is not None
_HAS_XPROP = shutil.which("xprop") is not None

HAS_EXCLUSIONS = _PSUTIL_OK and not _IS_WAYLAND and (_HAS_XDOTOOL or _HAS_XPROP)

if _IS_WAYLAND:
    log.info("Wayland: исключения по приложениям недоступны")
elif not _PSUTIL_OK:
    log.info("psutil не установлен — исключения по приложениям выключены")
elif not _HAS_XDOTOOL and not _HAS_XPROP:
    log.info("xdotool/xprop не найдены — исключения по приложениям выключены. "
             "Установите: sudo apt install xdotool  (или wmctrl)")


# Рекомендуемые исключения — имена процессов Linux (без .exe)
SUGGESTED_EXCLUSIONS = [
    "keepassxc", "keepass", "1password", "bitwarden", "lastpass",
    "dashlane", "nordpass", "protonpass",
    "gnome-keyring-daemon", "kwalletd5", "kwalletd6",
]


def _active_window_id():
    if not _HAS_XDOTOOL:
        return None
    try:
        out = subprocess.check_output(
            ["xdotool", "getactivewindow"],
            timeout=1, stderr=subprocess.DEVNULL,
        )
        return out.decode().strip() or None
    except Exception:
        return None


def _active_pid():
    win = _active_window_id()
    if not win:
        return None

    # 1) xdotool getwindowpid
    if _HAS_XDOTOOL:
        try:
            out = subprocess.check_output(
                ["xdotool", "getwindowpid", win],
                timeout=1, stderr=subprocess.DEVNULL,
            )
            pid = out.decode().strip()
            if pid.isdigit():
                return int(pid)
        except Exception:
            pass

    # 2) xprop _NET_WM_PID
    if _HAS_XPROP:
        try:
            out = subprocess.check_output(
                ["xprop", "-id", win, "_NET_WM_PID"],
                timeout=1, stderr=subprocess.DEVNULL,
            ).decode()
            for token in out.replace("=", " ").split():
                if token.isdigit():
                    return int(token)
        except Exception:
            pass

    return None


def get_foreground_app_name():
    """Имя процесса активного окна в нижнем регистре, или None."""
    if not HAS_EXCLUSIONS:
        return None
    pid = _active_pid()
    if not pid:
        return None
    try:
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
"""
Кроссплатформенный слой абстракции Fixup2X.

При импорте определяет ОС и подтягивает нужную реализацию.
Все остальные модули проекта импортируют платформенные функции
ТОЛЬКО отсюда — это гарантирует отсутствие прямых зависимостей
от win32 на Linux и наоборот.
"""

import sys
import logging

log = logging.getLogger("FixupX_Watcher")

if sys.platform == "win32":
    PLATFORM = "windows"
    from .windows import clipboard as _clipboard
    from .windows import notifications as _notifications
    from .windows import tray as _tray
    from .windows import hotkey as _hotkey
    from .windows import autostart as _autostart
    from .windows import instance as _instance
    from .windows import exclusions as _exclusions

elif sys.platform.startswith("linux"):
    PLATFORM = "linux"
    from .linux import clipboard as _clipboard
    from .linux import notifications as _notifications
    from .linux import tray as _tray
    from .linux import hotkey as _hotkey
    from .linux import autostart as _autostart
    from .linux import instance as _instance
    from .linux import exclusions as _exclusions

else:
    raise RuntimeError(
        f"Fixup2X: платформа {sys.platform!r} не поддерживается. "
        "Поддерживаются Windows и Linux."
    )

log.info("Платформенный слой: %s", PLATFORM)

# ---------- Clipboard ----------
read_text = _clipboard.read_text
replace_text_if_safe = _clipboard.replace_text_if_safe
read_format_list = _clipboard.read_format_list

# ---------- Notifications ----------
notify_replace = _notifications.notify_replace
notify_plain = _notifications.notify_plain
HAS_NOTIFY = getattr(_notifications, "HAS_NOTIFY", True)

# ---------- Tray ----------
TrayIcon = _tray.TrayIcon
TrayMenuItem = _tray.TrayMenuItem

# ---------- Hotkey ----------
HotkeyListener = _hotkey.HotkeyListener
HAS_HOTKEY = _hotkey.HAS_HOTKEY

# ---------- Autostart ----------
install_startup = _autostart.install_startup
uninstall_startup = _autostart.uninstall_startup
is_startup_enabled = _autostart.is_startup_enabled

# ---------- Single instance ----------
acquire_single_instance = _instance.acquire_single_instance

# ---------- Exclusions ----------
get_foreground_app_name = _exclusions.get_foreground_app_name
is_excluded = _exclusions.is_excluded
SUGGESTED_EXCLUSIONS = _exclusions.SUGGESTED_EXCLUSIONS
HAS_EXCLUSIONS = _exclusions.HAS_EXCLUSIONS
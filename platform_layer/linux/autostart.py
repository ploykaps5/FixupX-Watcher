import logging
import os
import sys

log = logging.getLogger("FixupX_Watcher")

APP_NAME = "FixupX Watcher"
DESKTOP_FILENAME = "fixupx-watcher.desktop"


def _autostart_dir() -> str:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        base = xdg
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "autostart")


def _desktop_path() -> str:
    return os.path.join(_autostart_dir(), DESKTOP_FILENAME)


def _exe_command_list():
    """Команда запуска (список argv)."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    # Не-frozen: запускаем python + скрипт
    return [sys.executable, os.path.abspath(sys.argv[0])]


def _exec_line() -> str:
    parts = _exe_command_list()
    # Экранируем кавычками — путь может содержать пробелы
    return " ".join(f'"{p}"' if " " in p else p for p in parts)


def install_startup():
    try:
        os.makedirs(_autostart_dir(), exist_ok=True)
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_NAME}\n"
            "Comment=Автозамена ссылок в буфере обмена\n"
            f"Exec={_exec_line()}\n"
            "Terminal=false\n"
            "X-GNOME-Autostart-enabled=true\n"
        )
        with open(_desktop_path(), "w", encoding="utf-8") as f:
            f.write(content)
        log.info("Автозагрузка добавлена: %s", _desktop_path())
        return True
    except Exception as e:
        log.exception("Ошибка установки автозагрузки: %s", e)
        return False


def uninstall_startup():
    try:
        p = _desktop_path()
        if os.path.exists(p):
            os.remove(p)
            log.info("Автозагрузка удалена")
        return True
    except Exception as e:
        log.exception("Ошибка удаления автозагрузки: %s", e)
        return False


def is_startup_enabled():
    return os.path.exists(_desktop_path())
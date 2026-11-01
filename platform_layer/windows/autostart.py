import logging
import os
import sys
import winreg

log = logging.getLogger("FixupX_Watcher")

APP_NAME = "FixupX_Watcher"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _exe_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pyw = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = sys.executable
    return f'"{pyw}" "{os.path.abspath(sys.argv[0])}"'


def install_startup():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                           winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _exe_command())
        winreg.CloseKey(k)
        log.info("Добавлено в автозагрузку")
        return True
    except Exception as e:
        log.exception("Ошибка автозагрузки: %s", e)
        return False


def uninstall_startup():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                           winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(k, APP_NAME)
            log.info("Удалено из автозагрузки")
        except FileNotFoundError:
            pass
        winreg.CloseKey(k)
        return True
    except Exception as e:
        log.exception("Ошибка удаления: %s", e)
        return False


def is_startup_enabled():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                           winreg.KEY_READ)
        try:
            winreg.QueryValueEx(k, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(k)
    except Exception:
        return False
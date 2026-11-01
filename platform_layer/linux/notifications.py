"""Уведомления Linux: notify-send (libnotify)."""
import logging
import shutil
import subprocess

log = logging.getLogger("FixupX_Watcher")

HAS_NOTIFY = shutil.which("notify-send") is not None
if not HAS_NOTIFY:
    log.info("notify-send не найден — уведомления отключены "
             "(установите libnotify-bin / libnotify)")


def _shorten(text, limit=180):
    text = text.replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _send(title, message, urgency="normal", timeout_ms=5000):
    if not HAS_NOTIFY:
        return
    try:
        subprocess.Popen(
            [
                "notify-send",
                "-a", "FixupX Watcher",
                "-u", urgency,
                "-t", str(timeout_ms),
                "-i", "edit-copy",
                title,
                message,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        log.exception("notify-send не удался")


def notify_replace(original, replaced, token, app_id="FixupX Watcher"):
    """
    На Linux действие «Отменить» в тосте недоступно без
    полноценного D-Bus-loop. Тост показываем, отмену можно
    сделать через окно истории (меню трея → «История замен…»).
    """
    _send("Ссылка исправлена", _shorten(replaced), urgency="normal")


def notify_plain(title, message, app_id="FixupX Watcher"):
    _send(title, _shorten(message), urgency="low", timeout_ms=4000)
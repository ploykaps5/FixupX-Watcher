import logging
import sys

log = logging.getLogger("FixupX_Watcher")

try:
    from winotify import Notification, audio
    HAS_NOTIFY = True
except Exception:
    HAS_NOTIFY = False


def _exe_path():
    return sys.executable


def _shorten(text, limit=180):
    text = text.replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"


def notify_replace(original, replaced, token, app_id="FixupX Watcher"):
    if not HAS_NOTIFY:
        return
    try:
        toast = Notification(app_id=app_id, title="Ссылка исправлена",
                             msg=_shorten(replaced), duration="short")
        try:
            toast.set_audio(audio.Default, loop=False)
        except Exception:
            pass
        launch = f'"{_exe_path()}" --undo {token}'
        try:
            toast.add_actions(label="Отменить", launch=launch)
        except Exception:
            pass
        toast.show()
    except Exception:
        log.exception("Не удалось показать уведомление")


def notify_plain(title, message, app_id="FixupX Watcher"):
    if not HAS_NOTIFY:
        return
    try:
        Notification(app_id=app_id, title=title, msg=message,
                     duration="short").show()
    except Exception:
        pass
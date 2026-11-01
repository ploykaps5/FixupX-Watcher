"""Буфер обмена для Linux (X11 + Wayland).

Логика безопасности аналогична Windows-версии:
- если в буфере есть картинки / файлы / произвольные бинарные MIME —
  замену не делаем;
- иначе — перезаписываем только текст.
"""
import logging
import os
import shutil
import subprocess

log = logging.getLogger("FixupX_Watcher")

DANGEROUS_TARGETS = {
    # картинки
    "image/png", "image/jpeg", "image/jpg", "image/gif", "image/bmp",
    "image/webp", "image/tiff", "image/avif", "image/heic",
    "image/svg+xml", "application/x-qt-image",
    # файлы из файлового менеджера
    "text/uri-list",
    "x-special/gnome-copied-files",
    "x-special/mate-copied-files",
    "application/x-kde4-urilist",
    "application/x-qt-windows-mime;value=\"FileNameW\"",
    "application/x-qt-windows-mime;value=\"FileName\"",
    "application/x-qt-windows-mime;value=\"Shell IDList Array\"",
    "application/x-qt-windows-mime;value=\"DataObject\"",
    "application/x-qt-windows-mime;value=\"Ole Private Data\"",
}

_SAFE_TEXT_TARGETS = {
    "utf8_string", "text/plain;charset=utf-8", "text/plain",
    "string", "text", "text/html", "text/rtf",
    "application/rtf",
}


def _use_wayland() -> bool:
    return bool(os.environ.get("WAYLAND_DISPLAY"))


def _which(name):
    return shutil.which(name)


def _get_targets():
    """Список MIME-типов в буфере. Пустой список — либо пусто, либо утилит нет."""
    # Wayland
    if _use_wayland() and _which("wl-paste"):
        try:
            out = subprocess.check_output(
                ["wl-paste", "--list-types"],
                timeout=2, stderr=subprocess.DEVNULL,
            )
            return [l.strip() for l in out.decode("utf-8", "replace").splitlines() if l.strip()]
        except Exception:
            return []

    # X11
    if _which("xclip"):
        try:
            out = subprocess.check_output(
                ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"],
                timeout=2, stderr=subprocess.DEVNULL,
            )
            return [l.strip() for l in out.decode("utf-8", "replace").splitlines() if l.strip()]
        except Exception:
            return []

    return []


def _is_dangerous_target(name: str) -> bool:
    n = name.lower().strip()
    if n in DANGEROUS_TARGETS:
        return True
    if n.startswith("image/"):
        return True
    # application/x-qt-image-* тоже опасны
    if n.startswith("application/x-qt-image"):
        return True
    return False


def _read_text_pyperclip():
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception:
        return None


def _write_text_pyperclip(text: str) -> bool:
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception as e:
        log.debug("pyperclip.copy не удался: %s", e)
        return False


def read_text():
    """Возвращает str или None."""
    txt = _read_text_pyperclip()
    if txt is None or txt == "":
        # pyperclip может вернуть пустую строку, если буфер пуст.
        if not _get_targets():
            return None
    return txt


def read_format_list():
    """MIME-типы для лога/диагностики. На Linux это не ID, а строки."""
    return _get_targets()


def replace_text_if_safe(new_text):
    """(success: bool, reason: str)."""
    targets = _get_targets()

    # Если буфер пустой (нечего считывать) — просто записываем текст.
    if targets:
        for t in targets:
            if _is_dangerous_target(t):
                return False, f"binary target={t!r}"

    ok = _write_text_pyperclip(new_text)
    if not ok:
        return False, "нет xclip / xsel / wl-clipboard (установите их)"
    return True, "ok"
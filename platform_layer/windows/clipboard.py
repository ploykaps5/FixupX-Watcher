import logging
import win32clipboard
import win32con

log = logging.getLogger("FixupX_Watcher")

CF_UNICODETEXT = win32con.CF_UNICODETEXT

DANGEROUS_FORMATS = {
    2, 3, 8, 9, 14, 15, 17, 0x0080,
}

DANGEROUS_FORMAT_NAMES = {
    "png", "jfif", "gif",
    "image/png", "image/jpeg", "image/gif", "image/bmp",
    "image/webp", "image/avif", "image/heic",
    "shell idlist array", "preferred dropeffect",
    "ole private data", "dataobject",
    "filegroupdescriptorw", "filecontents",
}

SAFE_FORMAT_NAMES = {
    "HTML Format", "Rich Text Format",
    "Rich Text Format Without Objects", "Rich Text Format Private",
    "text/html", "text/rtf", "text/plain",
    "UniformResourceLocatorW", "UniformResourceLocator",
}


def _get_format_name(fmt):
    if fmt < 0xC000:
        return None
    try:
        return win32clipboard.GetClipboardFormatName(fmt)
    except Exception:
        return None


def _enumerate_formats():
    formats = []
    fmt = 0
    while True:
        fmt = win32clipboard.EnumClipboardFormats(fmt)
        if fmt == 0:
            break
        formats.append(fmt)
    return formats


def _is_safe_to_modify(formats):
    for fmt in formats:
        if fmt in DANGEROUS_FORMATS:
            return False, f"binary format_id={fmt}"
        if fmt >= 0xC000:
            name = _get_format_name(fmt)
            if name and name.lower() in DANGEROUS_FORMAT_NAMES:
                return False, f"format name={name!r}"
    return True, None


def read_text():
    try:
        win32clipboard.OpenClipboard()
    except Exception:
        return None
    try:
        if not win32clipboard.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return None
        try:
            return win32clipboard.GetClipboardData(CF_UNICODETEXT)
        except Exception:
            return None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def read_format_list():
    try:
        win32clipboard.OpenClipboard()
    except Exception:
        return []
    try:
        return _enumerate_formats()
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass


def replace_text_if_safe(new_text):
    try:
        win32clipboard.OpenClipboard()
    except Exception as e:
        return False, f"open failed: {e}"

    try:
        formats = _enumerate_formats()
        if not formats:
            return False, "clipboard empty"

        safe, reason = _is_safe_to_modify(formats)
        if not safe:
            return False, reason

        saved = {}
        for f in formats:
            if f == CF_UNICODETEXT:
                continue
            try:
                saved[f] = win32clipboard.GetClipboardData(f)
            except Exception:
                log.debug("Не удалось прочитать формат %d, пропускаем", f)

        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(CF_UNICODETEXT, new_text)
        for f, data in saved.items():
            try:
                win32clipboard.SetClipboardData(f, data)
            except Exception as e:
                log.debug("Не удалось восстановить формат %d: %s", f, e)

        return True, "ok"
    except Exception as e:
        return False, f"exception: {e}"
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
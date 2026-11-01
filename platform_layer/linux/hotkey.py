"""Горячая клавиша Linux (X11). На Wayland pynput не работает —
   функция автоматически отключается."""
import logging
import os
import threading

log = logging.getLogger("FixupX_Watcher")

try:
    from pynput import keyboard
    _PYNPUT_OK = True
except Exception as e:
    _PYNPUT_OK = False
    log.info("pynput недоступен: %s", e)

# На Wayland pynput поднять глобальный слушатель не может
_IS_WAYLAND = bool(os.environ.get("WAYLAND_DISPLAY"))

HAS_HOTKEY = _PYNPUT_OK and not _IS_WAYLAND
if _PYNPUT_OK and _IS_WAYLAND:
    log.warning("Wayland обнаружен — глобальная горячая клавиша недоступна. "
                "Используйте X11 или настройте ярлык в DE.")


def parse_combination(combo: str):
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    if not parts:
        return None
    key = parts[-1]
    mods = set(parts[:-1])
    mods = {m.replace("control", "ctrl").replace("super", "cmd")
              .replace("win", "cmd") for m in mods}
    return mods, key


class HotkeyListener(threading.Thread):
    def __init__(self, callback, combination="Ctrl+Shift+X"):
        super().__init__(daemon=True)
        self.callback = callback
        parsed = parse_combination(combination)
        if parsed:
            self.mods, self.key = parsed
        else:
            self.mods, self.key = {"ctrl", "shift"}, "x"
        self.listener = None
        self._pressed = set()

    def _canon(self, key):
        if hasattr(key, "char") and key.char:
            return key.char.lower()
        if hasattr(key, "name"):
            n = key.name.lower()
            if n.startswith("ctrl"):  return "ctrl"
            if n.startswith("shift"): return "shift"
            if n.startswith("alt"):   return "alt"
            if n.startswith("cmd") or n.startswith("super") or n.startswith("win"):
                return "cmd"
            return n
        return str(key).replace("Key.", "").lower()

    def _on_press(self, key):
        try:
            k = self._canon(key)
            self._pressed.add(k)
            if self.mods.issubset(self._pressed) and self.key in self._pressed:
                self._pressed.clear()
                try:
                    self.callback()
                except Exception:
                    log.exception("Ошибка в обработчике горячей клавиши")
        except Exception:
            pass

    def _on_release(self, key):
        try:
            self._pressed.discard(self._canon(key))
        except Exception:
            pass

    def run(self):
        if not HAS_HOTKEY:
            log.info("Горячая клавиша недоступна")
            return
        log.info("Слушаем горячую клавишу: %s",
                 "+".join(sorted(self.mods)) + "+" + self.key)
        try:
            with keyboard.Listener(on_press=self._on_press,
                                   on_release=self._on_release) as l:
                self.listener = l
                l.join()
        except Exception:
            log.exception("Ошибка запуска слушателя горячей клавиши")
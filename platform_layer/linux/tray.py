"""Системный трей Linux через pystray."""
import logging

log = logging.getLogger("FixupX_Watcher")

try:
    import pystray
    from pystray import Menu, MenuItem
    HAS_TRAY = True
except Exception as e:
    HAS_TRAY = False
    log.info("pystray недоступен: %s", e)


class TrayMenuItem:
    def __init__(self, text="", callback=None, checked=None,
                 separator=False, default=False, enabled=True):
        self.text = text
        self.callback = callback
        self.checked = checked
        self.separator = separator
        self.default = default
        self.enabled = enabled


class TrayIcon:
    def __init__(self, name, icon_image_factory, tooltip, menu_factory):
        if not HAS_TRAY:
            raise RuntimeError(
                "pystray не установлен. Установите: pip install pystray"
            )
        self.name = name
        self.icon_image_factory = icon_image_factory
        self.tooltip = tooltip
        self.menu_factory = menu_factory
        self._icon = None

    # ---------- построение меню ----------
    def _make_checked(self, getter):
        def is_checked(item):
            try:
                return bool(getter())
            except Exception:
                return False
        return is_checked

    def _make_callback(self, item):
        def cb(icon, it):
            try:
                if item.callback:
                    item.callback(self, item)
            except Exception:
                log.exception("Ошибка в обработчике меню")
        return cb

    def _build_menu(self):
        items = self.menu_factory()
        entries = []
        for it in items:
            if it.separator:
                entries.append(Menu.SEPARATOR)
                continue
            entries.append(MenuItem(
                it.text or "",
                self._make_callback(it),
                checked=self._make_checked(it.checked) if it.checked else None,
                default=it.default,
                enabled=it.enabled,
            ))
        return Menu(*entries)

    # ---------- публичный API ----------
    def update_icon(self):
        if self._icon is not None:
            try:
                self._icon.icon = self.icon_image_factory()
            except Exception:
                log.exception("Не удалось обновить иконку")

    def set_tooltip(self, text):
        self.tooltip = text
        if self._icon is not None:
            try:
                self._icon.title = text
            except Exception:
                pass

    def stop(self):
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass

    # совместимость с Windows-именованием
    def quit(self):
        self.stop()

    def _remove_icon(self):
        self.stop()

    def run(self):
        img = self.icon_image_factory()
        self._icon = pystray.Icon(
            self.name,
            icon=img,
            title=self.tooltip,
            menu=self._build_menu(),
        )
        log.info("Linux-трей запущен (pystray)")
        self._icon.run()
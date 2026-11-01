"""Windows-трей: нативная иконка через win32gui (Windows-only).

Перенесено из tray_win32.py без изменения логики.
"""
import os
import tempfile
import logging

import win32api
import win32con
import win32gui
import win32process

log = logging.getLogger("FixupX_Watcher")

WM_TRAYICON = win32con.WM_USER + 20
TRAY_ICON_ID = 1
MENU_CMD_BASE = 1000


# ------------------------------------------------------------------
#  Принудительный foreground (для TrackPopupMenu)
# ------------------------------------------------------------------
def _force_foreground(hwnd):
    """
    Делает окно foreground для корректной работы TrackPopupMenu.
    Возвращает True при успехе. Никогда не бросает исключений.
    """
    # 1) обычный путь
    try:
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        pass

    # 2) трюк с AttachThreadInput
    try:
        fg = win32gui.GetForegroundWindow()
        if fg:
            fg_thread = win32process.GetWindowThreadProcessId(fg)[0]
            our_thread = win32api.GetCurrentThreadId()
            if fg_thread and fg_thread != our_thread:
                win32process.AttachThreadInput(fg_thread, our_thread, True)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    return True
                finally:
                    win32process.AttachThreadInput(fg_thread, our_thread, False)
            else:
                win32gui.SetForegroundWindow(hwnd)
                return True
    except Exception:
        pass

    # 3) крайний случай — BringWindowToTop
    try:
        win32gui.BringWindowToTop(hwnd)
    except Exception:
        pass
    return False


# ------------------------------------------------------------------
#  Пункт меню
# ------------------------------------------------------------------
class TrayMenuItem:
    def __init__(self, text="", callback=None, checked=None,
                 separator=False, default=False, enabled=True):
        self.text = text
        self.callback = callback
        self.checked = checked
        self.separator = separator
        self.default = default
        self.enabled = enabled


# ------------------------------------------------------------------
#  Иконка
# ------------------------------------------------------------------
class TrayIcon:
    def __init__(self, name, icon_image_factory, tooltip, menu_factory):
        self.name = name
        self.icon_image_factory = icon_image_factory
        self.tooltip = tooltip
        self.menu_factory = menu_factory

        self.hwnd = None
        self.hicon = None
        self._running = False
        self._menu_map = {}
        self._icon_updating = False

        self.class_name = f"FixupXWatcherTray_{os.getpid()}"
        self.taskbar_created_msg = win32gui.RegisterWindowMessage("TaskbarCreated")

        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = self.class_name
        wc.lpfnWndProc = self._wnd_proc
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        try:
            win32gui.RegisterClass(wc)
        except Exception as e:
            if "1410" not in str(e) and "already exists" not in str(e).lower():
                raise

    # ==========================================================
    #  Иконка
    # ==========================================================
    def _pil_to_hicon(self, img):
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".ico", prefix="fixupx_")
        os.close(tmp_fd)
        try:
            img.save(tmp_path, format="ICO",
                     sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (48, 48)])
            cx = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
            cy = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
            hicon = win32gui.LoadImage(
                0, tmp_path, win32con.IMAGE_ICON,
                cx, cy, win32con.LR_LOADFROMFILE,
            )
            if not hicon:
                raise RuntimeError("LoadImage вернул NULL")
            return hicon
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _load_icon(self):
        return self._pil_to_hicon(self.icon_image_factory())

    def _add_icon(self):
        if self.hicon:
            try:
                win32gui.DestroyIcon(self.hicon)
            except Exception:
                pass
        self.hicon = self._load_icon()
        nid = (
            self.hwnd, TRAY_ICON_ID,
            win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
            WM_TRAYICON, self.hicon, self.tooltip,
        )
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        log.debug("Иконка добавлена в трей")

    def _update_icon(self):
        if self._icon_updating:
            return
        self._icon_updating = True
        try:
            new_icon = self._load_icon()
            old_icon = self.hicon
            self.hicon = new_icon
            nid = (
                self.hwnd, TRAY_ICON_ID,
                win32gui.NIF_ICON | win32gui.NIF_TIP,
                WM_TRAYICON, self.hicon, self.tooltip,
            )
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
            except Exception:
                pass
            if old_icon:
                try:
                    win32gui.DestroyIcon(old_icon)
                except Exception:
                    pass
        finally:
            self._icon_updating = False

    def _remove_icon(self):
        if not self.hwnd:
            return
        try:
            nid = (self.hwnd, TRAY_ICON_ID)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        except Exception:
            try:
                nid = (self.hwnd, TRAY_ICON_ID, 0, WM_TRAYICON, 0, "")
                win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            except Exception:
                pass
        if self.hicon:
            try:
                win32gui.DestroyIcon(self.hicon)
            except Exception:
                pass
            self.hicon = None

    # ==========================================================
    #  Публичные методы
    # ==========================================================
    def update_icon(self):
        if self.hwnd and self._running:
            try:
                self._update_icon()
            except Exception:
                log.exception("Не удалось обновить иконку")

    def set_tooltip(self, text):
        self.tooltip = text
        if self.hwnd and self._running:
            nid = (
                self.hwnd, TRAY_ICON_ID,
                win32gui.NIF_TIP, WM_TRAYICON, self.hicon, self.tooltip,
            )
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
            except Exception:
                pass

    def stop(self):
        if self.hwnd:
            try:
                win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass

    def quit(self):
        log.info("Трей: запрошен выход")
        self._remove_icon()
        self._running = False
        try:
            win32gui.DestroyWindow(self.hwnd)
        except Exception:
            pass
        self.hwnd = None
        win32gui.PostQuitMessage(0)

    # ==========================================================
    #  Меню
    # ==========================================================
    def _build_popup_menu(self):
        menu = win32gui.CreatePopupMenu()
        self._menu_map.clear()

        items = self.menu_factory()
        cmd_id = MENU_CMD_BASE
        for item in items:
            if item.separator:
                win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
                continue

            flags = win32con.MF_STRING
            if not item.enabled:
                flags |= win32con.MF_GRAYED
            if item.default:
                flags |= win32con.MF_DEFAULT
            if item.checked:
                try:
                    if bool(item.checked()):
                        flags |= win32con.MF_CHECKED
                except Exception:
                    pass

            win32gui.AppendMenu(menu, flags, cmd_id, item.text or "")
            self._menu_map[cmd_id] = item
            cmd_id += 1

        return menu

    def _show_menu(self):
        log.debug("Открываем контекстное меню трея")
        menu = self._build_popup_menu()
        cmd = 0
        hwnd = self.hwnd
        try:
            try:
                _force_foreground(hwnd)
            except Exception as e:
                log.debug("force_foreground ошибка: %s", e)

            pos = win32gui.GetCursorPos()
            cmd = win32gui.TrackPopupMenu(
                menu,
                win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON
                | win32con.TPM_RETURNCMD | win32con.TPM_NONOTIFY,
                pos[0], pos[1], 0, hwnd, None,
            )
        except Exception:
            log.exception("Ошибка TrackPopupMenu")
        finally:
            try:
                win32gui.DestroyMenu(menu)
            except Exception:
                pass
            if self.hwnd:
                try:
                    win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
                except Exception:
                    pass

        if cmd > 0:
            item = self._menu_map.get(cmd)
            if item and item.callback:
                try:
                    item.callback(self, item)
                except Exception:
                    log.exception("Ошибка в обработчике меню")

    def _run_default(self):
        try:
            for item in self.menu_factory():
                if item.default and item.callback:
                    item.callback(self, item)
                    return
        except Exception:
            log.exception("Ошибка в default-обработчике")

    # ==========================================================
    #  Оконная процедура
    # ==========================================================
    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == self.taskbar_created_msg:
            log.info("Explorer перезапустился — восстанавливаем иконку")
            self._add_icon()
            return 0

        if msg == WM_TRAYICON:
            event = lparam & 0xFFFF
            log.debug("WM_TRAYICON, event=0x%04X", event)

            if event in (win32con.WM_RBUTTONUP, win32con.WM_CONTEXTMENU):
                self._show_menu()
                return 0
            if event == win32con.WM_RBUTTONDOWN:
                self._show_menu()
                return 0
            if event in (win32con.WM_LBUTTONUP, win32con.WM_LBUTTONDOWN):
                self._show_menu()
                return 0
            if event == win32con.WM_LBUTTONDBLCLK:
                self._run_default()
                return 0
            return 0

        if msg == win32con.WM_COMMAND:
            cmd = wparam & 0xFFFF
            item = self._menu_map.get(cmd)
            if item and item.callback:
                try:
                    item.callback(self, item)
                except Exception:
                    log.exception("Ошибка в обработчике WM_COMMAND")
            return 0

        if msg == win32con.WM_CLOSE:
            win32gui.DestroyWindow(hwnd)
            return 0

        if msg == win32con.WM_DESTROY:
            self._remove_icon()
            win32gui.PostQuitMessage(0)
            return 0

        if msg == win32con.WM_ENDSESSION:
            self._remove_icon()
            win32gui.PostQuitMessage(0)
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    # ==========================================================
    #  Главный цикл
    # ==========================================================
    def run(self):
        self.hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST,
            self.class_name,
            "FixupX Watcher Tray",
            win32con.WS_OVERLAPPED,
            0, 0, 1, 1,
            0, 0,
            win32api.GetModuleHandle(None),
            None,
        )
        if not self.hwnd:
            raise RuntimeError("Не удалось создать окно для трея")

        log.info("HWND трея: %s", self.hwnd)

        self._add_icon()
        self._running = True
        log.info("Нативный трей запущен")

        try:
            win32gui.PumpMessages()
        finally:
            self._running = False
            self._remove_icon()
            try:
                win32gui.DestroyWindow(self.hwnd)
            except Exception:
                pass
            self.hwnd = None
            log.info("Трей остановлен")
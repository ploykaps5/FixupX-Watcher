import os
import re
import sys
import time
import json
import logging
import threading
import uuid
from platform_layer import (
    TrayIcon, TrayMenuItem,
    read_text, replace_text_if_safe,
    notify_replace, notify_plain,
    HotkeyListener, HAS_HOTKEY,
    install_startup, uninstall_startup, is_startup_enabled,
    acquire_single_instance,
    is_excluded, get_foreground_app_name,
    PLATFORM,
)
from custom_rules import (build_domain_replace_rules, build_param_strip_rules, apply_param_strip,)
from history import History
from history_window import HistoryWindow
from onboarding import OnboardingWindow
import undo_manager
from PIL import Image, ImageDraw
from services import SERVICES, all_service_keys
from config_manager import (
    get_data_dir, load_config, save_config, is_service_enabled,
)
from url_cleaner import clean_urls_in_text
from settings_window import SettingsWindow
from custom_rules import (
    build_domain_replace_rules,
    build_param_strip_rules,
    apply_param_strip,
)
from url_expander import expand_urls_in_text

HAS_PYNPUT = HAS_HOTKEY
APP_NAME = "FixupX_Watcher"
_SHUTDOWN = False
# Папка для конфига и логов — всегда writable (%APPDATA%)
DATA_DIR = get_data_dir()
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
LOG_PATH = os.path.join(DATA_DIR, "fixupx_watcher.log")

# Папка, где лежит сам exe (или .py) — может быть в Program Files
if getattr(sys, "frozen", False):
    EXE_DIR = os.path.dirname(sys.executable)
else:
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))

# Логирование с защитой от ошибок
try:
    logging.basicConfig(
        filename=LOG_PATH, level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s", encoding="utf-8",
    )
except Exception:
    # Если всё-таки не удалось — пишем только в stderr
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
log = logging.getLogger(APP_NAME)
HISTORY = History()

# ---------- Правила ----------
def build_rules(cfg):
    """Возвращает (domain_rules, clean_domains, custom_domain_rules,
                    custom_param_rules, expand_opts)."""
    domain_rules = []
    clean_domains = {}
    if not cfg.get("enabled", True):
        return domain_rules, clean_domains, [], {}, {}

    for key in all_service_keys():
        if not is_service_enabled(cfg, key):
            continue
        svc = SERVICES[key]
        if svc.get("utm_clean"):
            clean_domains[key] = svc["domains"]
        repl = svc.get("replacement")
        if repl:
            for d in svc["domains"]:
                pat = re.compile(r'(?<![\w.-])' + re.escape(d) + r'(?=/|$|\?)')
                domain_rules.append((pat, repl))

    custom = cfg.get("custom_rules", {})
    custom_domain = build_domain_replace_rules(custom)
    custom_param = build_param_strip_rules(custom)

    expand = cfg.get("expand", {})
    return domain_rules, clean_domains, custom_domain, custom_param, expand

def fix_links(text, domain_rules, clean_domains, custom_domain_rules,
              custom_param_rules, expand_opts):
    if not text:
        return text
    result = text

    # 1) пользовательское удаление параметров — до всего остального
    if custom_param_rules:
        result = apply_param_strip(result, custom_param_rules)

    # 2) разворачивание коротких / мобильных / AMP
    if expand_opts:
        result = expand_urls_in_text(
            result,
            expand_short=bool(expand_opts.get("short_urls")),
            normalize_mobile_flag=bool(expand_opts.get("mobile_to_desktop")),
            normalize_amp_flag=bool(expand_opts.get("amp_to_canonical")),
        )

    # 3) встроенная очистка трекинга
    if clean_domains:
        result = clean_urls_in_text(result, clean_domains)

    # 4) пользовательская замена доменов
    for pat, repl in custom_domain_rules:
        result = pat.sub(repl, result)

    # 5) встроенная замена доменов
    for pat, repl in domain_rules:
        result = pat.sub(repl, result)

    return result

# ---------- Watcher ----------
class Watcher(threading.Thread):
    MAX_TEXT_LEN = 200_000
    def __init__(self):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()
        self.domain_rules = []
        self.clean_domains = {}
        self.custom_domain_rules = []
        self.custom_param_rules = {}
        self.expand_opts = {}
        self.interval = 0.4
        self.enabled = True
        self.notify_on_replace = False
        self.last_mtime_ns = 0
        self.our_last_write = None
        self.last_seen_text = None
        self.last_unsafe_reason = None

    # ---------- конфиг ----------
    def _reload(self):
        try:
            mtime = os.stat(CONFIG_PATH).st_mtime_ns
        except OSError:
            return
        if mtime == self.last_mtime_ns:
            return
        self.last_mtime_ns = mtime
        cfg = load_config()
        (self.domain_rules, self.clean_domains,
         self.custom_domain_rules, self.custom_param_rules,
         self.expand_opts) = build_rules(cfg)
        self.interval = float(cfg.get("poll_interval_sec", 0.4))
        self.enabled = bool(cfg.get("enabled", True))
        self.notify_on_replace = bool(cfg.get("notify_on_replace", False))
        log.info(
            "Конфиг обновлён: rules=%d, clean=%d, custom_dom=%d, custom_param=%d, expand=%s",
            len(self.domain_rules), len(self.clean_domains),
            len(self.custom_domain_rules), len(self.custom_param_rules),
            self.expand_opts,
        )

    def _compute(self, text):
        return fix_links(
            text,
            self.domain_rules, self.clean_domains,
            self.custom_domain_rules, self.custom_param_rules,
            self.expand_opts,
        )

    def _tick(self):
        # --- Сначала обрабатываем запросы на отмену, пришедшие из тостов ---
        signals = undo_manager.read_and_clear_signals()
        if signals:
            for token in signals:
                entry = undo_manager.pop_pending(token)
                if not entry:
                    continue
                ok, _ = replace_text_if_safe(entry["original"])
                if ok:
                    self.our_last_write = entry["original"]
                    self.last_seen_text = entry["original"]
                    log.info("Undo: восстановлено → %s", entry["original"])
                    HISTORY.add(entry["replaced"], entry["original"], app="undo")
                    break
            return

        current = read_text()
        if current is None:
            return
        if current == self.our_last_write:
            return
        if current == self.last_seen_text:
            return
        self.last_seen_text = current

        if not self.enabled:
            log.debug("Watcher выключен — пропуск")
            return
        if not (self.domain_rules or self.clean_domains
                or self.custom_domain_rules or self.custom_param_rules):
            log.debug("Нет активных правил — пропуск")
            return

        # Проверяем активное приложение — если в исключениях, молча пропускаем
        try:
            cfg_excl = load_config()
            if is_excluded(cfg_excl):
                app = get_foreground_app_name()
                log.debug("Приложение %s в исключениях — пропуск", app)
                return
        except Exception:
            pass

        if len(current) > self.MAX_TEXT_LEN:
            log.info("Текст слишком большой (%d), пропускаем", len(current))
            return
        if "http" not in current and not self.custom_param_rules:
            log.debug("В буфере нет http — пропуск")
            return

        fixed = self._compute(current)
        if fixed == current:
            log.debug("Нечего менять в: %s", current[:100])
            return

        time.sleep(0.06)
        if read_text() != current:
            log.debug("Буфер изменился во время обработки — пропуск")
            return

        # Готовим undo-токен заранее
        token = uuid.uuid4().hex[:12]
        ok, reason = replace_text_if_safe(fixed)
        if not ok:
            log.info("Пропущено (формат буфера): %s | было: %s",
                     reason, current[:80])
            if reason != self.last_unsafe_reason:
                self.last_unsafe_reason = reason
            self.our_last_write = None
            return

        self.our_last_write = fixed
        self.last_seen_text = fixed
        self.last_unsafe_reason = None
        log.info("Исправлено → %s", fixed)

        # Пишем в историю и в undo-pending
        app_name = get_foreground_app_name() or ""
        HISTORY.add(current, fixed, app=app_name)

        if self.notify_on_replace:
            undo_manager.save_pending(token, current, fixed)
            notify_replace(current, fixed, token)

    def run(self):
        log.info("Watcher запущен")
        self._reload()
        while not self.stop_event.is_set():
            try:
                self._reload()
                self._tick()
            except Exception:
                log.exception("Ошибка в watcher-цикле")
            self.stop_event.wait(self.interval)
        log.info("Watcher остановлен")

    # ---------- force (для горячей клавиши) ----------
    def force_process(self):
        current = read_text()
        if not current or "http" not in current:
            log.info("Горячая клавиша: нечего обрабатывать")
            return
        fixed = self._compute(current)
        if fixed == current:
            log.info("Горячая клавиша: нечего менять")
            return

        token = uuid.uuid4().hex[:12]
        ok, reason = replace_text_if_safe(fixed)
        if not ok:
            log.info("Горячая клавиша: пропущено (%s)", reason)
            return

        self.our_last_write = fixed
        self.last_seen_text = fixed
        log.info("Горячая клавиша: исправлено → %s", fixed)
        app_name = get_foreground_app_name() or "hotkey"
        HISTORY.add(current, fixed, app=app_name)

        if self.notify_on_replace:
            undo_manager.save_pending(token, current, fixed)
            notify_replace(current, fixed, token)

def _shorten(text, limit=180):
    text = text.replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"

# ---------- Иконка ----------
def make_icon_image(enabled=True):
    size = 64
    bg = (30, 30, 30) if enabled else (45, 45, 45)
    fg = (74, 168, 255) if enabled else (130, 130, 130)
    img = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, size - 5, size - 5], outline=fg, width=3)
    try:
        d.text((size // 2, size // 2), "fx", fill=fg, anchor="mm")
    except Exception:
        d.line([16, 16, 48, 48], fill=fg, width=4)
        d.line([48, 16, 16, 48], fill=fg, width=4)
    return img

# ---------- Меню ----------
def _is_processing_enabled():
    return bool(load_config().get("enabled", True))

def _open_path(path):
    """Открыть файл/папку в системном просмотрщике."""
    if PLATFORM == "windows":
        os.startfile(path)
    else:
        import subprocess
        subprocess.Popen(["xdg-open", path])

def on_open_settings(icon, item):
    def on_save():
        try:
            icon.icon = make_icon_image(_is_processing_enabled())
        except Exception:
            pass
    SettingsWindow(on_save=on_save).open()

def on_toggle_processing(icon, item):
    cfg = load_config()
    cfg["enabled"] = not cfg.get("enabled", True)
    save_config(cfg)
    icon.update_icon()
    log.info("Обработка ссылок: %s", cfg["enabled"])

def on_toggle_startup(icon, item):
    if is_startup_enabled():
        uninstall_startup()
    else:
        install_startup()

def on_open_config(icon, item):
    if not os.path.exists(CONFIG_PATH):
        load_config()
    _open_path(CONFIG_PATH)

def on_open_log(icon, item):
    if os.path.exists(LOG_PATH):
        _open_path(LOG_PATH)
    else:
        _open_path(DATA_DIR)

def on_open_folder(icon, item):
    _open_path(EXE_DIR)

def on_quit(icon, item):
    log.info("Выход из программы")
    # 1) Останавливаем watcher
    try:
        if watcher:
            watcher.stop_event.set()
    except Exception:
        log.exception("Ошибка остановки watcher")

    # 2) Останавливаем горячую клавишу
    try:
        if hotkey_listener and getattr(hotkey_listener, "listener", None):
            hotkey_listener.listener.stop()
    except Exception:
        log.exception("Ошибка остановки hotkey")

    # 3) Убираем иконку из трея
    try:
        icon._remove_icon()
    except Exception:
        pass

    # 4) Сбрасываем логи на диск и жёстко убиваем процесс
    try:
        logging.shutdown()
    except Exception:
        pass
    os._exit(0)

def on_open_data_folder(icon, item):
    """Открыть папку с настройками и логом (%APPDATA%)."""
    _open_path(DATA_DIR)

def on_open_exe_folder(icon, item):
    """Открыть папку, где лежит exe."""
    if getattr(sys, "frozen", False):
        _open_path(os.path.dirname(sys.executable))
    else:
        _open_path(os.path.dirname(os.path.abspath(__file__)))

def build_menu_items():
    """Возвращает список TrayMenuItem (пересобирается при каждом открытии меню)."""
    return [
        TrayMenuItem(
            "Включить обработку ссылок",
            on_toggle_processing,
            checked=_is_processing_enabled,
        ),
        TrayMenuItem(separator=True),
        TrayMenuItem("Настройки…", on_open_settings, default=True),
        TrayMenuItem(
            "Автозагрузка при входе в Windows",
            on_toggle_startup,
            checked=is_startup_enabled,
        ),
        TrayMenuItem(separator=True),
        TrayMenuItem("История замен…", on_open_history),
        TrayMenuItem(separator=True),
        TrayMenuItem("Выход", on_quit),
    ]

def handle_undo_cli(token):
    """Сигналим работающему экземпляру, что нужно откатить."""
    undo_manager.write_signal(token)
    log.info("Записан undo-сигнал: %s", token)

def handle_show_onboarding_cli():
    """Показать онбординг по запросу (например, из настроек)."""
    OnboardingWindow().open()
    # Ждём немного, чтобы окно успело открыться (для CLI-режима)
    time.sleep(2)

def on_open_history(icon, item):
    HistoryWindow(HISTORY).open()

def on_show_onboarding(icon, item):
    OnboardingWindow().open()




# ---------- main ----------
watcher = None

def main():
    global watcher, hotkey_listener
    args = list(sys.argv[1:])

    if "--install" in args:
        install_startup(); return
    if "--uninstall" in args:
        uninstall_startup(); return
    if "--status" in args:
        try:
            print("enabled:", _is_processing_enabled())
            print("startup:", is_startup_enabled())
        except Exception:
            pass
        return

    if "--undo" in args:
        i = args.index("--undo")
        if i + 1 < len(args):
            handle_undo_cli(args[i + 1])
        return

    if not acquire_single_instance():
        log.info("Программа уже запущена — выходим")
        return

    load_config()

    try:
        cfg_check = load_config()
        if not cfg_check.get("onboarding_done"):
            OnboardingWindow().open()
    except Exception:
        log.exception("Не удалось открыть онбординг")

    watcher = Watcher()
    watcher.start()

    cfg = load_config()
    hk = cfg.get("hotkey", {})
    if hk.get("enabled"):
        hotkey_listener = HotkeyListener(
            callback=watcher.force_process,
            combination=hk.get("combination", "Ctrl+Shift+X"),
        )
        hotkey_listener.start()

    icon = TrayIcon(
        name="FixupX Watcher",
        icon_image_factory=lambda: make_icon_image(_is_processing_enabled()),
        tooltip="FixupX Watcher — автозамена ссылок",
        menu_factory=build_menu_items,
    )

    log.info("Иконка в трее запущена")
    try:
        icon.run()
    finally:
        log.info("Завершение работы")
        os._exit(0)


if __name__ == "__main__":
    main()
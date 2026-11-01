import json
import os
import sys
import tempfile
from services import SERVICES, all_service_keys


APP_NAME = "FixupX Watcher"


def _exe_dir() -> str:
    """Папка, где лежит exe или скрипт. Только для чтения!"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_data_dir() -> str:
    """
    Папка для хранения config.json и логов.
    Всегда writable — APPDATA на Windows, ~/.config на Linux/macOS,
    либо temp как последний фолбэк.
    """
    # 1) Windows: %APPDATA%\FixupX Watcher\
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidate = os.path.join(appdata, APP_NAME)
    else:
        # 2) Unix-like: ~/.config/fixupx-watcher
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            candidate = os.path.join(xdg, "fixupx-watcher")
        else:
            home = os.path.expanduser("~")
            candidate = os.path.join(home, ".config", "fixupx-watcher")

    try:
        os.makedirs(candidate, exist_ok=True)
        # Проверим, что реально можно писать
        test_file = os.path.join(candidate, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return candidate
    except Exception:
        # 3) Последний фолбэк — временная папка
        fallback = os.path.join(tempfile.gettempdir(), APP_NAME)
        os.makedirs(fallback, exist_ok=True)
        return fallback

# Для обратной совместимости (используется в других модулях)
def get_app_dir() -> str:
    return get_data_dir()

DATA_DIR = get_data_dir()
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

def default_config() -> dict:
    return {
        "enabled": True,
        "poll_interval_sec": 0.4,
        "notify_on_replace": False,
        "onboarding_done": False,
        "excluded_apps": [],  # список .exe, для которых не обрабатывать
        "expand": {
            "short_urls": False,
            "mobile_to_desktop": True,
            "amp_to_canonical": False,
        },
        "hotkey": {"enabled": False, "combination": "Ctrl+Shift+X"},
        "custom_rules": {"domain_replace": {}, "param_strip": {}},
        "services": {
            k: {"enabled": SERVICES[k]["enabled_by_default"]}
            for k in all_service_keys()
        },
    }

def _deep_merge(base: dict, override: dict) -> dict:
    """base — дефолт, override — из файла. Сохраняем всё из base, что не в override."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        cfg = default_config()
        save_config(cfg)
        return cfg
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        cfg = default_config()
        save_config(cfg)
        return cfg

    merged = _deep_merge(default_config(), raw)

    # Все известные сервисы должны присутствовать
    merged.setdefault("services", {})
    for key in all_service_keys():
        merged["services"].setdefault(
            key, {"enabled": SERVICES[key]["enabled_by_default"]}
        )
    return merged

def save_config(cfg: dict) -> None:
    """Атомарная запись — сначала во временный файл, потом rename."""
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, CONFIG_PATH)

def is_service_enabled(cfg: dict, key: str) -> bool:
    return bool(cfg.get("services", {}).get(key, {}).get("enabled", False))

def toggle_service(cfg: dict, key: str, value: bool) -> dict:
    cfg.setdefault("services", {}).setdefault(key, {})["enabled"] = value
    return cfg

def export_config(target_path: str) -> None:
    cfg = load_config()
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def import_config(source_path: str) -> dict:
    with open(source_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    merged = _deep_merge(default_config(), raw)
    save_config(merged)
    return merged

def reset_to_defaults() -> dict:
    cfg = default_config()
    save_config(cfg)
    return cfg




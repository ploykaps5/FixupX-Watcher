"""
Управление отменой замен.

Кнопка «Отменить» в тосте не может напрямую менять буфер (это отдельный
процесс), поэтому она пишет сигнал в файл. Основной watcher видит сигнал
и восстанавливает оригинал сам — так мы избегаем гонки и «эхо»-замены.
"""

import json
import os
import threading
import time

from config_manager import get_data_dir

DATA_DIR = get_data_dir()
PENDING_PATH = os.path.join(DATA_DIR, "undo_pending.json")
SIGNAL_PATH = os.path.join(DATA_DIR, "undo_signal.json")

MAX_AGE_SEC = 3600  # старше часа — не отменяем
_lock = threading.Lock()


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def save_pending(token, original, replaced):
    with _lock:
        data = _read_json(PENDING_PATH) or {}
        data = _cleanup(data)
        data[token] = {"original": original, "replaced": replaced, "ts": time.time()}
        _write_json(PENDING_PATH, data)


def pop_pending(token):
    with _lock:
        data = _read_json(PENDING_PATH) or {}
        entry = data.pop(token, None)
        _write_json(PENDING_PATH, data)
        return entry


def _cleanup(data):
    now = time.time()
    return {k: v for k, v in data.items() if now - v.get("ts", 0) < MAX_AGE_SEC}


def write_signal(token):
    """Вызывается из процесса `--undo`."""
    with _lock:
        data = _read_json(SIGNAL_PATH) or []
        if token not in data:
            data.append(token)
        _write_json(SIGNAL_PATH, data)


def read_and_clear_signals():
    with _lock:
        data = _read_json(SIGNAL_PATH)
        if not data:
            return []
        _write_json(SIGNAL_PATH, [])
        return data if isinstance(data, list) else []
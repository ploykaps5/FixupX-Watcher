"""История последних замен. Хранится в history.json, максимум 50 записей."""

import json
import os
import threading
import time
from collections import deque

from config_manager import get_data_dir

HISTORY_PATH = os.path.join(get_data_dir(), "history.json")
MAX_ITEMS = 50


class History:
    def __init__(self, path=HISTORY_PATH, maxlen=MAX_ITEMS):
        self.path = path
        self._items = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                for item in raw[-MAX_ITEMS:]:
                    self._items.append(item)
        except Exception:
            pass

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(list(self._items), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add(self, original, replaced, app=""):
        with self._lock:
            self._items.appendleft({
                "ts": time.time(),
                "original": original,
                "replaced": replaced,
                "app": app or "",
            })
            self._save()

    def all(self):
        with self._lock:
            return list(self._items)

    def clear(self):
        with self._lock:
            self._items.clear()
            self._save()
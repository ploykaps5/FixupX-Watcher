"""Окно первого запуска — «Добро пожаловать»."""

import threading
import tkinter as tk
from tkinter import ttk

from services import SERVICES
from config_manager import load_config, save_config


# Какие сервисы показать в онбординге
ONBOARDING_SERVICES = [
    "x_twitter", "youtube", "instagram", "tiktok",
    "reddit", "bluesky", "facebook", "spotify",
]


class OnboardingWindow:
    _lock = threading.Lock()
    _is_open = False

    def __init__(self, on_finish=None):
        self.on_finish = on_finish
        self.root = None
        self.vars = {}

    def open(self):
        with self._lock:
            if self._is_open:
                return
            self._is_open = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            cfg = load_config()
            # Импорт UI-хелперов из окна настроек — единая тема
            from settings_window import apply_dark_theme, C

            self.root = tk.Tk()
            self.root.title("FixupX Watcher — Добро пожаловать")
            self.root.geometry("600x620")
            self.root.resizable(False, False)
            apply_dark_theme(self.root)

            # Заголовок
            head = ttk.Frame(self.root)
            head.pack(fill="x", padx=24, pady=(22, 6))
            ttk.Label(head, text="Добро пожаловать!",
                      style="H1.TLabel",
                      font=("Segoe UI", 18, "bold")).pack(anchor="w")
            ttk.Label(
                head,
                text="FixupX Watcher следит за буфером обмена и автоматически "
                     "преобразует ссылки, чтобы они красиво разворачивались "
                     "в чатах, на форумах и в соцсетях.",
                style="Dim.TLabel", wraplength=540, justify="left",
            ).pack(anchor="w", pady=(6, 0))

            ttk.Separator(self.root).pack(fill="x", padx=24, pady=14)

            # Что умеет
            ttk.Label(self.root, text="Что умеет",
                      style="H2.TLabel").pack(anchor="w", padx=24)
            bullets = [
                "• Меняет ссылки X (Twitter), Instagram, TikTok, Reddit и др. "
                "на embed-friendly фронтенды.",
                "• Убирает трекинг-параметры (utm_*, si, igsh, tag и т.д.).",
                "• Работает в фоне, не мешает и не трогает картинки и файлы "
                "в буфере.",
                "• Всё настраивается: вкл/выкл сервисы, свои правила, "
                "горячая клавиша.",
            ]
            for b in bullets:
                ttk.Label(self.root, text=b, style="Dim.TLabel",
                          wraplength=540, justify="left").pack(
                    anchor="w", padx=24, pady=(2, 0))

            ttk.Separator(self.root).pack(fill="x", padx=24, pady=14)

            # Быстрый старт
            ttk.Label(self.root, text="Что включить сразу",
                      style="H2.TLabel").pack(anchor="w", padx=24)
            ttk.Label(self.root,
                      text="Отметьте сервисы, ссылки которых нужно обрабатывать. "
                           "Потом это можно поменять в настройках.",
                      style="Dim.TLabel", wraplength=540, justify="left"
                      ).pack(anchor="w", padx=24, pady=(2, 6))

            grid = ttk.Frame(self.root)
            grid.pack(fill="x", padx=24)
            cols = 2
            for i, key in enumerate(ONBOARDING_SERVICES):
                svc = SERVICES.get(key, {})
                if not svc:
                    continue
                # По умолчанию включены: X, YouTube, Instagram, TikTok, Reddit
                default_on = key in {"x_twitter", "youtube", "instagram",
                                     "tiktok", "reddit"}
                var = tk.BooleanVar(value=default_on)
                self.vars[key] = var
                cb = ttk.Checkbutton(grid, text=svc["name"], variable=var)
                cb.grid(row=i // cols, column=i % cols, sticky="w",
                        padx=(0, 20), pady=2)

            # Кнопки
            btns = ttk.Frame(self.root)
            btns.pack(fill="x", padx=24, pady=(20, 24))
            ttk.Button(btns, text="Пропустить",
                       command=self._skip).pack(side="left")
            ttk.Button(btns, text="Готово, начать работу",
                       style="Accent.TButton",
                       command=self._finish).pack(side="right")

            self.root.protocol("WM_DELETE_WINDOW", self._finish)
            self.root.mainloop()
        except Exception:
            import traceback, logging
            logging.getLogger("FixupX_Watcher").exception(
                "Ошибка онбординга:\n%s", traceback.format_exc()
            )
        finally:
            with self._lock:
                self._is_open = False

    def _save_and_close(self, apply_services=True):
        cfg = load_config()
        if apply_services:
            for key, var in self.vars.items():
                cfg.setdefault("services", {}).setdefault(key, {})[
                    "enabled"
                ] = bool(var.get())
        cfg["onboarding_done"] = True
        save_config(cfg)
        try:
            if self.on_finish:
                self.on_finish()
        except Exception:
            pass
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass

    def _finish(self):
        self._save_and_close(apply_services=True)

    def _skip(self):
        self._save_and_close(apply_services=False)
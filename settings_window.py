import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from exclusions import SUGGESTED_EXCLUSIONS, HAS_PSUTIL
from services import SERVICES, PRESETS, all_service_keys
from config_manager import load_config, save_config, is_service_enabled
from url_cleaner import clean_urls_in_text
from tkinter import filedialog
from config_manager import (
    load_config, save_config, is_service_enabled,
    export_config, import_config, reset_to_defaults, CONFIG_PATH, DATA_DIR,
)
from exclusions import SUGGESTED_EXCLUSIONS, HAS_EXCLUSIONS
from hotkey import HAS_PYNPUT
HAS_PSUTIL = HAS_EXCLUSIONS


# ---------- Цвета ----------
C = {
    "bg":       "#1e1e1e",
    "bg_alt":   "#2a2a2a",
    "bg_alt2":  "#333333",
    "fg":       "#e8e8e8",
    "fg_dim":   "#8f8f8f",
    "accent":   "#4aa8ff",
    "accent_h": "#6cbdff",
    "border":   "#3a3a3a",
    "green":    "#5cc46e",
    "red":      "#e57373",
}


def apply_dark_theme(root):
    root.configure(bg=C["bg"])
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(".",
                    background=C["bg"], foreground=C["fg"],
                    fieldbackground=C["bg_alt"], bordercolor=C["border"],
                    lightcolor=C["border"], darkcolor=C["border"],
                    troughcolor=C["bg_alt"])
    style.configure("TFrame", background=C["bg"])
    style.configure("Card.TFrame", background=C["bg_alt"])
    style.configure("TLabel", background=C["bg"], foreground=C["fg"])
    style.configure("Dim.TLabel", foreground=C["fg_dim"])
    style.configure("H1.TLabel", font=("Segoe UI", 12, "bold"))
    style.configure("H2.TLabel", font=("Segoe UI", 10, "bold"))
    style.configure("Mono.TLabel", font=("Consolas", 9))
    style.configure("GoodMono.TLabel", font=("Consolas", 9), foreground=C["green"])
    style.configure("Accent.TLabel", foreground=C["accent"])

    style.configure("TCheckbutton",
                    background=C["bg"], foreground=C["fg"], focuscolor=C["bg"])
    style.map("TCheckbutton",
              background=[("active", C["bg"])],
              foreground=[("active", C["accent"])])

    style.configure("TButton",
                    background=C["bg_alt"], foreground=C["fg"],
                    borderwidth=1, relief="flat", padding=(10, 6))
    style.map("TButton",
              background=[("active", C["bg_alt2"]), ("pressed", C["bg_alt2"])],
              foreground=[("active", C["accent"])])

    style.configure("Accent.TButton",
                    background=C["accent"], foreground="#ffffff")
    style.map("Accent.TButton",
              background=[("active", C["accent_h"]), ("pressed", C["accent_h"])],
              foreground=[("active", "#ffffff")])

    style.configure("TNotebook", background=C["bg"], borderwidth=0)
    style.configure("TNotebook.Tab",
                    background=C["bg_alt"], foreground=C["fg_dim"],
                    padding=(16, 8), borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", C["bg"])],
              foreground=[("selected", C["accent"])])

    style.configure("TSeparator", background=C["border"])
    style.configure("TScrollbar",
                    background=C["bg_alt"], troughcolor=C["bg"],
                    bordercolor=C["bg"], arrowcolor=C["fg_dim"],
                    relief="flat")
    style.map("TScrollbar", background=[("active", C["bg_alt2"])])

    style.configure("TScale",
                    background=C["bg"], troughcolor=C["bg_alt"],
                    bordercolor=C["bg"])

    style.configure("TEntry",
                    fieldbackground=C["bg_alt"], foreground=C["fg"],
                    bordercolor=C["border"], lightcolor=C["border"],
                    darkcolor=C["border"], insertcolor=C["fg"])
    style.map("TEntry",
              fieldbackground=[("focus", C["bg_alt2"])],
              bordercolor=[("focus", C["accent"])])

# ---------- Вспомогательное ----------
def build_preview_rules(enabled_keys):
    """Правила замены доменов для превью (по текущим чекбоксам)."""
    rules = []
    for key in enabled_keys:
        svc = SERVICES.get(key, {})
        repl = svc.get("replacement")
        if not repl:
            continue
        for d in svc["domains"]:
            pat = re.compile(r'(?<![\w.-])' + re.escape(d) + r'(?=/|$|\?)')
            rules.append((pat, repl))
    return rules

def build_preview_clean_domains(enabled_keys):
    """Домены для очистки URL (только сервисы с utm_clean=True)."""
    return {
        k: SERVICES[k]["domains"]
        for k in enabled_keys
        if SERVICES[k].get("utm_clean")
    }

def preview_transform(text, enabled_keys):
    if not text:
        return ""
    # 1) очистка URL от трекинга
    domains = build_preview_clean_domains(enabled_keys)
    result = clean_urls_in_text(text, domains) if domains else text
    # 2) замена доменов
    for pat, repl in build_preview_rules(enabled_keys):
        result = pat.sub(repl, result)
    return result

# ---------- Окно ----------
class SettingsWindow:
    _lock = threading.Lock()
    _is_open = False

    def __init__(self, on_save=None):
        self.on_save = on_save
        self.root = None
        self.service_vars = {}
        self.global_var = None
        self.notify_var = None
        self.interval_var = None
        self.interval_lbl = None
        self.test_input = None
        self.test_output = None
        self.test_trace_id = None

    # ---- публичное ----
    def open(self):
        with self._lock:
            if self._is_open:
                return
            self._is_open = True
        threading.Thread(target=self._run, daemon=True).start()

    def _close_flag(self):
        with self._lock:
            self._is_open = False

    # ---- внутреннее ----
    def _run(self):
        try:
            cfg = load_config()
            self.root = tk.Tk()
            self.root.title("FixupX Watcher — Настройки")
            self.root.geometry("680x640")
            self.root.minsize(640, 560)
            apply_dark_theme(self.root)

            nb = ttk.Notebook(self.root)
            nb.pack(fill="both", expand=True, padx=12, pady=(12, 6))

            self._build_services_tab(nb, cfg)
            self._build_general_tab(nb, cfg)
            self._build_test_tab(nb, cfg)
            self._build_expand_tab(nb, cfg)
            self._build_custom_rules_tab(nb, cfg)
            self._build_hotkey_tab(nb, cfg)
            self._build_exclusions_tab(nb, cfg)

            btns = ttk.Frame(self.root)
            btns.pack(fill="x", padx=12, pady=(0, 12))
            ttk.Button(btns, text="Экспорт…", command=self._do_export).pack(side="left")
            ttk.Button(btns, text="Импорт…", command=self._do_import).pack(side="left", padx=(6, 0))
            ttk.Button(btns, text="Сбросить…", command=self._do_reset).pack(side="left", padx=(6, 0))
            ttk.Button(btns, text="Отмена", command=self.root.destroy).pack(side="right")
            ttk.Button(btns, text="Сохранить", style="Accent.TButton",
                       command=self._save).pack(side="right", padx=(0, 8))

            self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
            self.root.mainloop()
        except Exception:
            import traceback, logging
            logging.getLogger("FixupX_Watcher").exception(
                "Ошибка окна настроек:\n%s", traceback.format_exc()
            )
        finally:
            self._close_flag()

    # ======= Вкладка «Сервисы» =======
    def _build_services_tab(self, nb, cfg):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Сервисы")

        head = ttk.Frame(frame)
        head.pack(fill="x", padx=14, pady=(14, 6))
        ttk.Label(head, text="Какие ссылки обрабатывать",
                  style="H1.TLabel").pack(anchor="w")
        ttk.Label(head,
                  text="Галочка — сервис включён. Изменения применятся после «Сохранить».",
                  style="Dim.TLabel").pack(anchor="w", pady=(2, 0))

        # ---- Пресеты ----
        presets = ttk.Frame(frame)
        presets.pack(fill="x", padx=14, pady=(6, 4))
        ttk.Label(presets, text="Пресеты:", style="Dim.TLabel").pack(side="left")
        for pkey in ("only_x", "social", "media_news", "all", "none"):
            p = PRESETS[pkey]
            ttk.Button(presets, text=p["label"],
                       command=lambda k=pkey: self._apply_preset(k)
                       ).pack(side="left", padx=(6, 0))

        ttk.Separator(frame).pack(fill="x", padx=14, pady=(6, 0))

        # ---- Скролл ----
        wrap = ttk.Frame(frame)
        wrap.pack(fill="both", expand=True, padx=14, pady=(6, 12))

        canvas = tk.Canvas(wrap, borderwidth=0, highlightthickness=0,
                           bg=C["bg"])
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)

        def _on_inner_config(_):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", _on_inner_config)

        def _on_canvas_config(e):
            canvas.itemconfigure(inner_id, width=e.width)
        canvas.bind("<Configure>", _on_canvas_config)

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Группируем по категории
        categories = [
            ("social",     "Социальные сети"),
            ("video",      "Видео"),
            ("music",      "Музыка"),
            ("news",       "Новости"),
            ("shop",       "Магазины"),
            ("search",     "Поиск и карты"),
            ("reference",  "Справочники"),
        ]
        keys_by_cat = {c: [] for c, _ in categories}
        for k in all_service_keys():
            cat = SERVICES[k].get("category", "reference")
            keys_by_cat.setdefault(cat, []).append(k)

        for cat_key, cat_label in categories:
            keys = keys_by_cat.get(cat_key, [])
            if not keys:
                continue
            ttk.Label(inner, text=cat_label,
                      style="H2.TLabel").pack(anchor="w", pady=(10, 4))
            for k in keys:
                self._build_service_row(inner, k, cfg)

    def _build_service_row(self, parent, key, cfg):
        svc = SERVICES[key]
        var = tk.BooleanVar(value=is_service_enabled(cfg, key))
        self.service_vars[key] = var

        card = tk.Frame(parent, bg=C["bg_alt"], highlightthickness=1,
                        highlightbackground=C["border"])
        card.pack(fill="x", pady=4)

        inner = tk.Frame(card, bg=C["bg_alt"])
        inner.pack(fill="x", padx=10, pady=8)

        cb = tk.Checkbutton(
            inner, variable=var, bg=C["bg_alt"], activebackground=C["bg_alt"],
            selectcolor=C["bg_alt2"], highlightthickness=0, bd=0,
            fg=C["fg"], activeforeground=C["accent"], cursor="hand2",
        )
        cb.pack(side="left", anchor="n", padx=(0, 8))

        text = tk.Frame(inner, bg=C["bg_alt"])
        text.pack(side="left", fill="x", expand=True)

        tk.Label(text, text=svc["name"], bg=C["bg_alt"], fg=C["fg"],
                 font=("Segoe UI", 10, "bold"), anchor="w"
                 ).pack(anchor="w")
        tk.Label(text, text=svc["description"], bg=C["bg_alt"], fg=C["fg_dim"],
                 font=("Segoe UI", 9), wraplength=520, justify="left", anchor="w"
                 ).pack(anchor="w", pady=(1, 3))

        # предпросмотр «до → после»
        prev = tk.Frame(text, bg=C["bg_alt"])
        prev.pack(anchor="w", fill="x")
        tk.Label(prev, text=svc.get("example_from", ""),
                 bg=C["bg_alt"], fg=C["fg_dim"],
                 font=("Consolas", 8), anchor="w"
                 ).pack(anchor="w")
        arrow_text = svc.get("example_to", "")
        if arrow_text and arrow_text != svc.get("example_from"):
            tk.Label(prev, text="→ " + arrow_text,
                     bg=C["bg_alt"], fg=C["green"],
                     font=("Consolas", 8), anchor="w"
                     ).pack(anchor="w")

    def _apply_preset(self, preset_key):
        p = PRESETS[preset_key]
        target = set(p["services"])
        for key, var in self.service_vars.items():
            var.set(key in target)

    def _build_exclusions_tab(self, nb, cfg):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Исключения")

        self.excluded_apps = list(cfg.get("excluded_apps", []))

        pad = {"padx": 16, "pady": 8}
        ttk.Label(frame, text="Не обрабатывать в приложениях",
                  style="H1.TLabel").pack(anchor="w", **pad)
        ttk.Label(frame,
                  text="Если активное окно принадлежит одному из этих приложений, "
                       "буфер не изменяется. Особенно полезно для менеджеров паролей.",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16)

        if not HAS_PSUTIL:
            ttk.Label(frame,
                      text="⚠ Модуль psutil не установлен — функция недоступна.",
                      foreground="#e57373").pack(anchor="w", padx=16, pady=(8, 0))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(14, 8))

        self.excl_listbox = tk.Listbox(
            list_frame, height=10, bg=C["bg_alt"], fg=C["fg"],
            selectbackground=C["accent"], selectforeground="#fff",
            relief="flat", highlightthickness=1,
            highlightbackground=C["border"], font=("Consolas", 10),
        )
        self.excl_listbox.pack(side="left", fill="both", expand=True)
        for app in self.excluded_apps:
            self.excl_listbox.insert("end", app)

        side = ttk.Frame(list_frame)
        side.pack(side="left", fill="y", padx=(6, 0))
        ttk.Button(side, text="＋", width=3,
                   command=self._excl_add).pack(pady=1)
        ttk.Button(side, text="－", width=3,
                   command=self._excl_remove).pack(pady=1)
        ttk.Button(side, text="Рекомендуемые",
                   command=self._excl_suggested).pack(pady=(12, 1))

        ttk.Label(frame,
                  text="Указывайте имя процесса, как в системном мониторе "
                       "(Windows: с .exe, Linux: без расширения): keepassxc, "
                       "1password.exe, ...",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16, pady=(6, 0))

    def _excl_add(self):
        from tkinter import simpledialog
        name = simpledialog.askstring(
            "Добавить исключение",
            "Имя процесса (например, keepass.exe):",
        )
        if not name:
            return
        name = name.strip().lower()
        if not name:
            return
        if name not in self.excluded_apps:
            self.excluded_apps.append(name)
            self.excl_listbox.insert("end", name)

    def _excl_remove(self):
        sel = self.excl_listbox.curselection()
        if not sel:
            return
        name = self.excl_listbox.get(sel[0])
        if name in self.excluded_apps:
            self.excluded_apps.remove(name)
        self.excl_listbox.delete(sel[0])

    def _excl_suggested(self):
        added = 0
        for app in SUGGESTED_EXCLUSIONS:
            if app not in self.excluded_apps:
                self.excluded_apps.append(app)
                self.excl_listbox.insert("end", app)
                added += 1
        if added == 0:
            messagebox.showinfo("Готово", "Все рекомендуемые уже добавлены.")

    # ======= Вкладка «Разворачивание» =======
    def _build_expand_tab(self, nb, cfg):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Разворачивание")

        exp = cfg.get("expand", {})
        self.expand_short_var = tk.BooleanVar(value=bool(exp.get("short_urls")))
        self.expand_mobile_var = tk.BooleanVar(value=bool(exp.get("mobile_to_desktop", True)))
        self.expand_amp_var = tk.BooleanVar(value=bool(exp.get("amp_to_canonical")))

        pad = {"padx": 16, "pady": 8}

        ttk.Label(frame, text="Разворачивание ссылок", style="H1.TLabel").pack(
            anchor="w", **pad
        )

        ttk.Checkbutton(
            frame,
            text="Разворачивать короткие ссылки (bit.ly, t.co, tinyurl…)",
            variable=self.expand_short_var,
        ).pack(anchor="w", **pad)
        ttk.Label(frame,
                  text="Требует интернет-соединение. Может быть медленно: "
                       "каждая короткая ссылка запрашивается через HTTP HEAD.",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16)

        ttk.Separator(frame).pack(fill="x", padx=16, pady=10)

        ttk.Checkbutton(
            frame,
            text="Приводить мобильные ссылки к десктопным",
            variable=self.expand_mobile_var,
        ).pack(anchor="w", **pad)
        ttk.Label(frame,
                  text="Пример: m.youtube.com → www.youtube.com, "
                       "mobile.twitter.com → x.com, amp.reddit.com → www.reddit.com.",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16)

        ttk.Separator(frame).pack(fill="x", padx=16, pady=10)

        ttk.Checkbutton(
            frame,
            text="Убирать AMP-префиксы (google.com/amp/...)",
            variable=self.expand_amp_var,
        ).pack(anchor="w", **pad)
        ttk.Label(frame,
                  text="Пример: https://www.google.com/amp/s/example.com/article "
                       "→ https://example.com/article",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16)

    # ======= Вкладка «Горячая клавиша» =======
    def _build_hotkey_tab(self, nb, cfg):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Горячая клавиша")

        hk = cfg.get("hotkey", {})
        self.hotkey_enabled_var = tk.BooleanVar(value=bool(hk.get("enabled")))
        self.hotkey_combo_var = tk.StringVar(
            value=hk.get("combination", "Ctrl+Shift+X")
        )

        pad = {"padx": 16, "pady": 8}

        ttk.Label(frame, text="Обработка по требованию", style="H1.TLabel").pack(
            anchor="w", **pad
        )
        ttk.Label(frame,
                  text="Если автоматический watcher выключен или мешает — "
                       "можно обработать текущий буфер одним нажатием.",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16)

        cb = ttk.Checkbutton(frame, text="Включить горячую клавишу",
                             variable=self.hotkey_enabled_var)
        cb.pack(anchor="w", **pad)
        if not HAS_PYNPUT:
            cb.state(["disabled"])
            ttk.Label(frame,
                      text="⚠ Библиотека pynput не установлена — функция недоступна.",
                      foreground="#e57373").pack(anchor="w", padx=16)

        ttk.Label(frame, text="Комбинация:", style="H2.TLabel").pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        ttk.Entry(frame, textvariable=self.hotkey_combo_var, width=30).pack(
            anchor="w", padx=16
        )
        ttk.Label(frame,
                  text="Формат: Ctrl+Shift+X (модификаторы + одна буква или цифра). "
                       "Изменения применятся после перезапуска программы.",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16, pady=(6, 0))

    # ======= Вкладка «Свои правила» =======
    def _build_custom_rules_tab(self, nb, cfg):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Свои правила")

        custom = cfg.get("custom_rules", {})
        self.custom_domain_rules = dict(custom.get("domain_replace", {}))
        self.custom_param_rules = {
            k: list(v) for k, v in custom.get("param_strip", {}).items()
        }

        pad = {"padx": 16, "pady": 8}

        ttk.Label(frame, text="Свои правила", style="H1.TLabel").pack(anchor="w", **pad)
        ttk.Label(frame,
                  text="Работают поверх встроенных. Можно добавить свои замены доменов "
                       "и удаление параметров со своих сайтов.",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16)

        # --- Domain replace ---
        ttk.Label(frame, text="Замена доменов", style="H2.TLabel").pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        dr_frame = ttk.Frame(frame)
        dr_frame.pack(fill="x", padx=16)

        self.dr_listbox = tk.Listbox(
            dr_frame, height=5, bg=C["bg_alt"], fg=C["fg"],
            selectbackground=C["accent"], selectforeground="#fff",
            relief="flat", highlightthickness=1, highlightbackground=C["border"],
            font=("Consolas", 9),
        )
        self.dr_listbox.pack(side="left", fill="x", expand=True)
        for k, v in self.custom_domain_rules.items():
            self.dr_listbox.insert("end", f"{k}  →  {v}")

        dr_btns = ttk.Frame(dr_frame)
        dr_btns.pack(side="left", fill="y", padx=(6, 0))
        ttk.Button(dr_btns, text="＋", width=3,
                   command=self._dr_add).pack(pady=1)
        ttk.Button(dr_btns, text="－", width=3,
                   command=self._dr_remove).pack(pady=1)

        # --- Param strip ---
        ttk.Label(frame, text="Удалять параметры", style="H2.TLabel").pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        ttk.Label(frame,
                  text="Формат: хост (или *.хост) → параметры через запятую. "
                       "Пример: myshop.com → track, session_id",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", padx=16)

        ps_frame = ttk.Frame(frame)
        ps_frame.pack(fill="x", padx=16, pady=(4, 0))

        self.ps_listbox = tk.Listbox(
            ps_frame, height=5, bg=C["bg_alt"], fg=C["fg"],
            selectbackground=C["accent"], selectforeground="#fff",
            relief="flat", highlightthickness=1, highlightbackground=C["border"],
            font=("Consolas", 9),
        )
        self.ps_listbox.pack(side="left", fill="x", expand=True)
        for k, v in self.custom_param_rules.items():
            self.ps_listbox.insert("end", f"{k}  →  {', '.join(v)}")

        ps_btns = ttk.Frame(ps_frame)
        ps_btns.pack(side="left", fill="y", padx=(6, 0))
        ttk.Button(ps_btns, text="＋", width=3,
                   command=self._ps_add).pack(pady=1)
        ttk.Button(ps_btns, text="－", width=3,
                   command=self._ps_remove).pack(pady=1)

    def _dr_add(self):
        from tkinter import simpledialog
        src = simpledialog.askstring("Новое правило", "Исходный домен (например, nitter.net):")
        if not src:
            return
        dst = simpledialog.askstring("Новое правило", "Целевой домен (например, x.com):")
        if not dst:
            return
        errs = validate_domain_replace({src: dst})
        if errs:
            messagebox.showerror("Ошибка", "\n".join(errs))
            return
        self.custom_domain_rules[src.strip()] = dst.strip()
        self.dr_listbox.insert("end", f"{src.strip()}  →  {dst.strip()}")

    def _dr_remove(self):
        sel = self.dr_listbox.curselection()
        if not sel:
            return
        item = self.dr_listbox.get(sel[0])
        src = item.split("→")[0].strip()
        self.custom_domain_rules.pop(src, None)
        self.dr_listbox.delete(sel[0])

    def _ps_add(self):
        from tkinter import simpledialog
        host = simpledialog.askstring("Новое правило", "Хост (например, myshop.com или *.news.com):")
        if not host:
            return
        params = simpledialog.askstring("Новое правило", "Параметры через запятую (например, track, utm_*):")
        if not params:
            return
        plist = [p.strip() for p in params.split(",") if p.strip()]
        if not plist:
            return
        errs = validate_param_strip({host: plist})
        if errs:
            messagebox.showerror("Ошибка", "\n".join(errs))
            return
        self.custom_param_rules[host.strip()] = plist
        self.ps_listbox.insert("end", f"{host.strip()}  →  {', '.join(plist)}")

    def _ps_remove(self):
        sel = self.ps_listbox.curselection()
        if not sel:
            return
        item = self.ps_listbox.get(sel[0])
        host = item.split("→")[0].strip()
        self.custom_param_rules.pop(host, None)
        self.ps_listbox.delete(sel[0])

    # ======= Экспорт/импорт/сброс =======
    def _do_export(self):
        path = filedialog.asksaveasfilename(
            title="Экспорт настроек",
            defaultextension=".json",
            initialfile="fixupx-profile.json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            # Сохраним текущее состояние из формы
            self._save(silent=True)
            export_config(path)
            messagebox.showinfo("Готово", f"Настройки сохранены:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _do_import(self):
        path = filedialog.askopenfilename(
            title="Импорт настроек",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            import_config(path)
            messagebox.showinfo("Готово", "Настройки импортированы.\nПерезапустите окно настроек.")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _do_reset(self):
        if not messagebox.askyesno("Сброс",
                                   "Сбросить все настройки к значениям по умолчанию?"):
            return
        reset_to_defaults()
        messagebox.showinfo("Готово", "Сброшено.\nПерезапустите окно настроек.")
        self.root.destroy()

    # ======= Вкладка «Общие» =======
    def _build_general_tab(self, nb, cfg):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Общие")

        pad = {"padx": 16, "pady": 8}

        # Главный выключатель
        self.global_var = tk.BooleanVar(value=cfg.get("enabled", True))
        ttk.Checkbutton(frame, text="Включить обработку ссылок",
                        variable=self.global_var).pack(anchor="w", **pad)

        ttk.Separator(frame).pack(fill="x", padx=16, pady=6)

        # Интервал
        ttk.Label(frame, text="Как часто проверять буфер обмена",
                  style="H2.TLabel").pack(anchor="w", **pad)
        row = ttk.Frame(frame)
        row.pack(anchor="w", fill="x", padx=16, pady=(0, 8))
        self.interval_var = tk.DoubleVar(value=cfg.get("poll_interval_sec", 0.25))
        scale = ttk.Scale(row, from_=0.1, to=2.0, variable=self.interval_var,
                          orient="horizontal", length=340,
                          command=lambda v: self.interval_lbl.config(
                              text=f"{float(v):.2f} сек"
                          ))
        scale.pack(side="left")
        self.interval_lbl = ttk.Label(row, text=f"{self.interval_var.get():.2f} сек",
                                      width=10)
        self.interval_lbl.pack(side="left", padx=(10, 0))
        ttk.Label(frame, text="Меньше — быстрее реакция, но чуть больше нагрузка на CPU.",
                  style="Dim.TLabel").pack(anchor="w", padx=16)

        ttk.Separator(frame).pack(fill="x", padx=16, pady=12)

        # Уведомления
        self.notify_var = tk.BooleanVar(value=cfg.get("notify_on_replace", False))
        ttk.Checkbutton(frame,
                        text="Показывать уведомление Windows при каждой замене",
                        variable=self.notify_var).pack(anchor="w", **pad)

        ttk.Separator(frame).pack(fill="x", padx=16, pady=12)

        ttk.Label(frame, text="Файлы программы хранятся рядом с exe-файлом.",
                  style="Dim.TLabel").pack(anchor="w", padx=16)

        ttk.Separator(frame).pack(fill="x", padx=16, pady=12)

        ttk.Label(frame, text="Где хранятся файлы",
                  style="H2.TLabel").pack(anchor="w", padx=16, pady=(6, 4))

        from config_manager import CONFIG_PATH, DATA_DIR

        info = tk.Text(frame, height=4, wrap="word",
                       bg=C["bg_alt"], fg=C["fg_dim"],
                       relief="flat", bd=0, font=("Consolas", 9),
                       highlightthickness=1, highlightbackground=C["border"])
        info.pack(fill="x", padx=16)
        info.insert("1.0",
                    f"Настройки: {CONFIG_PATH}\n"
                    f"Папка:     {DATA_DIR}\n\n"
                    "Файлы в Program Files защищены Windows, поэтому настройки и лог "
                    "хранятся в пользовательской папке APPDATA."
                    )
        info.configure(state="disabled")

    # ======= Вкладка «Тест» =======
    def _build_test_tab(self, nb, cfg):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Тест")

        head = ttk.Frame(frame)
        head.pack(fill="x", padx=16, pady=(16, 6))
        ttk.Label(head, text="Проверка ссылки", style="H1.TLabel").pack(anchor="w")
        ttk.Label(head,
                  text="Вставьте ссылку — увидите, как она преобразуется с текущими настройками (без сохранения).",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w", pady=(2, 0))

        ttk.Label(frame, text="Исходная ссылка:",
                  style="H2.TLabel").pack(anchor="w", padx=16, pady=(14, 4))
        self.test_input = tk.Text(frame, height=3, wrap="word",
                                  bg=C["bg_alt"], fg=C["fg"],
                                  insertbackground=C["fg"],
                                  relief="flat", bd=0,
                                  font=("Consolas", 10),
                                  highlightthickness=1,
                                  highlightbackground=C["border"],
                                  highlightcolor=C["accent"])
        self.test_input.pack(fill="x", padx=16)
        self.test_input.bind("<KeyRelease>", lambda e: self._update_preview())

        ttk.Label(frame, text="Результат:",
                  style="H2.TLabel").pack(anchor="w", padx=16, pady=(14, 4))
        self.test_output = tk.Text(frame, height=3, wrap="word",
                                   bg=C["bg_alt"], fg=C["green"],
                                   insertbackground=C["fg"],
                                   relief="flat", bd=0,
                                   font=("Consolas", 10),
                                   highlightthickness=1,
                                   highlightbackground=C["border"],
                                   state="disabled")
        self.test_output.pack(fill="x", padx=16)

        # Подписи-подсказки
        hint = ttk.Frame(frame)
        hint.pack(fill="x", padx=16, pady=(10, 0))
        ttk.Label(hint,
                  text="Совет: превью использует текущее состояние галочек "
                       "на вкладке «Сервисы», даже если вы ещё не нажали «Сохранить».",
                  style="Dim.TLabel", wraplength=600, justify="left"
                  ).pack(anchor="w")

        # демо-значение
        self.test_input.insert("1.0",
            "https://fixupx.com/KrishnaBuildsAI/status/2110573696708653534?s=20\n"
            "https://youtu.be/dQw4w9WgXcQ?si=abc123&feature=share"
        )
        self._update_preview()

    def _update_preview(self):
        if self.test_input is None or self.test_output is None:
            return
        src = self.test_input.get("1.0", "end").rstrip("\n")
        enabled = [k for k, v in self.service_vars.items() if v.get()]
        out = preview_transform(src, enabled)
        self.test_output.configure(state="normal")
        self.test_output.delete("1.0", "end")
        self.test_output.insert("1.0", out)
        self.test_output.configure(state="disabled")

    # ======= Сохранение =======
    def _save(self, silent=False):
        try:
            cfg = load_config()
            cfg["enabled"] = bool(self.global_var.get())
            cfg["poll_interval_sec"] = round(float(self.interval_var.get()), 2)
            cfg["notify_on_replace"] = bool(self.notify_var.get())
            cfg["excluded_apps"] = list(self.excluded_apps)
            cfg["expand"] = {
                "short_urls": bool(self.expand_short_var.get()),
                "mobile_to_desktop": bool(self.expand_mobile_var.get()),
                "amp_to_canonical": bool(self.expand_amp_var.get()),
            }
            cfg["hotkey"] = {
                "enabled": bool(self.hotkey_enabled_var.get()),
                "combination": self.hotkey_combo_var.get().strip() or "Ctrl+Shift+X",
            }
            cfg["custom_rules"] = {
                "domain_replace": dict(self.custom_domain_rules),
                "param_strip": {k: list(v) for k, v in self.custom_param_rules.items()},
            }

            for key, var in self.service_vars.items():
                cfg.setdefault("services", {}).setdefault(key, {})["enabled"] = bool(var.get())

            save_config(cfg)
            if self.on_save:
                try:
                    self.on_save()
                except Exception:
                    pass
            if not silent:
                messagebox.showinfo("Настройки сохранены",
                                    "Изменения применены автоматически.")
                self.root.destroy()
        except Exception as e:
            if not silent:
                messagebox.showerror("Ошибка", f"Не удалось сохранить настройки:\n{e}")
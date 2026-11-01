"""Окно истории последних замен."""

import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from history import History


class HistoryWindow:
    _lock = threading.Lock()
    _is_open = False

    def __init__(self, history: History):
        self.history = history
        self.root = None

    def open(self):
        with self._lock:
            if self._is_open:
                return
            self._is_open = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            from settings_window import apply_dark_theme, C
            self.root = tk.Tk()
            self.root.title("FixupX Watcher — История замен")
            self.root.geometry("820x520")
            self.root.minsize(700, 400)
            apply_dark_theme(self.root)

            head = ttk.Frame(self.root)
            head.pack(fill="x", padx=14, pady=(14, 6))
            ttk.Label(head, text="История замен", style="H1.TLabel").pack(anchor="w")
            ttk.Label(head,
                      text="Последние 50 операций. Двойной клик — копирует исходный URL.",
                      style="Dim.TLabel").pack(anchor="w", pady=(2, 0))

            # Таблица
            cols = ("time", "app", "original", "replaced")
            tree = ttk.Treeview(self.root, columns=cols, show="headings",
                                selectmode="browse")
            tree.heading("time", text="Когда")
            tree.heading("app", text="Приложение")
            tree.heading("original", text="Было")
            tree.heading("replaced", text="Стало")
            tree.column("time", width=140, anchor="w", stretch=False)
            tree.column("app", width=140, anchor="w", stretch=False)
            tree.column("original", width=250, anchor="w")
            tree.column("replaced", width=250, anchor="w")

            style = ttk.Style(self.root)
            style.configure("Treeview",
                            background=C["bg_alt"], foreground=C["fg"],
                            fieldbackground=C["bg_alt"],
                            bordercolor=C["border"], borderwidth=0)
            style.configure("Treeview.Heading",
                            background=C["bg_alt2"], foreground=C["fg"],
                            borderwidth=0, padding=(6, 4))
            style.map("Treeview",
                      background=[("selected", C["accent"])],
                      foreground=[("selected", "#ffffff")])

            vsb = ttk.Scrollbar(self.root, orient="vertical",
                                command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            tree.pack(side="left", fill="both", expand=True,
                      padx=(14, 0), pady=(0, 14))
            vsb.pack(side="left", fill="y", pady=(0, 14))

            # Кнопки справа
            side = ttk.Frame(self.root)
            side.pack(side="right", fill="y", padx=(6, 14), pady=(0, 14))
            ttk.Button(side, text="Обновить",
                       command=lambda: self._reload(tree)).pack(fill="x", pady=(0, 6))
            ttk.Button(side, text="Копировать «Было»",
                       command=lambda: self._copy(tree, "original")).pack(fill="x", pady=2)
            ttk.Button(side, text="Копировать «Стало»",
                       command=lambda: self._copy(tree, "replaced")).pack(fill="x", pady=2)
            ttk.Separator(side, orient="horizontal").pack(fill="x", pady=10)
            ttk.Button(side, text="Очистить историю",
                       command=lambda: self._clear(tree)).pack(fill="x")

            tree.bind("<Double-1>", lambda e: self._copy(tree, "original"))

            self._tree = tree
            self._reload(tree)
            self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
            self.root.mainloop()
        except Exception:
            import traceback, logging
            logging.getLogger("FixupX_Watcher").exception(
                "Ошибка окна истории:\n%s", traceback.format_exc()
            )
        finally:
            with self._lock:
                self._is_open = False

    def _reload(self, tree):
        for row in tree.get_children():
            tree.delete(row)
        for item in self.history.all():
            when = time.strftime("%Y-%m-%d %H:%M:%S",
                                 time.localtime(item.get("ts", 0)))
            app = item.get("app", "") or "—"
            orig = (item.get("original", "") or "").replace("\n", " ")
            repl = (item.get("replaced", "") or "").replace("\n", " ")
            if len(orig) > 80:
                orig = orig[:79] + "…"
            if len(repl) > 80:
                repl = repl[:79] + "…"
            iid = tree.insert("", "end", values=(when, app, orig, repl))
            # Store full values
            tree.set(iid, "original", orig)
            tree.set(iid, "replaced", repl)

    def _copy(self, tree, field):
        sel = tree.selection()
        if not sel:
            return
        iid = sel[0]
        idx = self._index_of(iid)
        if idx is None:
            return
        items = self.history.all()
        if idx >= len(items):
            return
        value = items[idx].get(field, "")
        try:
            from clipboard_manager import replace_text_if_safe
            ok, _ = replace_text_if_safe(value)
            if ok:
                messagebox.showinfo("Готово", "Скопировано в буфер обмена.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _index_of(self, iid):
        children = self._tree.get_children()
        try:
            return children.index(iid)
        except ValueError:
            return None

    def _clear(self, tree):
        if not messagebox.askyesno("Очистка", "Удалить всю историю?"):
            return
        self.history.clear()
        self._reload(tree)
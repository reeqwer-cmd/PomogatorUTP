"""
pomogator_utp.py - Панель Инструментов Клиента
Стилизовано под тему Catppuccin Mocha (theme.py)
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from theme import Theme

# --- ОПРЕДЕЛЕНИЕ ПУТЕЙ ---
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(application_path, "my_config.json")


def load_data():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}
    return {}


def get_absolute_path(path):
    if os.path.isabs(path):
        return path
    return os.path.join(application_path, path)


def run_file(path):
    try:
        full_path = get_absolute_path(path)
        if sys.platform == "win32":
            os.startfile(full_path)
        else:
            subprocess.run(["xdg-open", full_path], check=True)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить файл:\n{e}")


def copy_file_to_clipboard(path):
    try:
        full_path = get_absolute_path(path)
        if sys.platform == "win32":
            safe_path = full_path.replace("/", "\\").replace("'", "''")
            command = f"Set-Clipboard -LiteralPath '{safe_path}'"
            subprocess.run(["powershell", "-command", command], creationflags=0x08000000, check=True)
        else:
            root.clipboard_clear()
            root.clipboard_append(full_path)
            root.update()
        messagebox.showinfo("Успешно", "Файл скопирован и готов к вставке (Ctrl+V)!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")


def create_scrollable_tab(notebook_widget, tab_name):
    tab_frame = tk.Frame(notebook_widget, bg=Theme.BG_BASE)
    notebook_widget.add(tab_frame, text=f"  {tab_name}  ")

    canvas = tk.Canvas(tab_frame, highlightthickness=0, borderwidth=0, bg=Theme.BG_BASE)
    scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
    content_frame = tk.Frame(canvas, bg=Theme.BG_BASE)

    content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")

    def configure_canvas(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", configure_canvas)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)

    def _on_mousewheel(event):
        delta = event.delta if hasattr(event, "delta") and event.delta else (120 if event.num == 4 else -120)
        canvas.yview_scroll(int(-1 * (delta / 120)), "units")

    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    return content_frame


def create_user_button_row(parent, btn_info):
    row_frame = tk.Frame(parent, bg=Theme.BG_CARD, padx=6, pady=4)
    row_frame.pack(fill=X, pady=4, padx=10)

    # Кнопка запуска
    btn = tk.Button(
        row_frame,
        text=btn_info["name"],
        bg=Theme.BG_HOVER,
        fg=Theme.FG_MAIN,
        activebackground="#585b70",
        activeforeground="#ffffff",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        anchor="w",
        padx=12,
        pady=8,
        cursor="hand2",
        command=lambda p=btn_info["path"]: run_file(p)
    )
    btn.pack(side=LEFT, expand=True, fill=X, padx=(0, 6))

    # Кнопка копирования
    copy_btn = tk.Button(
        row_frame,
        text="Копировать",
        bg=Theme.BG_SIDEBAR,
        fg=Theme.ACCENT_BTN,
        activebackground=Theme.BG_HOVER,
        activeforeground="#ffffff",
        font=("Segoe UI", 9),
        relief="flat",
        padx=12,
        pady=8,
        cursor="hand2",
        command=lambda p=btn_info["path"]: copy_file_to_clipboard(p)
    )
    copy_btn.pack(side=RIGHT, fill=Y)


# === ОСНОВА ИНТЕРФЕЙСА ===
root = tb.Window(themename="darkly")
root.title("Панель Инструментов (Catppuccin Edition)")
root.geometry("520x620")
root.minsize(440, 500)
root.configure(bg=Theme.BG_BASE)

# Настройка стилей ttk
style = ttk.Style(root)
style.theme_use("clam")
style.configure(".", background=Theme.BG_BASE, foreground=Theme.FG_MAIN, font=("Segoe UI", 10))
style.configure("TNotebook", background=Theme.BG_BASE, borderwidth=0)
style.configure("TNotebook.Tab", background=Theme.BG_SIDEBAR, foreground=Theme.FG_MUTED, padding=(14, 7), borderwidth=0)
style.map("TNotebook.Tab",
          background=[("selected", Theme.BG_CARD)],
          foreground=[("selected", Theme.ACCENT_BTN)])

data = load_data()

if not data:
    lbl_empty = tk.Label(
        root,
        text="Нет доступных инструментов.\nПожалуйста, обратитесь к администратору.",
        bg=Theme.BG_BASE,
        fg=Theme.FG_MUTED,
        font=("Segoe UI", 11),
        justify=CENTER
    )
    lbl_empty.pack(expand=True)
else:
    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, expand=True, fill=BOTH, padx=12)

    for tab_name, buttons in data.items():
        content_frame = create_scrollable_tab(notebook, tab_name)
        for btn_info in buttons:
            create_user_button_row(content_frame, btn_info)

# Нижний статус
status_bar = tk.Frame(root, bg=Theme.BG_SIDEBAR, height=26)
status_bar.pack(side=BOTTOM, fill=X)

lbl_status = tk.Label(
    status_bar,
    text="Готов к работе",
    bg=Theme.BG_SIDEBAR,
    fg=Theme.FG_MUTED,
    font=("Segoe UI", 9)
)
lbl_status.pack(side=LEFT, padx=12, pady=3)

root.mainloop()
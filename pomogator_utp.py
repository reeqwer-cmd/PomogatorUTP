"""
pomogator_utp.py - Панель Инструментов Клиента (Dark Edition)
ФИНАЛЬНАЯ ВЕРСИЯ (Fix: Arial font, стабильный скролл)
Техническая поддержка АО "Гулливер"
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# --- УМНЫЙ ПОИСК ПУТИ К ФАЙЛУ ---
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(application_path, "my_config.json")

# --- РАБОТА С ПАМЯТЬЮ (Только чтение) ---
def load_data():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}
    return {}

# --- ФУНКЦИИ ЗАПУСКА И КОПИРОВАНИЯ (с поддержкой относительных путей) ---
def get_absolute_path(path):
    if os.path.isabs(path):
        return path
    return os.path.join(application_path, path)

def run_file(path):
    try:
        full_path = get_absolute_path(path)
        os.startfile(full_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить файл:\n{e}")

def copy_file_to_clipboard(path):
    try:
        full_path = get_absolute_path(path)
        safe_path = full_path.replace("/", "\\").replace("'", "''")
        CREATE_NO_WINDOW = 0x08000000 
        command = f"Set-Clipboard -LiteralPath '{safe_path}'"
        subprocess.run(["powershell", "-command", command], 
                       creationflags=CREATE_NO_WINDOW, check=True)
        messagebox.showinfo("Успешно", "Файл скопирован и готов к вставке (Ctrl+V)!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")

# --- НАДЕЖНАЯ ВКЛАДКА СО СКРОЛЛОМ ---
def create_scrollable_tab(notebook, tab_name):
    tab_frame = tb.Frame(notebook)
    notebook.add(tab_frame, text=tab_name)
    
    canvas = tk.Canvas(tab_frame, highlightthickness=0, borderwidth=0)
    # Темный фон, чтобы избежать белых пробелов
    canvas.configure(bg="#222222")
    
    scrollbar = tb.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
    content_frame = tb.Frame(canvas)
    
    content_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
    
    def configure_canvas(event):
        canvas.itemconfig(canvas_window, width=event.width)
    canvas.bind("<Configure>", configure_canvas)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    canvas.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))

    return content_frame

# --- ОТРИСОВКА СТРОКИ С КНОПКАМИ ---
def create_user_button_row(parent, btn_info):
    row_frame = tb.Frame(parent)
    row_frame.pack(fill=X, pady=4, padx=10)
    
    btn = tb.Button(row_frame, text=btn_info["name"], bootstyle=PRIMARY, 
                    command=lambda p=btn_info["path"]: run_file(p))
    # Делаем кнопку чуть толще (ipady) для удобства нажатия
    btn.pack(side=LEFT, expand=True, fill=X, padx=(0, 5), ipady=5)
    
    copy_btn = tb.Button(row_frame, text="Копировать", bootstyle=INFO, 
                         command=lambda p=btn_info["path"]: copy_file_to_clipboard(p))
    copy_btn.pack(side=RIGHT, fill=Y)

# === ОСНОВА (ИНТЕРФЕЙС) ===
root = tb.Window(themename="darkly")
root.title("Панель Инструментов (Dark Edition)")
root.geometry("450x550")
# Жестко фиксируем безопасный шрифт от багов Tcl
root.option_add("*Font", "Arial 10") 

data = load_data()

if not data:
    tb.Label(root, text="Нет доступных инструментов.\nПожалуйста, обратитесь к администратору.", 
             font=("Arial", 12), justify=CENTER).pack(pady=50)
else:
    notebook = tb.Notebook(root)
    notebook.pack(pady=10, expand=True, fill=BOTH)

    for tab_name, buttons in data.items():
        content_frame = create_scrollable_tab(notebook, tab_name)
        for btn_info in buttons:
            create_user_button_row(content_frame, btn_info)

root.mainloop()

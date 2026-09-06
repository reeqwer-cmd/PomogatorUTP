"""
configurator.py - Админ-панель Помогатора (Dark Edition)
ФИНАЛЬНАЯ ВЕРСИЯ (Fix: Arial font, стабильный скролл)
Техническая поддержка АО "Гулливер"
"""

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import json
import os
import subprocess
import sys
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# --- УМНЫЙ ПОИСК ПУТИ К ФАЙЛУ ---
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(application_path, "my_config.json")

# --- РАБОТА С ПАМЯТЬЮ ---
def load_data():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"Общие": []}

def save_data(data_to_save):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(data_to_save, file, ensure_ascii=False, indent=4)

# --- ФУНКЦИИ ЗАПУСКА И КОПИРОВАНИЯ ---
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
        
        messagebox.showinfo("Успешно", f"Файл готов к вставке (Ctrl+V)!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")

# --- НАДЕЖНАЯ ВКЛАДКА СО СКРОЛЛОМ ---
def create_scrollable_tab(notebook, tab_name):
    tab_frame = tb.Frame(notebook)
    notebook.add(tab_frame, text=tab_name)
    
    canvas = tk.Canvas(tab_frame, highlightthickness=0, borderwidth=0)
    # Задаем темный цвет фона холсту, чтобы не было белых полос
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

def refresh_ui():
    for tab in notebook.tabs():
        notebook.forget(tab)
    
    for tab_name, buttons in data.items():
        content_frame = create_scrollable_tab(notebook, tab_name)
        for btn_info in buttons:
            create_button_row(content_frame, tab_name, btn_info)

# --- УПРАВЛЕНИЕ ВКЛАДКАМИ ---
def add_tab():
    tab_name = simpledialog.askstring("Новая вкладка", "Введите название вкладки:")
    if tab_name:
        if tab_name not in data:
            data[tab_name] = []
            save_data(data)
            refresh_ui()
        else:
            messagebox.showwarning("Внимание", "Вкладка с таким именем уже существует!")

def rename_tab():
    global data 
    try:
        current_tab_id = notebook.select()
        if not current_tab_id: return
        old_name = notebook.tab(current_tab_id, "text")
    except Exception:
        return

    new_name = simpledialog.askstring("Переименование", "Новое название вкладки:", initialvalue=old_name)
    
    if new_name and new_name != old_name:
        if new_name in data:
            messagebox.showwarning("Внимание", "Вкладка с таким именем уже существует!")
            return
        new_data = {}
        for k, v in data.items():
            if k == old_name:
                new_data[new_name] = v
            else:
                new_data[k] = v
        data = new_data
        save_data(data)
        refresh_ui()

def delete_tab():
    try:
        current_tab_id = notebook.select()
        if not current_tab_id: return
        tab_name = notebook.tab(current_tab_id, "text")
        
        if messagebox.askyesno("Удаление вкладки", f"Удалить вкладку '{tab_name}' и все её кнопки?"):
            del data[tab_name]
            save_data(data)
            refresh_ui()
    except Exception:
        pass

# --- УПРАВЛЕНИЕ КНОПКАМИ ---
def make_path_relative(file_path):
    try:
        return os.path.relpath(file_path, application_path)
    except ValueError:
        return file_path

def add_button():
    try:
        current_tab_id = notebook.select()
        if not current_tab_id: return
        current_tab = notebook.tab(current_tab_id, "text")
    except Exception:
        messagebox.showwarning("Внимание", "Сначала создайте вкладку!")
        return

    btn_name = simpledialog.askstring("Новая кнопка", "Название кнопки:")
    if not btn_name: return
    
    file_path = filedialog.askopenfilename(title="Выберите файл")
    if not file_path: return

    final_path = make_path_relative(file_path)

    data[current_tab].append({"name": btn_name, "path": final_path})
    save_data(data)
    refresh_ui()

def rename_button(tab_name, btn_info):
    new_name = simpledialog.askstring("Переименование", "Новое название кнопки:", initialvalue=btn_info["name"])
    if new_name and new_name != btn_info["name"]:
        btn_info["name"] = new_name
        save_data(data)
        refresh_ui()

def change_path(tab_name, btn_info):
    old_full = get_absolute_path(btn_info["path"])
    old_dir = os.path.dirname(old_full) if os.path.exists(old_full) else application_path

    new_path = filedialog.askopenfilename(title="Выберите новый файл", initialdir=old_dir)
    
    if new_path:
        final_path = make_path_relative(new_path)
        if final_path != btn_info["path"]:
            btn_info["path"] = final_path
            save_data(data)
            refresh_ui()

def move_button(current_tab, btn_info):
    other_tabs = [t for t in data.keys() if t != current_tab]
    if not other_tabs:
        messagebox.showinfo("Информация", "У вас только одна вкладка. Перемещать некуда!")
        return
        
    move_win = tb.Toplevel(root)
    move_win.title("Перемещение")
    move_win.geometry("300x150")
    move_win.transient(root)
    move_win.grab_set() 
    
    tb.Label(move_win, text=f"Куда переместить '{btn_info['name']}'?", font=("Arial", 10)).pack(pady=15)
    
    selected_tab = tb.StringVar(value=other_tabs[0])
    dropdown = tb.Combobox(move_win, textvariable=selected_tab, values=other_tabs, state="readonly", font=("Arial", 10))
    dropdown.pack(pady=5)
    
    def apply_move():
        target_tab = selected_tab.get()
        data[current_tab].remove(btn_info) 
        data[target_tab].append(btn_info)  
        save_data(data)
        refresh_ui()
        move_win.destroy()
        
    tb.Button(move_win, text="🚚 Переместить", bootstyle=PRIMARY, command=apply_move).pack(pady=15)

def delete_button(tab_name, btn_info):
    if messagebox.askyesno("Удаление кнопки", f"Удалить инструмент '{btn_info['name']}'?"):
        data[tab_name].remove(btn_info)
        save_data(data)
        refresh_ui()

# --- ОТРИСОВКА СТРОКИ С КНОПКАМИ ---
def create_button_row(parent, tab_name, btn_info):
    row_frame = tb.Frame(parent)
    row_frame.pack(fill=X, pady=3, padx=10)
    
    # Кнопка запуска (Основная, синяя)
    btn = tb.Button(row_frame, text=btn_info["name"], bootstyle=PRIMARY, 
                    command=lambda p=btn_info["path"]: run_file(p))
    btn.pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
    
    # Служебные кнопки с цветовым кодированием
    copy_btn = tb.Button(row_frame, text="Копия", bootstyle=INFO, 
                         command=lambda p=btn_info["path"]: copy_file_to_clipboard(p))
    copy_btn.pack(side=LEFT, fill=Y, padx=(0, 2))

    edit_btn = tb.Button(row_frame, text="Имя", bootstyle=SECONDARY, 
                         command=lambda: rename_button(tab_name, btn_info))
    edit_btn.pack(side=LEFT, fill=Y, padx=(0, 2))
    
    path_btn = tb.Button(row_frame, text="Путь", bootstyle=SECONDARY, 
                         command=lambda: change_path(tab_name, btn_info))
    path_btn.pack(side=LEFT, fill=Y, padx=(0, 2))
    
    move_btn = tb.Button(row_frame, text="Вкладка", bootstyle=WARNING, 
                         command=lambda: move_button(tab_name, btn_info))
    move_btn.pack(side=LEFT, fill=Y, padx=(0, 2))
    
    del_btn = tb.Button(row_frame, text="Удалить", bootstyle=DANGER, 
                        command=lambda: delete_button(tab_name, btn_info))
    del_btn.pack(side=RIGHT, fill=Y)

# === ОСНОВА (ИНТЕРФЕЙС) ===
root = tb.Window(themename="darkly")
root.title("Панель Администратора (Dark Edition)")
root.geometry("750x600")
root.option_add("*Font", "Arial 10") # Жесткая фиксация шрифта

data = load_data()

notebook = tb.Notebook(root)
notebook.pack(pady=10, expand=True, fill=BOTH)

control_frame = tb.Frame(root)
control_frame.pack(side=BOTTOM, fill=X, pady=10, padx=10)

tab_controls = tb.Frame(control_frame)
tab_controls.pack(fill=X, pady=2)
tb.Button(tab_controls, text="+ Новая вкладка", bootstyle=SUCCESS, command=add_tab).pack(side=LEFT, expand=True, fill=X, padx=2)
tb.Button(tab_controls, text="Изменить имя вкладки", bootstyle=WARNING, command=rename_tab).pack(side=LEFT, expand=True, fill=X, padx=2)
tb.Button(tab_controls, text="- Удалить вкладку", bootstyle=DANGER, command=delete_tab).pack(side=LEFT, expand=True, fill=X, padx=2)

tb.Button(control_frame, text="+ Добавить скрипт в эту вкладку", bootstyle=(SUCCESS, OUTLINE), command=add_button).pack(fill=X, pady=(8, 0), ipady=5)

refresh_ui()
root.mainloop()

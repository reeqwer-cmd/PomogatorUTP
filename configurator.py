"""
configurator.py - Админ-панель Помогатора
Стилизовано под тему Catppuccin Mocha (theme.py)
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
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
            return {"Общие": []}
    return {"Общие": []}


def save_data(data_to_save):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(data_to_save, file, ensure_ascii=False, indent=4)


def get_absolute_path(path):
    if os.path.isabs(path):
        return path
    return os.path.join(application_path, path)


def make_path_relative(file_path):
    try:
        return os.path.relpath(file_path, application_path)
    except ValueError:
        return file_path


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
        messagebox.showinfo("Успешно", "Файл готов к вставке (Ctrl+V)!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")


# --- ВКЛАДКА СО СКРОЛЛОМ ---
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
        tab_name = tab_name.strip()
        if tab_name and tab_name not in data:
            data[tab_name] = []
            save_data(data)
            refresh_ui()
        elif tab_name in data:
            messagebox.showwarning("Внимание", "Вкладка с таким именем уже существует!")


def rename_tab():
    global data
    try:
        current_tab_id = notebook.select()
        if not current_tab_id:
            return
        old_name = notebook.tab(current_tab_id, "text").strip()
    except Exception:
        return

    new_name = simpledialog.askstring("Переименование", "Новое название вкладки:", initialvalue=old_name)
    if new_name and new_name.strip() != old_name:
        new_name = new_name.strip()
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
        if not current_tab_id:
            return
        tab_name = notebook.tab(current_tab_id, "text").strip()

        if messagebox.askyesno("Удаление вкладки", f"Удалить вкладку '{tab_name}' и все её кнопки?"):
            del data[tab_name]
            save_data(data)
            refresh_ui()
    except Exception:
        pass


# --- УПРАВЛЕНИЕ КНОПКАМИ ---
def add_button():
    try:
        current_tab_id = notebook.select()
        if not current_tab_id:
            return
        current_tab = notebook.tab(current_tab_id, "text").strip()
    except Exception:
        messagebox.showwarning("Внимание", "Сначала создайте вкладку!")
        return

    btn_name = simpledialog.askstring("Новая кнопка", "Название кнопки:")
    if not btn_name:
        return

    file_path = filedialog.askopenfilename(title="Выберите файл")
    if not file_path:
        return

    final_path = make_path_relative(file_path)
    data[current_tab].append({"name": btn_name.strip(), "path": final_path})
    save_data(data)
    refresh_ui()


def rename_button(tab_name, btn_info):
    new_name = simpledialog.askstring("Переименование", "Новое название кнопки:", initialvalue=btn_info["name"])
    if new_name and new_name.strip() != btn_info["name"]:
        btn_info["name"] = new_name.strip()
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

    move_win = tk.Toplevel(root)
    move_win.title("Перемещение")
    move_win.geometry("320x160")
    move_win.configure(bg=Theme.BG_BASE)
    move_win.transient(root)
    move_win.grab_set()

    tk.Label(
        move_win,
        text=f"Куда переместить '{btn_info['name']}'?",
        bg=Theme.BG_BASE,
        fg=Theme.FG_MAIN,
        font=("Segoe UI", 10)
    ).pack(pady=15)

    selected_tab = tk.StringVar(value=other_tabs[0])
    dropdown = ttk.Combobox(move_win, textvariable=selected_tab, values=other_tabs, state="readonly", font=("Segoe UI", 10))
    dropdown.pack(pady=5)

    def apply_move():
        target_tab = selected_tab.get()
        data[current_tab].remove(btn_info)
        data[target_tab].append(btn_info)
        save_data(data)
        refresh_ui()
        move_win.destroy()

    tk.Button(
        move_win,
        text="🚚 Переместить",
        bg=Theme.ACCENT_BTN,
        fg=Theme.ACCENT_TEXT,
        activebackground=Theme.ACCENT_HOVER,
        activeforeground=Theme.ACCENT_TEXT,
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=5,
        command=apply_move
    ).pack(pady=12)


def delete_button(tab_name, btn_info):
    if messagebox.askyesno("Удаление кнопки", f"Удалить инструмент '{btn_info['name']}'?"):
        data[tab_name].remove(btn_info)
        save_data(data)
        refresh_ui()


# --- ОТРИСОВКА СТРОКИ С КНОПКАМИ ---
def create_button_row(parent, tab_name, btn_info):
    row_frame = tk.Frame(parent, bg=Theme.BG_CARD, padx=6, pady=4)
    row_frame.pack(fill=X, pady=3, padx=10)

    # Основная кнопка запуска
    btn = tk.Button(
        row_frame,
        text=btn_info["name"],
        bg=Theme.BG_HOVER,
        fg=Theme.FG_MAIN,
        activebackground="#585b70",
        activeforeground="#ffffff",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        anchor="w",
        padx=10,
        pady=5,
        cursor="hand2",
        command=lambda p=btn_info["path"]: run_file(p)
    )
    btn.pack(side=LEFT, expand=True, fill=X, padx=(0, 6))

    # Служебные кнопки
    copy_btn = tk.Button(
        row_frame,
        text="Копия",
        bg=Theme.BG_SIDEBAR,
        fg=Theme.INFO,
        activebackground=Theme.BG_HOVER,
        activeforeground=Theme.INFO,
        font=("Segoe UI", 8),
        relief="flat",
        padx=8,
        pady=4,
        cursor="hand2",
        command=lambda p=btn_info["path"]: copy_file_to_clipboard(p)
    )
    copy_btn.pack(side=LEFT, padx=2)

    edit_btn = tk.Button(
        row_frame,
        text="Имя",
        bg=Theme.BG_SIDEBAR,
        fg=Theme.FG_MUTED,
        activebackground=Theme.BG_HOVER,
        activeforeground=Theme.FG_MAIN,
        font=("Segoe UI", 8),
        relief="flat",
        padx=8,
        pady=4,
        cursor="hand2",
        command=lambda: rename_button(tab_name, btn_info)
    )
    edit_btn.pack(side=LEFT, padx=2)

    path_btn = tk.Button(
        row_frame,
        text="Путь",
        bg=Theme.BG_SIDEBAR,
        fg=Theme.FG_MUTED,
        activebackground=Theme.BG_HOVER,
        activeforeground=Theme.FG_MAIN,
        font=("Segoe UI", 8),
        relief="flat",
        padx=8,
        pady=4,
        cursor="hand2",
        command=lambda: change_path(tab_name, btn_info)
    )
    path_btn.pack(side=LEFT, padx=2)

    move_btn = tk.Button(
        row_frame,
        text="Вкладка",
        bg=Theme.BG_SIDEBAR,
        fg=Theme.WARNING,
        activebackground=Theme.BG_HOVER,
        activeforeground=Theme.WARNING,
        font=("Segoe UI", 8),
        relief="flat",
        padx=8,
        pady=4,
        cursor="hand2",
        command=lambda: move_button(tab_name, btn_info)
    )
    move_btn.pack(side=LEFT, padx=2)

    del_btn = tk.Button(
        row_frame,
        text="✕",
        bg=Theme.BG_SIDEBAR,
        fg=Theme.DANGER,
        activebackground=Theme.BG_HOVER,
        activeforeground=Theme.DANGER,
        font=("Segoe UI", 8, "bold"),
        relief="flat",
        padx=8,
        pady=4,
        cursor="hand2",
        command=lambda: delete_button(tab_name, btn_info)
    )
    del_btn.pack(side=RIGHT)


# === ОСНОВА ИНТЕРФЕЙСА ===
root = tb.Window(themename="darkly")
root.title("Панель Администратора (Catppuccin Edition)")
root.geometry("820x640")
root.minsize(740, 520)
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

notebook = ttk.Notebook(root)
notebook.pack(pady=10, expand=True, fill=BOTH, padx=12)

# Нижняя панель управления
control_frame = tk.Frame(root, bg=Theme.BG_SIDEBAR, padx=12, pady=10)
control_frame.pack(side=BOTTOM, fill=X)

tab_controls = tk.Frame(control_frame, bg=Theme.BG_SIDEBAR)
tab_controls.pack(fill=X, pady=2)

btn_new_tab = tk.Button(
    tab_controls,
    text="+ Новая вкладка",
    bg=Theme.BG_CARD,
    fg=Theme.SUCCESS,
    activebackground=Theme.BG_HOVER,
    activeforeground=Theme.SUCCESS,
    font=("Segoe UI", 9, "bold"),
    relief="flat",
    cursor="hand2",
    pady=5,
    command=add_tab
)
btn_new_tab.pack(side=LEFT, expand=True, fill=X, padx=3)

btn_ren_tab = tk.Button(
    tab_controls,
    text="Переименовать вкладку",
    bg=Theme.BG_CARD,
    fg=Theme.WARNING,
    activebackground=Theme.BG_HOVER,
    activeforeground=Theme.WARNING,
    font=("Segoe UI", 9),
    relief="flat",
    cursor="hand2",
    pady=5,
    command=rename_tab
)
btn_ren_tab.pack(side=LEFT, expand=True, fill=X, padx=3)

btn_del_tab = tk.Button(
    tab_controls,
    text="- Удалить вкладку",
    bg=Theme.BG_CARD,
    fg=Theme.DANGER,
    activebackground=Theme.BG_HOVER,
    activeforeground=Theme.DANGER,
    font=("Segoe UI", 9),
    relief="flat",
    cursor="hand2",
    pady=5,
    command=delete_tab
)
btn_del_tab.pack(side=LEFT, expand=True, fill=X, padx=3)

btn_add_script = tk.Button(
    control_frame,
    text="+ Добавить скрипт в эту вкладку",
    bg=Theme.ACCENT_BTN,
    fg=Theme.ACCENT_TEXT,
    activebackground=Theme.ACCENT_HOVER,
    activeforeground=Theme.ACCENT_TEXT,
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    cursor="hand2",
    pady=7,
    command=add_button
)
btn_add_script.pack(fill=X, pady=(8, 0))

refresh_ui()
root.mainloop()
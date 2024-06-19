import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
import sqlite3
import os

tasks = []
categories = []
db_path = ""

def connect_to_db():
    global conn, cursor
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT,
            completed BOOLEAN,
            category TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY,
            task_id INTEGER,
            subtask TEXT,
            completed BOOLEAN,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            category TEXT
        )
    ''')
    conn.commit()

def load_data():
    global tasks, categories
    cursor.execute('SELECT * FROM categories')
    categories = [row[1] for row in cursor.fetchall()]
    cursor.execute('SELECT * FROM tasks')
    tasks = []
    for row in cursor.fetchall():
        task_id, task, completed, category = row
        cursor.execute('SELECT * FROM subtasks WHERE task_id = ?', (task_id,))
        subtasks = [{"task": subtask, "completed": sub_completed} for _, _, subtask, sub_completed in cursor.fetchall()]
        tasks.append({"task": task, "completed": completed, "subtasks": subtasks, "category": category})
    update_category_combobox()
    update_task_list()

def save_task_to_db(task, completed, category):
    cursor.execute('INSERT INTO tasks (task, completed, category) VALUES (?, ?, ?)', (task, completed, category))
    conn.commit()
    return cursor.lastrowid

def save_subtask_to_db(task_id, subtask, completed):
    cursor.execute('INSERT INTO subtasks (task_id, subtask, completed) VALUES (?, ?, ?)', (task_id, subtask, completed))
    conn.commit()

def save_category_to_db(category):
    cursor.execute('INSERT INTO categories (category) VALUES (?)', (category,))
    conn.commit()

def add_task():
    task = task_entry.get()
    category = category_combobox.get()
    if task and category:
        task_id = save_task_to_db(task, False, category)
        tasks.append({"task": task, "completed": False, "subtasks": [], "category": category})
        update_task_list()
        task_entry.delete(0, tk.END)
        category_combobox.set('')
    else:
        messagebox.showwarning("Uyarı", "Lütfen bir görev ve kategori girin.")

def add_category():
    category = category_entry.get()
    if category and category not in categories:
        categories.append(category)
        save_category_to_db(category)
        update_category_combobox()
        category_entry.delete(0, tk.END)
    elif category in categories:
        messagebox.showwarning("Uyarı", "Bu kategori zaten mevcut")
    else:
        messagebox.showwarning("Uyarı", "Lütfen bir kategori girin.")

def update_category_combobox():
    category_combobox['values'] = categories

def update_task_list():
    task_listbox.delete(0, tk.END)
    for idx, task in enumerate(tasks):
        status = "Tamamlandı" if task["completed"] else "Tamamlanmadı"
        task_text = f"{idx + 1}. {task['task']}  ({task['category']}) - {status}"
        task_listbox.insert(tk.END, task_text)
        color = "green" if task["completed"] else "red"
        task_listbox.itemconfig(idx, {'bg': color})

def update_subtask_list(index):
    subtask_listbox.delete(0, tk.END)
    for subidx, subtask in enumerate(tasks[index]["subtasks"]):
        status = "Tamamlandı" if subtask["completed"] else "Tamamlanmadı"
        subtask_text = f"{subidx + 1}. {subtask['task']} - {status}"
        subtask_listbox.insert(tk.END, subtask_text)
        color = "green" if subtask["completed"] else "red"
        subtask_listbox.itemconfig(subidx, {'bg': color})

def complete_task():
    try:
        index = task_listbox.curselection()[0]
        tasks[index]["completed"] = True
        cursor.execute('UPDATE tasks SET completed = ? WHERE id = ?', (True, index + 1))
        conn.commit()
        update_task_list()
    except IndexError:
        messagebox.showerror("Hata", "Lütfen tamamlanacak bir görev seçin.")

def delete_task():
    try:
        index = task_listbox.curselection()[0]
        cursor.execute('DELETE FROM tasks WHERE id = ?', (index + 1,))
        cursor.execute('DELETE FROM subtasks WHERE task_id = ?', (index + 1,))
        conn.commit()
        tasks.pop(index)
        update_task_list()
        subtask_listbox.delete(0, tk.END)
    except IndexError:
        messagebox.showerror("Hata", "Lütfen silinecek bir görev seçin.")

def edit_task():
    try:
        index = task_listbox.curselection()[0]
        new_task = task_entry.get()
        new_category = category_combobox.get()
        if new_task and new_category:
            cursor.execute('UPDATE tasks SET task = ?, category = ? WHERE id = ?', (new_task, new_category, index + 1))
            conn.commit()
            tasks[index]["task"] = new_task
            tasks[index]["category"] = new_category
            update_task_list()
            task_entry.delete(0, tk.END)
            category_combobox.set('')
        else:
            messagebox.showwarning("Uyarı", "Lütfen yeni bir görev ve kategori girin.")
    except IndexError:
        messagebox.showerror("Hata", "Lütfen düzenlenecek bir görev seçin.")

def add_subtask():
    try:
        index = task_listbox.curselection()[0]
        subtask = subtask_entry.get()
        if subtask:
            save_subtask_to_db(index + 1, subtask, False)
            tasks[index]["subtasks"].append({"task": subtask, "completed": False})
            update_subtask_list(index)
            subtask_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Uyarı", "Lütfen bir alt görev girin.")
    except IndexError:
        messagebox.showerror("Hata", "Lütfen alt görev eklemek için bir ana görev seçin.")

def complete_subtask():
    try:
        task_index = task_listbox.curselection()[0]
        subtask_index = subtask_listbox.curselection()[0]
        tasks[task_index]["subtasks"][subtask_index]["completed"] = True
        cursor.execute('UPDATE subtasks SET completed = ? WHERE task_id = ? AND subtask = ?', (True, task_index + 1, tasks[task_index]["subtasks"][subtask_index]["task"]))
        conn.commit()
        update_subtask_list(task_index)
    except IndexError:
        messagebox.showerror("Hata", "Lütfen tamamlanacak bir alt görev seçin.")

def delete_subtask():
    try:
        task_index = task_listbox.curselection()[0]
        subtask_index = subtask_listbox.curselection()[0]
        cursor.execute('DELETE FROM subtasks WHERE task_id = ? AND subtask = ?', (task_index + 1, tasks[task_index]["subtasks"][subtask_index]["task"]))
        conn.commit()
        tasks[task_index]["subtasks"].pop(subtask_index)
        update_subtask_list(task_index)
    except IndexError:
        messagebox.showerror("Hata", "Lütfen silinecek bir alt görev seçin.")

def select_db():
    global db_path
    db_path = filedialog.askopenfilename(defaultextension=".db", filetypes=[("SQLite Database", ".db"), ("All Files", ".*")])
    if db_path:
        connect_to_db()
        load_data()

def create_db():
    global db_path
    db_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", ".db"), ("All Files", ".*")])
    if db_path:
        connect_to_db()
        load_data()

root = tk.Tk()
root.title("To-Do List Uygulaması")

# Database selection
db_button_frame = tk.Frame(root)
db_button_frame.pack(pady=10)

select_db_button = tk.Button(db_button_frame, text="Kullanıcı Seç", command=select_db)
select_db_button.pack(side=tk.LEFT, padx=5)

create_db_button = tk.Button(db_button_frame, text="Yeni Kullanıcı Oluştur", command=create_db)
create_db_button.pack(side=tk.LEFT, padx=5)

task_label = tk.Label(root, text="Görev:")
task_label.pack(pady=5)
task_entry = tk.Entry(root, width=50)
task_entry.pack(pady=5)

category_label = tk.Label(root, text="Kategori:")
category_label.pack(pady=5)
category_combobox = ttk.Combobox(root, width=50)
category_combobox.pack(pady=5)

add_button = tk.Button(root, text="Görev Ekle", command=add_task)
add_button.pack(pady=5)

task_listbox = tk.Listbox(root, width=50, height=10)
task_listbox.pack(pady=10)

complete_button = tk.Button(root, text="Görevi Tamamla", command=complete_task)
complete_button.pack(pady=5)

delete_button = tk.Button(root, text="Görev Sil", command=delete_task)
delete_button.pack(pady=5)

edit_button = tk.Button(root, text="Görevi Düzenle", command=edit_task)
edit_button.pack(pady=5)

category_entry_label = tk.Label(root, text="Yeni Kategori:")
category_entry_label.pack(pady=5)
category_entry = tk.Entry(root, width=50)
category_entry.pack(pady=5)

add_category_button = tk.Button(root, text="Kategori Ekle", command=add_category)
add_category_button.pack(pady=5)

subtask_listbox_label = tk.Label(root, text="Alt Görevler:")
subtask_listbox_label.pack(pady=5)
subtask_listbox = tk.Listbox(root, width=50, height=10)
subtask_listbox.pack(pady=10)

subtask_entry_label = tk.Label(root, text="Alt Görev:")
subtask_entry_label.pack(pady=5)
subtask_entry = tk.Entry(root, width=50)
subtask_entry.pack(pady=5)

add_subtask_button = tk.Button(root, text="Alt Görev Ekle", command=add_subtask)
add_subtask_button.pack(pady=5)

complete_subtask_button = tk.Button(root, text="Alt Görevi Tamamla", command=complete_subtask)
complete_subtask_button.pack(pady=5)

delete_subtask_button = tk.Button(root, text="Alt Görevi Sil", command=delete_subtask)
delete_subtask_button.pack(pady=5)

def on_task_select(event):
    try:
        index = task_listbox.curselection()[0]
        update_subtask_list(index)
    except IndexError:
        pass

task_listbox.bind("<<ListboxSelect>>", on_task_select)
root.mainloop()

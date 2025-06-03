import tkinter as tk
from tkinter import messagebox
import sys
import os
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))
from database import get_user, register_user

def open_admin_window(user):
    import admin_window
    admin_window.open_admin_interface(user)

def open_trainer_window(user):
    import trainer_window
    trainer_window.open_trainer_interface(user)

def login():
    username = entry_username.get()
    password = entry_password.get()

    user = get_user(username, password)
    if user:
        messagebox.showinfo("Успіх", f"Вхід виконано! Ваша роль: {user[3]}")
        root.withdraw()
        if user[3] == 'admin':
            open_admin_window(user)
        elif user[3] == 'trainer':
            open_trainer_window(user)
    else:
        messagebox.showerror("Помилка", "Невірний логін або пароль")

def open_register_window():
    register_window = tk.Toplevel(root)
    register_window.title("Реєстрація")
    register_window.geometry("400x500")
    register_window.configure(bg='#34495e')

    tk.Label(register_window, text="Реєстрація", font=("Arial", 24), bg='#34495e', fg='white').pack(pady=10)

    tk.Label(register_window, text="Введіть логін:", font=("Arial", 14), bg='#34495e', fg='white', anchor="w").pack(fill="x", padx=20)
    entry_new_username = tk.Entry(register_window, font=("Arial", 14), width=30)
    entry_new_username.pack(pady=5, padx=20)

    tk.Label(register_window, text="Введіть пароль:", font=("Arial", 14), bg='#34495e', fg='white', anchor="w").pack(fill="x", padx=20)
    entry_new_password = tk.Entry(register_window, font=("Arial", 14), width=30, show="*")
    entry_new_password.pack(pady=5, padx=20)

    tk.Label(register_window, text="Повторіть пароль:", font=("Arial", 14), bg='#34495e', fg='white', anchor="w").pack(fill="x", padx=20)
    entry_repeat_password = tk.Entry(register_window, font=("Arial", 14), width=30, show="*")
    entry_repeat_password.pack(pady=5, padx=20)

    tk.Label(register_window, text="Оберіть роль:", font=("Arial", 14), bg='#34495e', fg='white', anchor="w").pack(fill="x", padx=20)

    role_var = tk.StringVar(value="")
    frame_roles = tk.Frame(register_window, bg='#34495e')
    frame_roles.pack(pady=5)

    tk.Radiobutton(frame_roles, text="Адмін", font=("Arial", 12), variable=role_var, value="admin", bg='#34495e', fg='white', selectcolor='#2c3e50').pack(side="left", padx=10)
    tk.Radiobutton(frame_roles, text="Тренер", font=("Arial", 12), variable=role_var, value="trainer", bg='#34495e', fg='white', selectcolor='#2c3e50').pack(side="left", padx=10)

    def is_password_strong(password):
        if len(password) < 6:
            return False, "Пароль має містити щонайменше 6 символів!"
        if not re.search(r"[A-Za-z]", password):
            return False, "Пароль має містити хоча б одну літеру!"
        if not re.search(r"[0-9]", password):
            return False, "Пароль має містити хоча б одну цифру!"
        return True, ""

    def register():
        new_username = entry_new_username.get()
        new_password = entry_new_password.get()
        repeat_password = entry_repeat_password.get()
        selected_role = role_var.get()

        if not new_username or not new_password or not repeat_password:
            messagebox.showerror("Помилка", "Заповніть всі поля!")
            return

        if not re.match(r"^[A-Za-z0-9_]{4,}$", new_username):
            messagebox.showerror("Помилка",
                                 "Ім’я користувача має містити щонайменше 4 символи і складатися лише з літер, цифр або '_'!")
            return

        if new_password != repeat_password:
            messagebox.showerror("Помилка", "Паролі не співпадають!")
            return

        valid, message = is_password_strong(new_password)
        if not valid:
            messagebox.showerror("Слабкий пароль", message)
            return

        if not selected_role:
            messagebox.showerror("Помилка", "Оберіть роль!")
            return

        if register_user(new_username, new_password, selected_role):
            messagebox.showinfo("Успіх", "Акаунт створено!")
            register_window.destroy()
        else:
            messagebox.showerror("Помилка", "Користувач уже існує!")

    tk.Button(register_window, text="Зареєструватися", font=("Arial", 14), bg='#27ae60', fg='white', width=20, command=register).pack(pady=20)

global root, entry_username, entry_password
root = tk.Tk()
root.title("Авторизація")
root.geometry("800x600")
root.configure(bg='#2c3e50')

frame = tk.Frame(root, bg='#34495e', padx=50, pady=50)
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

tk.Label(frame, text="Логін:", font=("Arial", 20), bg='#34495e', fg='white').pack(pady=10)
entry_username = tk.Entry(frame, font=("Arial", 20), width=20)
entry_username.pack(pady=10)

tk.Label(frame, text="Пароль:", font=("Arial", 20), bg='#34495e', fg='white').pack(pady=10)
entry_password = tk.Entry(frame, font=("Arial", 20), width=20, show="*")
entry_password.pack(pady=10)

tk.Button(frame, text="Увійти", font=("Arial", 18), bg='#27ae60', fg='white', width=15, command=login).pack(pady=10)
tk.Button(frame, text="Зареєструватися", font=("Arial", 14), bg='#2980b9', fg='white', width=25,
          command=open_register_window).pack(pady=10)

root.bind("<Escape>", lambda event: root.destroy())
root.mainloop()
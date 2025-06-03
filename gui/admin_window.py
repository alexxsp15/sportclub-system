import os
import sys
import unicodedata

import tkinter as tk
from tkinter import ttk, messagebox

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))

from database.gym import (
    add_client_to_db,
    get_all_clients_with_details,
    was_client_present_today,
    delete_client_by_id
)
from attendance_window import open_attendance_calendar_window
from edit_client_window import open_edit_client_details

def open_admin_interface(user):
    username = user[1]
    user_id = user[0]

    admin_window = tk.Toplevel()
    admin_window.title("Панель адміністратора")
    admin_window.state('zoomed')
    admin_window.configure(bg='#2c3e50')
    admin_window.option_add("*Font", "Arial 12")

    main_frame = tk.Frame(admin_window, bg='#2c3e50')
    main_frame.pack(expand=True, fill="both")

    title_label = tk.Label(
        main_frame,
        text="Панель адміністратора",
        font=("Arial", 50, "bold"),
        fg="white",
        bg="#2c3e50"
    )
    title_label.pack(pady=(80, 5))  # Раніше було (40, 5)

    welcome_label = tk.Label(
        main_frame,
        text=f"Вітаємо, {username}!",
        font=("Arial", 35),
        fg="white",
        bg="#2c3e50"
    )
    welcome_label.pack(pady=(0, 40))  # Було (0, 30)

    icon_frame = tk.Frame(main_frame, bg='#2c3e50')
    icon_frame.place(relx=0.5, rely=0.5, anchor="center")

    btn_style = {
        "font": ("Arial", 70),
        "bg": 'white',
        "fg": '#2c3e50',
        "width": 4,
        "height": 2,
        "relief": "flat",
        "bd": 0,
        "highlightthickness": 0
    }

    def rounded_button_container(master):
        frame = tk.Frame(master, bg='#2c3e50')
        container = tk.Frame(frame, bg='white', width=180, height=180)
        container.pack_propagate(False)
        container.pack(padx=20, pady=10)
        container.configure(highlightbackground="white", highlightthickness=1)
        return frame, container

    def on_enter(e, btn):
        btn['bg'] = '#bdc3c7'

    def on_leave(e, btn):
        btn['bg'] = 'white'

    def open_add_client_window():
        add_win = tk.Toplevel(admin_window)
        add_win.title("Додавання нового клієнта")
        add_win.geometry("500x500")
        add_win.configure(bg="#34495e")

        tk.Label(add_win, text="Новий клієнт", font=("Arial", 20, "bold"), bg="#34495e", fg="white").pack(pady=20)

        def create_labeled_entry(label_text):
            tk.Label(add_win, text=label_text, font=("Arial", 14), bg="#34495e", fg="white").pack(pady=(10, 0))
            entry = tk.Entry(add_win, font=("Arial", 14), width=40)
            entry.pack(pady=5)
            return entry

        entry_name = create_labeled_entry("Повне ім’я:")
        entry_phone = create_labeled_entry("Номер телефону:")
        entry_email = create_labeled_entry("Email:")

        def save_client():
            import re

            name = entry_name.get()
            phone = entry_phone.get()
            email = entry_email.get()

            if not name or not phone or not email:
                messagebox.showwarning("Попередження", "Заповніть усі поля!")
                return

            if not re.match(r"^[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ'’\-\s]{2,}$", name.strip()):
                messagebox.showerror("Помилка", "Ім’я повинно бути українською та містити щонайменше 2 літери.")
                return

            if not re.match(r"^(\+380\d{9}|0\d{9})$", phone.strip()):
                messagebox.showerror("Помилка",
                                     "Невірний формат телефону. Використовуйте формат +380XXXXXXXXX або 0XXXXXXXXX.")
                return

            if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email.strip()):
                messagebox.showerror("Помилка", "Невірний формат email.")
                return

            if add_client_to_db(name, phone, email, user_id):
                messagebox.showinfo("Успіх", "Клієнта додано!")
                add_win.destroy()
            else:
                messagebox.showerror("Помилка", "Не вдалося додати клієнта.")

        tk.Button(add_win, text="Зберегти", font=("Arial", 16), bg="#27ae60", fg="white", padx=20, pady=10, command=save_client).pack(pady=30)

    def open_attendance_management_window():

        attend_win = tk.Toplevel()
        attend_win.title("Менеджмент відвідуваності")
        attend_win.geometry("1000x500")
        attend_win.configure(bg='#34495e')

        top_frame = tk.Frame(attend_win, bg='#34495e')
        top_frame.pack(fill='x', padx=20, pady=(10, 0))

        search_var = tk.StringVar()

        tk.Label(top_frame, text='🔍 Пошук:', font=('Arial', 12), bg='#34495e', fg='white').pack(side='left')
        tk.Entry(top_frame, textvariable=search_var, font=('Arial', 12), width=30).pack(side='left', padx=(5, 20))
        tk.Label(top_frame, text="Менеджмент відвідуваності", font=("Arial", 20, "bold"),
                 bg='#34495e', fg='white').pack(side='left')

        columns = ('id_clients', 'full_name', 'phone', 'email', 'registration_date',
                   'trainer_name', 'subscription_type', 'payment', 'attendance', 'present_today')

        headers = {
            'id_clients': 'ID',
            'full_name': "Ім'я",
            'phone': 'Телефон',
            'email': 'Email',
            'registration_date': 'Дата реєстрації',
            'trainer_name': "Ім'я тренера",
            'subscription_type': 'Тип підписки',
            'payment': 'Оплата',
            'attendance': 'Відвідування',
            'present_today': 'Сьогодні'
        }

        tree = ttk.Treeview(attend_win, columns=columns, show='headings')
        sort_directions = {}
        all_clients_data = []

        def try_cast(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return str(val).lower()

        def sort_by_column(col):
            col_index = columns.index(col)
            reverse = sort_directions.get(col, False)
            sort_directions[col] = not reverse

            filtered_data = []
            query = search_var.get().lower()
            for row in all_clients_data:
                visible = any(query in str(val).lower() for i, val in enumerate(row) if columns[i] != 'id_clients')
                if visible:
                    filtered_data.append(row)

            filtered_data.sort(key=lambda x: try_cast(x[col_index]), reverse=reverse)

            tree.delete(*tree.get_children())
            for row in filtered_data:
                tree.insert('', tk.END, values=row)

            for col_name in columns:
                direction = ''
                if col_name == col:
                    direction = ' ▼' if reverse else ' ▲'
                if col_name == 'id_clients':
                    tree.heading(col_name, text='', command=lambda _col=col_name: sort_by_column(_col))
                    tree.column(col_name, width=0, stretch=False)
                else:
                    tree.heading(col_name, text=headers[col_name] + direction,
                                 command=lambda _col=col_name: sort_by_column(_col))

        for col in columns:
            if col == 'id_clients':
                tree.heading(col, text='', command=lambda _col=col: sort_by_column(_col))
                tree.column(col, width=0, stretch=False)
            else:
                tree.heading(col, text=headers[col], command=lambda _col=col: sort_by_column(_col))
                tree.column(col, anchor='center', width=100)

        for client in get_all_clients_with_details():
            id_client = client[0]
            attendance_status = "✅" if was_client_present_today(id_client) else "❌"
            values_with_attendance = list(client) + [attendance_status]
            all_clients_data.append(values_with_attendance)
            tree.insert('', tk.END, values=values_with_attendance)

        def filter_clients(*args):
            query = search_var.get().lower()
            tree.delete(*tree.get_children())

            for row in all_clients_data:
                visible = any(query in str(val).lower() for i, val in enumerate(row) if columns[i] != 'id_clients')
                if visible:
                    tree.insert('', tk.END, values=row)

        search_var.trace_add('write', filter_clients)

        tree.pack(expand=True, fill='both', padx=20, pady=10)

        def open_calendar_for_selected():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Увага", "Оберіть клієнта.")
                return

            values = tree.item(selected, 'values')
            open_attendance_calendar_window(values)

        tk.Button(attend_win, text="Відкрити календар", font=("Arial", 14), bg="#2980b9", fg="white",
                  command=open_calendar_for_selected).pack(pady=10)

    def open_edit_client_window():

        def normalize_text(text):
            return unicodedata.normalize('NFKD', str(text)).casefold()

        edit_win = tk.Toplevel()
        edit_win.title("Редагування клієнтів")
        edit_win.geometry("1000x500")
        edit_win.configure(bg='#34495e')

        top_frame = tk.Frame(edit_win, bg='#34495e')
        top_frame.pack(fill='x', padx=20, pady=(10, 0))

        search_var = tk.StringVar()

        # Таблиця колонок
        columns = ('id_clients', 'full_name', 'phone', 'email', 'registration_date',
                   'trainer_name', 'subscription_type', 'payment', 'attendance', 'present_today')

        headers = {
            'id_clients': 'ID',
            'full_name': "Ім'я",
            'phone': 'Телефон',
            'email': 'Email',
            'registration_date': 'Дата реєстрації',
            'trainer_name': "Ім'я тренера",
            'subscription_type': 'Тип підписки',
            'payment': 'Оплата',
            'attendance': 'Відвідування',
            'present_today': 'Сьогодні'
        }

        tree = ttk.Treeview(edit_win, columns=columns, show='headings')

        sort_directions = {}

        def sort_by_column(col):
            data = []
            for child in tree.get_children():
                values = tree.item(child)['values']
                data.append((values, child))

            col_index = columns.index(col)
            reverse = sort_directions.get(col, False)
            sort_directions[col] = not reverse

            def try_cast(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return str(val).lower()

            data.sort(key=lambda x: try_cast(x[0][col_index]), reverse=reverse)

            for i in tree.get_children():
                tree.delete(i)

            for item in data:
                tree.insert('', tk.END, values=item[0])

            for col_name in columns:
                direction = ''
                if col_name == col:
                    direction = ' ▼' if reverse else ' ▲'
                if col_name == 'id_clients':
                    tree.heading(col_name, text='', command=lambda _col=col_name: sort_by_column(_col))
                    tree.column(col_name, width=0, stretch=False)
                else:
                    tree.heading(col_name, text=headers[col_name] + direction,
                                 command=lambda _col=col_name: sort_by_column(_col))

        for col in columns:
            if col == 'id_clients':
                tree.heading(col, text='', command=lambda _col=col: sort_by_column(_col))
                tree.column(col, width=0, stretch=False)
            else:
                tree.heading(col, text=headers[col], command=lambda _col=col: sort_by_column(_col))
                tree.column(col, anchor='center', width=100)

        all_clients_data = []
        for client in get_all_clients_with_details():
            id_client = client[0]
            attendance_status = "✅" if was_client_present_today(id_client) else "❌"
            values_with_attendance = list(client) + [attendance_status]
            all_clients_data.append(values_with_attendance)
            tree.insert('', tk.END, values=values_with_attendance)

        def filter_clients(*args):
            query = normalize_text(search_var.get())

            tree.delete(*tree.get_children())  # Очистити дерево

            for row in all_clients_data:
                visible = False
                for i, val in enumerate(row):
                    if i >= len(columns):
                        break
                    if columns[i] == 'id_clients':
                        continue
                    if query in normalize_text(val):
                        visible = True
                        break
                if visible:
                    tree.insert('', tk.END, values=row)

        search_var.trace_add('write', filter_clients)

        tk.Label(top_frame, text='🔍 Пошук:', font=('Arial', 12), bg='#34495e', fg='white').pack(side='left')
        tk.Entry(top_frame, textvariable=search_var, font=('Arial', 12), width=30).pack(side='left', padx=(5, 20))
        tk.Label(top_frame, text="Редагування клієнтів", font=("Arial", 20, "bold"), bg='#34495e', fg='white').pack(
            side='left')

        tree.pack(expand=True, fill='both', padx=20, pady=10)

        def edit_selected_client():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Увага", "Оберіть клієнта для редагування.")
                return
            values = tree.item(selected, 'values')
            open_edit_client_details(values[:-1])

        def delete_selected_client():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Увага", "Оберіть клієнта для видалення.")
                return
            values = tree.item(selected, 'values')
            client_id = values[0]
            client_name = values[1]
            confirm = messagebox.askyesno("Підтвердження", f"Ви впевнені, що хочете видалити клієнта {client_name}?")
            if confirm:
                if delete_client_by_id(client_id):
                    messagebox.showinfo("Успіх", "Клієнта видалено.")
                    tree.delete(selected)
                    # Оновити список
                    all_clients_data[:] = [row for row in all_clients_data if row[0] != client_id]
                else:
                    messagebox.showerror("Помилка", "Не вдалося видалити клієнта.")

        tk.Button(edit_win, text="Редагувати обране", font=("Arial", 14), bg="#f39c12", fg="white",
                  command=edit_selected_client).pack(pady=10)
        tk.Button(edit_win, text="Видалити обране", font=("Arial", 14), bg="#c0392b", fg="white",
                  command=delete_selected_client).pack(pady=10)

    def show_subscription_info():
        info_win = tk.Toplevel()
        info_win.title("Інформація про абонементи")
        info_win.geometry("750x700")
        info_win.configure(bg='#ecf0f1')

        tk.Label(info_win, text="Типи абонементів", font=("Arial", 18, "bold"),
                 bg='#ecf0f1', fg="#2c3e50").pack(pady=(10, 0))

        text_frame = tk.Frame(info_win, bg='#ecf0f1')
        text_frame.pack(expand=True, fill='both', padx=10, pady=10)

        subscription_text = (
            "✅ Разове відвідування (1v)\n"
            "• Опис: Ідеальний варіант для новачків, гостей міста або тих, хто хоче спробувати тренування перед покупкою абонементу. "
            "Включає повний доступ до тренажерного залу або групового заняття на один день.\n"
            "• Ціна: 150–250 грн\n"
            "________________________________________\n\n"

            "🗓️ Абонемент на 4 відвідування / місяць (4v)\n"
            "• Опис: Підходить для людей з щільним графіком або тих, хто починає свій спортивний шлях. "
            "Включає 4 відвідування залу протягом 30 днів.\n"
            "• Ціна: 600–800 грн\n"
            "________________________________________\n\n"

            "📆 Абонемент на 8 відвідувань / місяць (8v)\n"
            "• Опис: Оптимальний варіант для підтримання регулярної фізичної форми. "
            "Дозволяє тренуватися двічі на тиждень. Термін дії — 30 днів.\n"
            "• Ціна: 1000–1200 грн\n"
            "________________________________________\n\n"

            "🔄 Безлімітний абонемент (місячний) (unlimitedV)\n"
            "• Опис: Необмежена кількість відвідувань протягом одного місяця. "
            "Ідеальний для активних користувачів, які відвідують зал 3+ рази на тиждень.\n"
            "• Ціна: 1500–2000 грн\n"
            "________________________________________\n\n"

            "📅 Абонементи тривалої дії (3, 6, 12 місяців) (monthPass)\n"
            "• Опис: Економічно вигідне рішення для тих, хто має стабільне тренувальне навантаження. "
            "Забезпечують повний доступ до залу протягом обраного періоду з бонусними знижками.\n"
            "• Ціни:\n"
            "   o 3 місяці: 4000–5000 грн\n"
            "   o 6 місяців: 7000–9000 грн\n"
            "   o 12 місяців: 12 000–15 000 грн\n"
            "________________________________________\n\n"

            "👑 VIP / Преміум абонемент (VIP)\n"
            "• Опис: Максимальний комфорт і розширені можливості. Включає:\n"
            "   o Необмежений доступ до залу\n"
            "   o Безкоштовну воду/напої\n"
            "   o Персональні консультації\n"
            "   o Доступ до сауни або зони релаксу\n"
            "   o Рушники та інші зручності\n"
            "• Ціна: 2500–4000 грн/місяць\n"
        )

        text_widget = tk.Text(text_frame, wrap='word', font=("Arial", 12), bg='white', fg='black')
        text_widget.insert('1.0', subscription_text)
        text_widget.config(state='disabled')
        text_widget.pack(expand=True, fill='both')

        tk.Button(info_win, text="Закрити", command=info_win.destroy,
                  bg="#c0392b", fg="white", font=("Arial", 12)).pack(pady=10)

    frame_add, container_add = rounded_button_container(icon_frame)
    btn_add = tk.Button(container_add, text="➕", **btn_style)
    btn_add.pack(expand=True)
    btn_add.bind("<Enter>", lambda e: on_enter(e, btn_add))
    btn_add.bind("<Leave>", lambda e: on_leave(e, btn_add))
    frame_add.pack(side="left", padx=40)
    tk.Label(frame_add, text="Додати", fg="white", bg="#2c3e50", font=("Arial", 12)).pack()
    btn_add.config(command=open_add_client_window)

    frame_edit, container_edit = rounded_button_container(icon_frame)
    btn_edit = tk.Button(container_edit, text="📝", **btn_style)
    btn_edit.pack(expand=True)
    btn_edit.bind("<Enter>", lambda e: on_enter(e, btn_edit))
    btn_edit.bind("<Leave>", lambda e: on_leave(e, btn_edit))
    frame_edit.pack(side="left", padx=40)
    tk.Label(frame_edit, text="Редагувати", fg="white", bg="#2c3e50", font=("Arial", 12)).pack()
    btn_edit.config(command=open_edit_client_window)

    frame_manage, container_manage = rounded_button_container(icon_frame)
    btn_manage = tk.Button(container_manage, text="📆", **btn_style)
    btn_manage.pack(expand=True)
    btn_manage.bind("<Enter>", lambda e: on_enter(e, btn_manage))
    btn_manage.bind("<Leave>", lambda e: on_leave(e, btn_manage))
    frame_manage.pack(side="left", padx=40)
    tk.Label(frame_manage, text="Відвідуваність", fg="white", bg="#2c3e50", font=("Arial", 12)).pack()
    btn_manage.config(command=open_attendance_management_window)

    info_frame, info_container = rounded_button_container(icon_frame)
    btn_info = tk.Button(info_container, text="ℹ️", **btn_style)
    btn_info.pack(expand=True)
    btn_info.bind("<Enter>", lambda e: on_enter(e, btn_info))
    btn_info.bind("<Leave>", lambda e: on_leave(e, btn_info))
    btn_info.config(command=show_subscription_info)
    tk.Label(info_frame, text="Інформація про абонементи", fg="white", bg="#2c3e50", font=("Arial", 12)).pack()
    info_frame.pack(pady=10)

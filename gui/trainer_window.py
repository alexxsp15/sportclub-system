import tkinter as tk
from tkinter import ttk, messagebox
from attendance_window import open_attendance_calendar_window
from database.gym import get_clients_for_trainer, was_client_present_today

def open_trainer_interface(user):
    attend_win = tk.Toplevel()
    attend_win.title("Кабінет тренера")
    attend_win.state('zoomed')
    attend_win.configure(bg='#34495e')

    search_var = tk.StringVar()

    title_frame = tk.Frame(attend_win, bg='#34495e')
    title_frame.pack(fill='x', pady=(5, 0))

    title_label = tk.Label(title_frame, text="Менеджмент відвідуваності",
                           font=("Arial", 65, "bold"), bg='#34495e', fg='white')
    title_label.pack(anchor='center')  # Центр по ширині title_frame

    search_frame = tk.Frame(attend_win, bg='#34495e')
    search_frame.pack(fill='x', padx=20, pady=(5, 10))

    tk.Label(search_frame, text='🔍 Пошук:', font=('Arial', 12),
             bg='#34495e', fg='white').pack(side='left')
    tk.Entry(search_frame, textvariable=search_var,
             font=('Arial', 12), width=30).pack(side='left', padx=(5, 0))

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

    for client in get_clients_for_trainer(user[0]):
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

    info_frame = tk.Frame(attend_win, bg='#34495e')
    info_frame.pack(pady=(10, 20))

    tk.Label(info_frame, text="Інформація про абонементи:",
             font=("Arial", 14, "bold"), bg='#34495e', fg='white').pack(side='left')

    tk.Button(info_frame, text="i", font=("Arial", 14, "bold"), width=2,
              bg="#27ae60", fg='white', command=show_subscription_info).pack(side='left', padx=(10, 0))

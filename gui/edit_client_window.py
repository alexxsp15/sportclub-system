import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta
import re
from database.gym import update_client, get_all_trainers, add_subscription, deactivate_active_subscriptions

def open_edit_client_details(client_data):
    client_id, full_name, phone, email, reg_date, trainer_name, subscription_type, payment, attendance = client_data

    window = tk.Toplevel()
    window.title(f"Редагування клієнта: {full_name}")
    window.geometry("900x750")
    window.configure(bg="#2c3e50")

    main_frame = tk.Frame(window, bg="#2c3e50")
    main_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(main_frame, bg="#2c3e50", highlightthickness=0)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    center_frame = tk.Frame(canvas, bg="#2c3e50")
    canvas_window = canvas.create_window((0, 0), window=center_frame, anchor="n")

    inner_frame = tk.Frame(center_frame, bg="#2c3e50", width=800)
    inner_frame.pack(anchor="center", padx=20, pady=10)

    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", on_canvas_configure)

    tk.Label(inner_frame, text="Редагування інформації клієнта", font=("Arial", 16, "bold"),
             bg="#2c3e50", fg="white").pack(pady=10)

    def create_entry(label_text, value):
        tk.Label(inner_frame, text=label_text, bg="#2c3e50", fg="white", font=("Arial", 12)).pack()
        entry = tk.Entry(inner_frame, font=("Arial", 14), width=40)
        entry.insert(0, value if value is not None else "")
        entry.pack(pady=5)
        return entry

    entry_name = create_entry("Ім’я:", full_name)
    entry_phone = create_entry("Телефон:", phone)
    entry_email = create_entry("Email:", email)

    tk.Label(inner_frame, text="Ім’я тренера:", bg="#2c3e50", fg="white", font=("Arial", 12)).pack()
    trainer_list = ["None"] + get_all_trainers()
    trainer_var = tk.StringVar()
    trainer_dropdown = ttk.Combobox(inner_frame, textvariable=trainer_var, font=("Arial", 12), width=37)
    trainer_dropdown['values'] = trainer_list
    trainer_dropdown.set(trainer_name if trainer_name else "")
    trainer_dropdown.pack(pady=5)

    tk.Label(inner_frame, text="Тип підписки:", bg="#2c3e50", fg="white", font=("Arial", 12)).pack()
    subscription_types = ['1v', '4v', '8v', 'UnlimitedV', 'MonthPass', 'VIP']
    subscription_type_var = tk.StringVar()
    subscription_dropdown = ttk.Combobox(inner_frame, textvariable=subscription_type_var, font=("Arial", 12),
                                         width=37)
    subscription_dropdown['values'] = subscription_types
    subscription_dropdown.set(subscription_type if subscription_type else "")
    subscription_dropdown.pack(pady=5)

    duration_frame = tk.Frame(inner_frame, bg="#2c3e50")
    tk.Label(duration_frame, text="Тривалість підписки (місяців):", bg="#2c3e50", fg="white", font=("Arial", 12)).pack()
    duration_var = tk.StringVar()
    duration_dropdown = ttk.Combobox(duration_frame, textvariable=duration_var, font=("Arial", 12), width=37, state="readonly")
    duration_dropdown['values'] = ['1', '3', '6', '12']
    duration_dropdown.set('1')
    duration_dropdown.pack(pady=5)
    duration_frame.pack(pady=5)

    tk.Label(inner_frame, text="Дата початку підписки (рррр-мм-дд):", bg="#2c3e50", fg="white", font=("Arial", 12)).pack()
    entry_start_date = tk.Entry(inner_frame, font=("Arial", 14), width=40)
    entry_start_date.insert(0, datetime.now().date().isoformat())
    entry_start_date.pack(pady=5)

    entry_payment = create_entry("Оплата:", payment)

    subscription_prices = {
        "1v": 200,
        "4v": 700,
        "8v": 1100,
        "UnlimitedV": 1800,
        "MonthPass": {
            "1": 1500,
            "3": 4500,
            "6": 8000,
            "12": 13000
        },
        "VIP": {
            "1": 3000,
            "3": 8500,
            "6": 16000,
            "12": 28000
        }
    }

    subscription_info_label = tk.Label(inner_frame, text="", bg="#2c3e50", fg="white", font=("Arial", 12, "bold"))

    def update_subscription_info():
        sub_type = subscription_type_var.get()
        duration = duration_var.get()
        try:
            if sub_type in ["MonthPass", "VIP", "UnlimitedV"]:
                months = int(duration)
                start_date = datetime.strptime(entry_start_date.get(), "%Y-%m-%d").date()
                end_date = start_date + timedelta(days=months * 30)
                subscription_info_label.config(text=f"Підписка діє до: {end_date.isoformat()}")
            else:
                subscription_info_label.config(text="")
        except Exception:
            subscription_info_label.config(text="Неможливо визначити термін дії підписки.")

    def update_payment_price(*args):
        sub_type = subscription_type_var.get()
        duration = duration_var.get()

        if sub_type in ["MonthPass", "VIP"]:
            duration_frame.pack(pady=5)
            price = subscription_prices.get(sub_type, {}).get(duration)
        elif sub_type in ["1v", "4v", "8v", "UnlimitedV"]:
            duration_frame.pack_forget()
            price = subscription_prices.get(sub_type)
        else:
            duration_frame.pack_forget()
            price = ""

        if price:
            entry_payment.delete(0, tk.END)
            entry_payment.insert(0, str(price))

        update_subscription_info()

    subscription_type_var.trace_add("write", update_payment_price)
    duration_var.trace_add("write", update_payment_price)

    def save_changes():
        name_value = entry_name.get().strip()
        phone_value = entry_phone.get().strip()
        email_value = entry_email.get().strip()
        payment_value = entry_payment.get().strip()

        if not re.match(r"^[А-ЯІЇЄҐа-яіїєґ'\- ]{2,}$", name_value):
            messagebox.showerror("Помилка", "Ім’я повинно містити лише українські літери та бути не менше 2 символів.")
            return

        if not re.match(r"^\+380\d{9}$", phone_value):
            messagebox.showerror("Помилка", "Введіть номер телефону у форматі +380XXXXXXXXX.")
            return

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email_value):
            messagebox.showerror("Помилка", "Некоректна email адреса.")
            return

        if payment_value:
            try:
                payment_float = float(payment_value)
                if payment_float < 0:
                    messagebox.showerror("Помилка", "Сума оплати не може бути від’ємною.")
                    return
            except ValueError:
                messagebox.showerror("Помилка", "Некоректне значення для оплати. Введіть число.")
                return
        else:
            payment_float = None

        trainer_value = trainer_var.get()
        success = update_client(
            client_id,
            name_value,
            phone_value,
            email_value,
            trainer_value,
            payment_float
        )

        try:
            sub_type = subscription_type_var.get()
            months = int(duration_var.get())

            start_date_str = entry_start_date.get().strip()
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Помилка",
                                     "Некоректний формат дати. Використовуйте формат РРРР-ММ-ДД (наприклад, 2025-06-03).")
                return

            end_date = start_date + timedelta(days=months * 30)
            status = "active"

            deactivate_active_subscriptions(client_id)

            add_subscription(client_id, sub_type, start_date.isoformat(), end_date.isoformat(), status)

            update_subscription_info()
        except Exception as e:
            print("Помилка при збереженні підписки:", e)

        if success:
            messagebox.showinfo("Успіх", "Інформацію оновлено.")
        else:
            messagebox.showerror("Помилка", "Не вдалося оновити клієнта.")

    tk.Button(inner_frame, text="Зберегти", font=("Arial", 14), bg="#27ae60", fg="white",
              command=save_changes).pack(pady=20)

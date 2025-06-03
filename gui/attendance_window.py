import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from datetime import datetime
from database.gym import (
   get_client_attendance,
   get_attendance_within_subscription,
   add_attendance,
   is_attendance_overlap,
   get_client_subscriptions,
   get_planned_visit_dates,
   delete_planned_visit,
    add_planned_visit
)

def open_attendance_calendar_window(client_data):
   client_id, full_name, phone, email, reg_date, trainer_name, subscription_type, payment, *_ = client_data


   win = tk.Toplevel()
   win.title(f"Відвідування: {full_name}")
   win.geometry("600x650")
   win.configure(bg="#2c3e50")


   tk.Label(win, text=f"Клієнт: {full_name}", font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack(pady=10)
   tk.Label(win, text=f"Телефон: {phone}", font=("Arial", 12), bg="#2c3e50", fg="white").pack()
   tk.Label(win, text=f"Підписка: {subscription_type}", font=("Arial", 12), bg="#2c3e50", fg="white").pack()


   active_sub = {}


   def refresh_active_subscription():
       nonlocal active_sub
       active_sub = {}

       attendance = get_client_attendance(client_id)

       active_start, active_end = None, None
       for sub in get_client_subscriptions(client_id):
           _, sub_type, start_date, end_date, status, _ = sub
           if status == 'active':
               active_start = datetime.strptime(start_date, "%Y-%m-%d").date()
               active_end = datetime.strptime(end_date, "%Y-%m-%d").date()


               visits_limit = None
               if sub_type in ["1v", "4v", "8v"]:
                   visits_limit = int(sub_type[0])


               active_sub = {
                   'start_date': active_start,
                   'end_date': active_end,
                   'type': sub_type,
                   'visits': visits_limit  # 🔧 Додано
               }
               break


       for rec in attendance:
           check_in = rec[1]
           if not check_in or len(check_in) < 10:
               continue
           try:
               date_str = check_in[:10]
               date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
               if active_start and active_end and active_start <= date_obj <= active_end:
                   calendar.calevent_create(date_obj, 'Відвідування', 'present')
               else:
                   calendar.calevent_create(date_obj, 'Минуле', 'past_visit')
           except Exception as e:
               print("Помилка обробки дати:", e)

   main_content_frame = tk.Frame(win, bg="#2c3e50")
   main_content_frame.pack(pady=10)

   calendar = Calendar(main_content_frame, selectmode='day',
                       year=datetime.now().year,
                       month=datetime.now().month,
                       day=datetime.now().day)
   calendar.pack(side=tk.LEFT, padx=20, pady=10)

   calendar.tag_config('present', background='green', foreground='white')
   calendar.tag_config('past_visit', background='blue', foreground='white')
   calendar.tag_config('planned', background='orange', foreground='white')
   calendar.tag_config('overdue', background='red', foreground='white')

   right_frame = tk.Frame(main_content_frame, bg="#2c3e50")
   right_frame.pack(side=tk.LEFT, padx=10, pady=10, anchor="n")


   date_visits_label = tk.Label(right_frame, text="Відвідування", font=("Arial", 11, "bold"), bg="#2c3e50", fg="white")
   date_visits_label.pack(anchor="nw", pady=5)

   visits_text = tk.Text(right_frame, width=25, height=6, font=("Arial", 11), bg="#34495e", fg="white", wrap=tk.WORD,
                         bd=1, relief=tk.FLAT)
   visits_text.pack()
   visits_text.config(state=tk.DISABLED)

   def show_visits_for_selected_date(event):
       selected_date = calendar.selection_get()
       selected_date_str = selected_date.isoformat()
       all_visits = get_client_attendance(client_id)
       planned_visits = get_planned_visit_dates(client_id)


       visits_on_date = []
       for visit in all_visits:
           date_part = visit[1].split()[0]
           if date_part == selected_date_str:
               visits_on_date.append((visit[1], visit[2]))


       planned_on_date = [v for v in planned_visits if v["date"] == selected_date_str]

       if planned_on_date:
           visit = planned_on_date[0]
           if not is_attendance_overlap(client_id, selected_date_str, visit["time_start"], visit["end_time"]):
               btn_confirm.pack(pady=5)
           else:
               btn_confirm.pack_forget()
       else:
           btn_confirm.pack_forget()

       visits_text.config(state=tk.NORMAL)
       visits_text.delete('1.0', tk.END)
       visits_text.insert(tk.END, f"Дата: {selected_date_str}\n")


       if visits_on_date:
           visits_text.insert(tk.END, "\n[Факт. відвідування]\n")
           for check_in, check_out in visits_on_date:
               try:
                   time_in = check_in.split()[1][:5]
                   time_out = check_out.split()[1][:5]
                   visits_text.insert(tk.END, f"{time_in} - {time_out}\n")
               except:
                   visits_text.insert(tk.END, "Невідомий формат часу\n")

       if planned_on_date:
           visits_text.insert(tk.END, "\n[Заплановані]\n")
           now = datetime.now()
           for v in planned_on_date:
               status = "Заплановано"
               try:
                   end_datetime = datetime.strptime(f"{v['date']} {v['end_time']}", "%Y-%m-%d %H:%M")
                   if end_datetime < now:
                       status = "Просрочено"
               except:
                   status = "???"
               visits_text.insert(tk.END, f"{v['time_start']} - {v['end_time']}  —  {status}\n")

       if not visits_on_date and not planned_on_date:
           visits_text.insert(tk.END, "\nНемає даних.")

       visits_text.config(state=tk.DISABLED)

   calendar.bind("<<CalendarSelected>>", show_visits_for_selected_date)
   #
   def get_total_used_dates(client_id, sub):
       attendances = get_client_attendance(client_id)
       planned_visits = get_planned_visit_dates(client_id)

       used_dates = set()

       start = sub["start_date"]
       end = sub["end_date"]

       for a in attendances:
           try:
               date_obj = datetime.strptime(a[1], "%Y-%m-%d %H:%M:%S").date()
           except:
               try:
                   date_obj = datetime.strptime(a[1], "%Y-%m-%d %H:%M").date()
               except:
                   continue
           if start <= date_obj <= end:
               used_dates.add(date_obj)

       for p in planned_visits:
           try:
               date_obj = datetime.strptime(p["date"], "%Y-%m-%d").date()
               if start <= date_obj <= end and date_obj not in used_dates:
                   used_dates.add(date_obj)
           except:
               continue


       return used_dates

   def confirm_attendance(selected_date):
       selected_date_str = selected_date.isoformat()
       planned_visits = get_planned_visit_dates(client_id)

       match = next((v for v in planned_visits if v["date"] == selected_date_str), None)

       if not match:
           messagebox.showinfo("Інформація", "На цю дату не заплановано відвідування.")
           return

       if is_attendance_overlap(client_id, selected_date_str, match["time_start"], match["end_time"]):
           messagebox.showinfo("Інформація", "Відвідування вже зареєстровано.")
           return

       if subscription_type in ["1v", "4v", "8v"]:
           allowed = int(subscription_type[0])
           used_dates = get_total_used_dates(client_id, active_sub)

           if len(used_dates) >= allowed and selected_date not in used_dates:
               messagebox.showerror("Помилка", "Досягнуто ліміту відвідувань для поточного абонементу.")
               return
       messagebox.showinfo(
           "DEBUG",
           f"used_dates: {used_dates}\n"
           f"len(used_dates): {len(used_dates)}\n"
           f"allowed: {allowed}\n"
           f"selected_date: {selected_date}\n"
           f"in used_dates: {selected_date in used_dates}"
       )

       add_attendance(client_id, match["time_start"], match["end_time"], selected_date_str)

       delete_planned_visit(client_id, selected_date_str)

       messagebox.showinfo("Успіх", "Присутність підтверджено.")
       refresh_active_subscription()
       update_subscription_info()
       reload_calendar_attendance()
       show_visits_for_selected_date(None)

   info_label = tk.Label(win, text="", font=("Arial", 12, "bold"), bg="#2c3e50", fg="white")
   info_label.pack(pady=5)


   def update_subscription_info():
       attendances = get_client_attendance(client_id)
       planned_visits = get_planned_visit_dates(client_id)

       used_dates = set()

       for a in attendances:
           try:
               date_obj = datetime.strptime(a[1], "%Y-%m-%d %H:%M:%S").date()
               used_dates.add(date_obj)
           except (ValueError, TypeError):
               try:
                   date_obj = datetime.strptime(a[1], "%Y-%m-%d %H:%M").date()
                   used_dates.add(date_obj)
               except:
                   pass

       for p in planned_visits:
           try:
               p_date = datetime.strptime(p["date"], "%Y-%m-%d").date()
               if p_date not in used_dates:
                   used_dates.add(p_date)
           except:
               pass

       for p in planned_visits:
           try:
               p_date = datetime.strptime(p["date"], "%Y-%m-%d").date()
               if p_date not in used_dates:
                   used_dates.add(p_date)
           except:
               pass

       active_subs = [
           s for s in get_client_subscriptions(client_id) if s[4] == "active"
       ]

       if active_subs:
           sub = active_subs[0]
           sub_type = sub[1]
           start_date = datetime.strptime(sub[2], "%Y-%m-%d").date()
           end_date = datetime.strptime(sub[3], "%Y-%m-%d").date()

           if sub_type in ["1v", "4v", "8v"]:
               allowed = int(sub_type[0])
               used = len([d for d in used_dates if start_date <= d <= end_date])
               remaining = max(allowed - used, 0)
               info_label.config(text=f"Залишилось відвідувань: {remaining}")
           else:
               info_label.config(text="Підписка без обмежень.")
       else:
           info_label.config(text="Немає активної підписки.")

   def reload_calendar_attendance():

       calendar.calevent_remove('all')

       attendance = get_client_attendance(client_id)

       subscription_data = get_client_subscriptions(client_id)
       active_start, active_end = None, None
       for sub in subscription_data:
           _, sub_type, start_date, end_date, status, _ = sub
           if status == 'active':
               active_start = datetime.strptime(start_date, "%Y-%m-%d").date()
               active_end = datetime.strptime(end_date, "%Y-%m-%d").date()
               break

       for record in attendance:
           check_in = record[1]
           try:
               date_str = check_in.split()[0]
               date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

               if active_start and active_start <= date_obj <= active_end:
                   calendar.calevent_create(date_obj, 'Відвідування', 'present')
               else:
                   calendar.calevent_create(date_obj, 'Минуле', 'past_visit')

           except Exception as e:
               print("Пропущено:", e)

       planned_visits = get_planned_visit_dates(client_id)
       now = datetime.now()
       for visit in planned_visits:
           try:
               end_datetime = datetime.strptime(f"{visit['date']} {visit['end_time']}", "%Y-%m-%d %H:%M")
               date_obj = datetime.strptime(visit["date"], "%Y-%m-%d").date()

               if end_datetime < now:
                   calendar.calevent_create(date_obj, 'Просрочено', 'overdue')
               else:
                   calendar.calevent_create(date_obj, 'Заплановано', 'planned')
           except Exception as e:
               print("Помилка у planned date:", e)

   def open_planning_window():
       selected_date = calendar.selection_get()
       if not (active_sub and active_sub['start_date'] <= selected_date <= active_sub['end_date']):
           messagebox.showerror("Помилка", "Оберіть дату в межах активної підписки.")
           return

       start_time = entry_check_in.get().strip()
       end_time = entry_check_out.get().strip()

       try:
           datetime.strptime(start_time, "%H:%M")
           datetime.strptime(end_time, "%H:%M")
       except ValueError:
           messagebox.showerror("Помилка", "Невірний формат часу. Введіть у форматі HH:MM.")
           return

       if selected_date < datetime.now().date():
           messagebox.showerror("Помилка", "Не можна планувати на минулі дати.")
           return

       if subscription_type in ["1v", "4v", "8v"]:
           visits_allowed = int(subscription_type[0])
           visits_done = len(get_attendance_within_subscription(client_id))
           planned_visits = get_planned_visit_dates(client_id)

           planned_count = sum(
               1 for v in planned_visits
               if active_sub["start_date"] <= datetime.strptime(v["date"], "%Y-%m-%d").date() <= active_sub["end_date"]
           )

           if (visits_done + planned_count) >= visits_allowed:
               messagebox.showerror("Помилка",
                                    "Вичерпано кількість дозволених відвідувань (враховано заплановані).")
               return

       add_planned_visit(client_id, selected_date.isoformat(), start_time, end_time)
       messagebox.showinfo("Успіх", "Відвідування заплановано!")

       refresh_active_subscription()
       update_subscription_info()
       reload_calendar_attendance()
       show_visits_for_selected_date(None)


   tk.Label(win, text="Час входу (HH:MM):", bg="#2c3e50", fg="white").pack()
   entry_check_in = tk.Entry(win, font=("Arial", 12))
   entry_check_in.insert(0, "09:00")
   entry_check_in.pack(pady=5)

   tk.Label(win, text="Час виходу (HH:MM):", bg="#2c3e50", fg="white").pack()
   entry_check_out = tk.Entry(win, font=("Arial", 12))
   entry_check_out.insert(0, "10:00")
   entry_check_out.pack(pady=5)

   tk.Button(win, text="Запланувати відвідування", bg="#2980b9", fg="white", font=("Arial", 12),
             command=open_planning_window).pack(pady=5)

   def add_attendance_record():
       if not active_sub:
           messagebox.showerror("Помилка", "У клієнта немає активної підписки.")
           return

       date_obj = calendar.selection_get()
       date_str = date_obj.isoformat()
       check_in = entry_check_in.get()
       check_out = entry_check_out.get()

       try:
           datetime.strptime(check_in, "%H:%M")
           datetime.strptime(check_out, "%H:%M")
       except ValueError:
           messagebox.showerror("Помилка", "Невірний формат часу. Введіть у форматі HH:MM.")
           return

       check_in_datetime = datetime.combine(date_obj, datetime.strptime(check_in, "%H:%M").time())
       now = datetime.now()
       if check_in_datetime > now:
           messagebox.showerror("Помилка", "Не можна додавати відвідування в майбутньому.")
           return

       if active_sub and not (active_sub['start_date'] <= date_obj <= active_sub['end_date']):
           messagebox.showerror("Помилка", "Дата поза терміном дії підписки.")
           return

       if subscription_type in ["1v", "4v", "8v"]:
           used_dates = get_total_used_dates(client_id, active_sub)
           allowed = active_sub.get("visits", 0)

           if len(used_dates) >= allowed and date_obj not in used_dates:
               messagebox.showerror("Помилка", "Вичерпано кількість дозволених відвідувань.")
               return

       if is_attendance_overlap(client_id, date_str, check_in, check_out):
           messagebox.showinfo("Інформація", "Відвідування вже зареєстровано.")
           return

       add_attendance(client_id, check_in, check_out, date_str)
       messagebox.showinfo("Успіх", "Відвідування додано.")
       refresh_active_subscription()
       update_subscription_info()
       calendar.calevent_create(date_obj, 'Відвідування', 'present')

   tk.Button(win, text="Додати відвідування", bg="#27ae60", fg="white", font=("Arial", 14),
             command=add_attendance_record).pack(pady=20)
   btn_confirm = tk.Button(win, text="Підтвердити присутність", bg="#f39c12", fg="white",
                           font=("Arial", 12), command=lambda: confirm_attendance(calendar.selection_get()))
   btn_confirm.pack_forget()


   refresh_active_subscription()
   update_subscription_info()
   reload_calendar_attendance()

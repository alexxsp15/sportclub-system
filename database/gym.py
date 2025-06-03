import sqlite3
import os
from datetime import datetime, timedelta
import bcrypt

DB_PATH = os.path.join(os.path.dirname(__file__), "gym.db")

def connect_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id_users INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'trainer')) NOT NULL
        );
    ''')

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id_clients INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            registration_date DATE,
            id_users INTEGER,
            FOREIGN KEY (id_users) REFERENCES users(id_users) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id_subscriptions INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT CHECK (type IN ('1v', '4v', '8v', 'UnlimitedV', 'MonthPass', 'VIP')),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT CHECK (status IN ('active', 'expired', 'frozen', 'pending', 'canceled')),
            id_clients INTEGER,
            FOREIGN KEY (id_clients) REFERENCES clients(id_clients) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id_attendance INTEGER PRIMARY KEY AUTOINCREMENT,
                check_in_time TEXT,
                check_out_time TEXT,
                id_clients INTEGER,
                FOREIGN KEY (id_clients) REFERENCES clients(id_clients) ON DELETE CASCADE
            )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id_payments INTEGER PRIMARY KEY AUTOINCREMENT,
            amount DECIMAL NOT NULL,
            payment_date DATE NOT NULL,
            id_clients INTEGER,
            FOREIGN KEY (id_clients) REFERENCES clients(id_clients) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planned_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        date TEXT,
        time_start TEXT,
        time_end TEXT,
        status TEXT DEFAULT 'planned', -- 'planned', 'completed', 'canceled'
        FOREIGN KEY(client_id) REFERENCES clients(id)
        );
    """)

    conn.commit()
    conn.close()

def get_user(username, password):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    db.close()

    if user:
        stored_hash = user[2]  # password_hash — 3-тє поле (індекс 2)
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return user

    return None

def register_user(username, password, role):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        db.close()
        return False

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, hashed, role))
    db.commit()
    db.close()
    return True

def add_client_to_db(full_name, phone, email, id_users=None):
    db = connect_db()
    cursor = db.cursor()
    try:
        registration_date = datetime.now().date()
        cursor.execute("""
            INSERT INTO clients (full_name, phone, email, registration_date, id_users)
            VALUES (?, ?, ?, ?, ?)
        """, (full_name, phone, email, registration_date, id_users))
        db.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Помилка при додаванні клієнта: {e}")
        return False
    finally:
        db.close()

def update_client(client_id, full_name=None, phone=None, email=None, trainer_username=None,
                  payment_amount=None, attendance_count=None):
    db = connect_db()
    cursor = db.cursor()

    if full_name or phone or email or trainer_username is not None:
        updates, values = [], []

        if full_name:
            updates.append("full_name = ?")
            values.append(full_name)
        if phone:
            updates.append("phone = ?")
            values.append(phone)
        if email:
            updates.append("email = ?")
            values.append(email)

        if trainer_username == "None":
            updates.append("id_users = NULL")
        elif trainer_username:
            cursor.execute("SELECT id_users FROM users WHERE username = ?", (trainer_username,))
            trainer = cursor.fetchone()
            if trainer:
                updates.append("id_users = ?")
                values.append(trainer[0])

        if updates:
            query = f"UPDATE clients SET {', '.join(updates)} WHERE id_clients = ?"
            values.append(client_id)
            cursor.execute(query, values)

    if payment_amount:
        today = datetime.now().date()
        cursor.execute("""
            INSERT INTO payments (amount, payment_date, id_clients)
            VALUES (?, ?, ?)
        """, (payment_amount, today, client_id))

    if attendance_count:
        now = datetime.now().strftime("%H:%M")
        for _ in range(int(attendance_count)):
            cursor.execute("""
                INSERT INTO attendance (check_in_time, check_out_time, id_clients)
                VALUES (?, ?, ?)
            """, (now, now, client_id))

    db.commit()
    db.close()
    return True

def get_client_subscriptions(client_id):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM subscriptions WHERE id_clients = ?", (client_id,))
    data = cursor.fetchall()
    db.close()
    return data

def get_client_attendance(client_id):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM attendance WHERE id_clients = ?", (client_id,))
    data = cursor.fetchall()
    db.close()
    return data

def add_subscription(client_id, sub_type, start, end, status):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM subscriptions
        WHERE id_clients = ?
    """, (client_id,))

    cursor.execute("""
        INSERT INTO subscriptions (type, start_date, end_date, status, id_clients)
        VALUES (?, ?, ?, ?, ?)
    """, (sub_type, start, end, status, client_id))

    db.commit()
    db.close()

def get_all_clients_with_details():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            c.id_clients,
            c.full_name,
            c.phone,
            c.email,
            c.registration_date,
            u.username AS trainer_name,
            s.type AS subscription_type,
            IFNULL(p.total_payments, 0) AS payment,
            IFNULL(a.total_visits, 0) AS attendance
        FROM clients c
        LEFT JOIN users u ON c.id_users = u.id_users
        LEFT JOIN (
            SELECT s1.*
            FROM subscriptions s1
            INNER JOIN (
                SELECT id_clients, MAX(start_date) AS max_start
                FROM subscriptions
                WHERE status = 'active'
                GROUP BY id_clients
            ) s2 ON s1.id_clients = s2.id_clients AND s1.start_date = s2.max_start
        ) s ON c.id_clients = s.id_clients
        LEFT JOIN (
            SELECT id_clients, SUM(amount) AS total_payments
            FROM payments
            GROUP BY id_clients
        ) p ON c.id_clients = p.id_clients
        LEFT JOIN (
            SELECT id_clients, COUNT(*) AS total_visits
            FROM attendance
            GROUP BY id_clients
        ) a ON c.id_clients = a.id_clients
        GROUP BY c.id_clients
    """)
    clients = cursor.fetchall()
    db.close()
    return clients

def was_client_present_today(client_id, check_in_time=None):
    db = connect_db()
    cursor = db.cursor()
    today = datetime.now().date().isoformat()

    if check_in_time:
        cursor.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE id_clients = ? AND DATE(check_in_time) = ? AND TIME(check_in_time) = ?
        """, (client_id, today, check_in_time))
    else:
        cursor.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE id_clients = ? AND DATE(check_in_time) = ?
        """, (client_id, today))

    result = cursor.fetchone()
    db.close()
    return result[0] > 0

def get_attendance_within_subscription(client_id):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT start_date, end_date, type
        FROM subscriptions
        WHERE id_clients = ? AND status = 'active'
        ORDER BY start_date DESC
        LIMIT 1
    """, (client_id,))
    result = cursor.fetchone()

    if not result:
        db.close()
        return []

    start_date, end_date, sub_type = result

    if sub_type not in ["1v", "4v", "8v"]:
        db.close()
        return []

    cursor.execute("""
        SELECT check_in_time FROM attendance
        WHERE id_clients = ? AND DATE(substr(check_in_time, 1, 10)) BETWEEN ? AND ?
    """, (client_id, start_date, end_date))

    rows = cursor.fetchall()
    db.close()

    return [row[0].split()[0] for row in rows if row[0]]

def add_attendance(client_id, check_in, check_out, date_str=None):
    db = connect_db()
    cursor = db.cursor()

    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    check_in_full = f"{date_str} {check_in}"
    check_out_full = f"{date_str} {check_out}"

    cursor.execute("""
        INSERT INTO attendance (check_in_time, check_out_time, id_clients)
        VALUES (?, ?, ?)
    """, (check_in_full, check_out_full, client_id))

    db.commit()
    db.close()

def is_attendance_overlap(client_id, date_str, new_start_str, new_end_str):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT check_in_time, check_out_time
        FROM attendance
        WHERE id_clients = ? AND DATE(check_in_time) = ?
    """, (client_id, date_str))

    records = cursor.fetchall()
    db.close()

    new_start = datetime.strptime(f"{date_str} {new_start_str}", "%Y-%m-%d %H:%M")
    new_end = datetime.strptime(f"{date_str} {new_end_str}", "%Y-%m-%d %H:%M")

    for check_in, check_out in records:
        try:
            existing_start = datetime.strptime(check_in, "%Y-%m-%d %H:%M:%S")
            existing_end = datetime.strptime(check_out, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                existing_start = datetime.strptime(check_in, "%Y-%m-%d %H:%M")
                existing_end = datetime.strptime(check_out, "%Y-%m-%d %H:%M")
            except:
                continue

        if new_start < existing_end and new_end > existing_start:
            return True

    return False

def get_all_trainers():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE role = 'trainer'")
    trainers = [row[0] for row in cursor.fetchall()]
    db.close()
    return sorted(trainers, key=lambda name: name.lower())

def delete_client_by_id(client_id):
    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM clients WHERE id_clients = ?", (client_id,))
        db.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при видаленні клієнта: {e}")
        return False
    finally:
        db.close()

def add_planned_visit(client_id, date_str, start_time, end_time):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO planned_visits (client_id, date, time_start, time_end)
        VALUES (?, ?, ?, ?)
    """, (client_id, date_str, start_time, end_time))
    db.commit()
    db.close()

def get_planned_visit_dates(client_id):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT date, time_start, time_end FROM planned_visits
        WHERE client_id = ?
    """, (client_id,))
    visits = [{"date": row[0], "time_start": row[1], "end_time": row[2]} for row in cursor.fetchall()]
    db.close()
    return visits

def delete_planned_visit(client_id, date):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
        DELETE FROM planned_visits
        WHERE client_id = ? AND date = ?
    """, (client_id, date))
    db.commit()
    db.close()

def deactivate_active_subscriptions(client_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE subscriptions
        SET status = 'expired'
        WHERE id_clients = ? AND status = 'active'
    """, (client_id,))
    conn.commit()
    conn.close()

def get_clients_for_trainer(trainer_id):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            c.id_clients,
            c.full_name,
            c.phone,
            c.email,
            c.registration_date,
            u.username AS trainer_name,
            s.type AS subscription_type,
            IFNULL(p.total_payments, 0) AS payment,
            IFNULL(a.total_visits, 0) AS attendance
        FROM clients c
        LEFT JOIN users u ON c.id_users = u.id_users
        LEFT JOIN (
            SELECT s1.*
            FROM subscriptions s1
            INNER JOIN (
                SELECT id_clients, MAX(start_date) AS max_start
                FROM subscriptions
                WHERE status = 'active'
                GROUP BY id_clients
            ) s2 ON s1.id_clients = s2.id_clients AND s1.start_date = s2.max_start
        ) s ON c.id_clients = s.id_clients
        LEFT JOIN (
            SELECT id_clients, SUM(amount) AS total_payments
            FROM payments
            GROUP BY id_clients
        ) p ON c.id_clients = p.id_clients
        LEFT JOIN (
            SELECT id_clients, COUNT(*) AS total_visits
            FROM attendance
            GROUP BY id_clients
        ) a ON c.id_clients = a.id_clients
        WHERE c.id_users = ?
        GROUP BY c.id_clients
    """, (trainer_id,))
    clients = cursor.fetchall()
    db.close()
    return clients


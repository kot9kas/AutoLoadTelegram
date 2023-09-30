import sqlite3
from contextlib import closing
from db import DB_NAME
from datetime import datetime

async def add_user(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

async def check_user_rules_accepted(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT accepted_rules FROM users WHERE user_id=?", (user_id,))
        accepted = cursor.fetchone()
        return accepted[0] if accepted else None

async def set_accepted_rules(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET accepted_rules=1 WHERE user_id=?", (user_id,))
        conn.commit()

async def add_file_info(user_id, file_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (user_id, filenumber_id) VALUES (?, ?)", (user_id, file_id))
        conn.commit()

async def get_user_by_file_id(file_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM files WHERE file_id=?", (file_id,))
        user = cursor.fetchone()
        return user[0] if user else None

def add_file(user_id, telegram_file_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (user_id, telegram_file_id) VALUES (?, ?)", (user_id, telegram_file_id))
        conn.commit()
        return cursor.lastrowid
async def get_file_info_by_record(file_record_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT telegram_file_id FROM files WHERE file_id=?", (file_record_id,))
        result = cursor.fetchone()
        if result:
            file_info = {
                'telegram_file_id': result[0]
            }
            return file_info
        else:
            return None
    except Exception as e:
        print(f"Error fetching file info for record {file_record_id}: {e}")
        return None
    finally:
        conn.close()
async def create_user(user_id, registration_date, balance):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, registration_date, balance) VALUES (?, ?, ?)", (user_id, registration_date, balance))
        conn.commit()
async def add_user(user_id):
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, registration_date) VALUES (?, ?)", (user_id, registration_date))
        conn.commit()
def add_balance(user_id: int, amount: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Начисляем баланс
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))

    conn.commit()
    conn.close()
def get_user_balance(user_id: int) -> int:
    # Подключаемся к вашей базе данных
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result[0]
    else:
        return 0  # предполагаем, что если пользователя нет в базе данных, его баланс равен 0

async def get_registration_date(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT registration_date FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
    return None
def set_user_rating(user_id, rating):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET rating = ? WHERE user_id = ?", (rating, user_id))
        conn.commit()

def get_user_rating(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rating FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]

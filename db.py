import sqlite3

DB_NAME = "bot_data.db"

def initialize():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                accepted_rules BOOLEAN DEFAULT FALSE,
                balance INTEGER DEFAULT 0,
                registration_date DATE DEFAULT CURRENT_TIMESTAMP,
                files_submitted_count INTEGER DEFAULT 0
            )
        """)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            telegram_file_id TEXT,
            checked BOOLEAN DEFAULT FALSE,
            date_uploaded DATE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close() 

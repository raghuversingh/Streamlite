import sqlite3
import pandas as pd
from datetime import datetime
from passlib.hash import pbkdf2_sha256
import security

def create_db():
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    # Users table for regular users
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, 
                  email TEXT, 
                  password TEXT, 
                  role TEXT, 
                  otp TEXT, 
                  is_verified INTEGER DEFAULT 0)''')

    # Admins table separate from users
    c.execute('''CREATE TABLE IF NOT EXISTS admins
                 (username TEXT PRIMARY KEY,
                  email TEXT,
                  password TEXT,
                  is_active INTEGER DEFAULT 1)''')

    # Admin history table for admin actions
    c.execute('''CREATE TABLE IF NOT EXISTS admin_history
                 (admin_username TEXT,
                  action_time TEXT,
                  action_type TEXT,
                  details TEXT)''')

    # Create mood_logs table
    c.execute('''CREATE TABLE IF NOT EXISTS mood_logs
                 (username TEXT,
                  date TEXT,
                  mood_label TEXT,
                  score INTEGER)''')
    
    # Create journals table
    c.execute('''CREATE TABLE IF NOT EXISTS journals
                 (username TEXT,
                  date_time TEXT,
                  entry_text TEXT)''')
    
    # Create chat_history table for persistent user chat history
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (username TEXT,
                  timestamp TEXT,
                  user_message TEXT,
                  ai_response TEXT)''')

    # Create activity_logs table for tracking user actions
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs
                 (username TEXT,
                  timestamp TEXT,
                  activity_type TEXT,
                  details TEXT)''')

    # Ensure default admin account exists (password: Admin@123 by default)
    admin_password = pbkdf2_sha256.hash('Admin@123')
    c.execute("INSERT OR IGNORE INTO admins (username, email, password, is_active) VALUES (?,?,?,?)", ('admin', 'admin@clarityhub.local', admin_password, 1))
    
    conn.commit()
    conn.close()

def add_pending_user(username, email, password, otp):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False
    c.execute("SELECT username FROM admins WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False
    hashed = pbkdf2_sha256.hash(password)
    try:
        c.execute("INSERT INTO users (username, email, password, role, otp, is_verified) VALUES (?,?,?,?,?,?)", 
                  (username, email, hashed, 'user', otp, 0))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_pending_user_otp(username, new_otp):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("UPDATE users SET otp = ? WHERE username = ? AND is_verified = 0", (new_otp, username))
    conn.commit()
    success = c.rowcount > 0
    conn.close()
    return success

def verify_otp_in_db(username, otp):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("SELECT otp FROM users WHERE username = ? AND is_verified = 0", (username,))
    res = c.fetchone()
    if res and res[0] == otp:
        c.execute("UPDATE users SET is_verified = 1 WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def verify_user(username, password):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("SELECT password, role, is_verified FROM users WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    if res and pbkdf2_sha256.verify(password, res[0]) and res[2] == 1:
        return res[1]
    return None

def verify_admin(username, password):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("SELECT password, is_active FROM admins WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    if res and res[1] == 1 and pbkdf2_sha256.verify(password, res[0]):
        return True
    return False

def add_admin_account(username, email, password, is_hashed=False):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    hashed = password if is_hashed else pbkdf2_sha256.hash(password)
    try:
        c.execute("INSERT INTO admins (username, email, password, is_active) VALUES (?,?,?,?)", 
                  (username, email, hashed, 1))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def _decrypt_field(value):
    if isinstance(value, str):
        return security.decrypt_string(value)
    return value


def save_journal_entry(username, date_time, entry_text):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("INSERT INTO journals VALUES (?,?,?)", 
              (username, date_time, security.encrypt_string(entry_text)))
    conn.commit()
    conn.close()


def get_user_journals(username, limit=100):
    conn = sqlite3.connect('clarity_hub.db')
    df = pd.read_sql_query(
        f"SELECT date_time, entry_text FROM journals WHERE username=? ORDER BY date_time DESC LIMIT {limit}",
        conn,
        params=(username,),
    )
    conn.close()
    df['entry_text'] = df['entry_text'].apply(_decrypt_field)
    return df


def get_admin_history(limit=100):
    conn = sqlite3.connect('clarity_hub.db')
    df = pd.read_sql_query(f"SELECT admin_username, action_time, action_type, details FROM admin_history ORDER BY action_time DESC LIMIT {limit}", conn)
    conn.close()
    df['details'] = df['details'].apply(_decrypt_field)
    return df


def log_admin_action(admin_username, action_type, details):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("INSERT INTO admin_history VALUES (?,?,?,?)", 
              (admin_username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action_type, security.encrypt_string(details)))
    conn.commit()
    conn.close()


def save_chat_message(username, user_message, ai_response):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("INSERT INTO chat_history VALUES (?,?,?,?)", 
              (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), security.encrypt_string(user_message), security.encrypt_string(ai_response)))
    conn.commit()
    conn.close()


def get_user_chat_history(username, limit=50):
    conn = sqlite3.connect('clarity_hub.db')
    df = pd.read_sql_query(
        f"SELECT timestamp, user_message, ai_response FROM chat_history WHERE username=? ORDER BY timestamp DESC LIMIT {limit}",
        conn,
        params=(username,),
    )
    conn.close()
    df['user_message'] = df['user_message'].apply(_decrypt_field)
    df['ai_response'] = df['ai_response'].apply(_decrypt_field)
    return df


def save_activity_log(username, activity_type, details):
    conn = sqlite3.connect('clarity_hub.db')
    c = conn.cursor()
    c.execute("INSERT INTO activity_logs VALUES (?,?,?,?)", 
              (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), activity_type, security.encrypt_string(details)))
    conn.commit()
    conn.close()


def get_user_activity_logs(username, limit=100):
    conn = sqlite3.connect('clarity_hub.db')
    df = pd.read_sql_query(
        f"SELECT timestamp, activity_type, details FROM activity_logs WHERE username=? ORDER BY timestamp DESC LIMIT {limit}",
        conn,
        params=(username,),
    )
    conn.close()
    df['details'] = df['details'].apply(_decrypt_field)
    return df


def get_all_activity_logs(limit=100):
    conn = sqlite3.connect('clarity_hub.db')
    df = pd.read_sql_query(
        f"SELECT username, timestamp, activity_type, details FROM activity_logs ORDER BY timestamp DESC LIMIT {limit}",
        conn,
    )
    conn.close()
    df['details'] = df['details'].apply(_decrypt_field)
    return df

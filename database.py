from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import sql

# Загружаем переменные из .env
load_dotenv()
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Create routers table
    c.execute("""
        CREATE TABLE IF NOT EXISTS routers (
            mac TEXT PRIMARY KEY NOT NULL CHECK (mac <> ''),
            user_id BIGINT,
            router_name TEXT
        )
    """)
    # Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id BIGINT NOT NULL,
            phone_number TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def validate_router(mac):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM routers WHERE mac = %s", (mac,))
    result = c.fetchone()
    conn.close()
    if result is None:
        return False, "MAC адрес не найден"
    if result[0] is not None:
        return False, "Роутер уже занят"
    return True, ""

def add_new_user_db(chat_id, phone_number, name):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (chat_id, phone_number, name) VALUES (%s, %s, %s)",
            (chat_id, phone_number, name)
        )
        conn.commit()
        return True, "Пользователь добавлен"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

# Список информации по пользователю
def list_user_info_db(chat_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Получаем имя и номер телефона пользователя
        c.execute("SELECT phone_number, name FROM users WHERE chat_id = %s", (chat_id,))
        user = c.fetchone()
        if not user:
            return False, "Пользователь не найден"

        phone_number, name = user

        # Получаем роутеры пользователя
        c.execute("SELECT mac, router_name FROM routers WHERE user_id = %s", (chat_id,))
        routers = c.fetchall()

        return True, {
            "phone_number": phone_number,
            "name": name,
            "routers": routers  # список кортежей: (mac, router_name)
        }
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def add_router_db(chat_id, mac_address, router_name):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Проверка доступности роутера
        valid, error = validate_router(mac_address)
        if not valid:
            return False, error

        # Проверяем, существует ли такой пользователь
        c.execute("SELECT phone_number, name FROM users WHERE chat_id = %s", (chat_id,))
        user = c.fetchone()
        if not user:
            return False, "Пользователь с таким chat_id не найден"

        # Проверка, существует ли уже роутер и есть ли у него пользователь
        c.execute("SELECT user_id FROM routers WHERE mac = %s", (mac_address,))
        router = c.fetchone()
        if router:
            existing_user_id = router[0]
            if existing_user_id is not None and existing_user_id != chat_id:
                return False, "Роутер уже занят другим пользователем"
            # Обновляем роутер (возможно, просто смена имени)
            c.execute(
                "UPDATE routers SET user_id = %s, router_name = %s WHERE mac = %s",
                (chat_id, router_name, mac_address)
            )
        else:
            # Вставляем новый роутер
            c.execute(
                "INSERT INTO routers (mac, user_id, router_name) VALUES (%s, %s, %s)",
                (mac_address, chat_id, router_name)
            )

        conn.commit()
        return True, "Роутер добавлен"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def check_user_exist_db(chat_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT chat_id FROM users WHERE chat_id = %s", (chat_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def remove_router_db(chat_id, mac_address):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check if the router is assigned to this user
        c.execute(
            "SELECT 1 FROM routers WHERE user_id = %s AND mac = %s",
            (chat_id, mac_address)
        )
        if not c.fetchone():
            return False, "Роутер не найден у этого пользователя"
        
        # Remove from routers table
        c.execute("UPDATE routers SET user_id = NULL WHERE mac = %s", (mac_address,))
        
        conn.commit()
        return True, "Роутер удален"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def list_routers_db(chat_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT mac, router_name FROM routers WHERE user_id = %s",
        (chat_id,)
    )
    routers = [{"mac": row[0], "name": row[1]} for row in c.fetchall()]
    conn.close()
    return routers

# ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
def list_tables_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public'
""")
    tables = ({"-": table[0]} for table in c.fetchall())
    conn.close()
    return tables
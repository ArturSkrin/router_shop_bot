import os
import psycopg2

def drop_all_tables():
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")

    tables_to_drop = ["users", "routers", "products"]

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True  # Без этого DROP TABLE может не примениться

    cur = conn.cursor()

    for table in tables_to_drop:
        try:
            print(f"Удаляю таблицу: {table}")
            cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
        except Exception as e:
            print(f"Ошибка при удалении таблицы {table}: {e}")

    cur.close()
    conn.close()
    print("Все указанные таблицы удалены.")

# Пример вызова
drop_all_tables()

if __name__ == "__main__":
    drop_all_tables()
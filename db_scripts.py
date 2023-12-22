
from aiosqlite import connect

# Подключение к базе данных SQLite
async def get_db_connection():
    return connect("stud_database.db")

# Создание таблицы пользователей, если она еще не существует
async def create_users_table():
    async with await get_db_connection() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                role TEXT,
                grup_number TEXT
            )
        """)
        await db.commit()
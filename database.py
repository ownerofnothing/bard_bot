import logging
import sqlite3

DB_DIR = 'db'
DB_NAME = 'gpt_helper.db'
DB_TABLE_USERS_NAME = 'users'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)

def create_db(database_name=DB_NAME):
    db_path = f"{database_name}"
    connection = sqlite3.connect(db_path)
    connection.close

    logging.info(f"DATABASE: Output: База данных успешно создана")


def execute_query(db_file, query, data=None):
    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()

        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)

        connection.commit()
        return cursor
    except sqlite3.Error as e:
        print("Ошибка при выполнении запроса:", e)
    finally:
        connection.close()


def create_table(table_name):
    global DB_NAME
    sql_query = f'CREATE TABLE IF NOT EXISTS {table_name}' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'subject TEXT, ' \
                f'level TEXT, ' \
                f'task TEXT, ' \
                f'answer TEXT)'
    execute_query(DB_NAME, sql_query)


def insert_row(values):
    columns = '(user_id, subject, level, task, answer)'
    sql_query = f"INSERT INTO {DB_TABLE_USERS_NAME} {columns} VALUES (?, ?, ?, ?, ?)"
    execute_query(sql_query, values)
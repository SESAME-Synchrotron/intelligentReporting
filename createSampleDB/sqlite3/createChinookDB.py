import sqlite3

db_file = "./createSampleDB/sqlite3/Chinook.db"
sql_file = "./createSampleDB/sqlite3/Chinook_Sqlite-2.sql"
sql_file2 = "./createSampleDB/sqlite3/Chinook_Sqlite_AutoIncrementPKs.sql"
def load_sql_file_and_execute(db_file, sql_file, sql_file2):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    with open(sql_file, 'r') as file:
        sql_script = file.read()

    try:
        cursor.executescript(sql_script)
        print(f"Database '{db_file}' created successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    with open(sql_file2, 'r') as file:
        sql_script = file.read()

    try:
        cursor.executescript(sql_script)
        print(f"Database '{db_file}' created successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    conn.commit()
    conn.close()



load_sql_file_and_execute(db_file, sql_file, sql_file2)
# load_sql_file_and_execute(db_file, sql_file2)


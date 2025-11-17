import sqlite3
from SQLGenerator import SQLGenerator

class SQLQueryAgent:
    def __init__(self, db_path="createSampleDB/sqlite3/Chinook.db", model_name="SQLCoder-7B", use_vocab_mask=False, k_samples=12):
        self.db_path = db_path
        self.sql_generator = SQLGenerator(model_name, use_vocab_mask, k_samples=k_samples)

        # Establish database connection
        self.conn = sqlite3.connect(self.db_path)

    def ask_sql(self, question: str):
        sql_queries = self.sql_generator.ask_sql(question)
        for sql in sql_queries:
            try:
                rows = self.conn.execute(sql).fetchall()
                return sql, rows[:5]
            except sqlite3.DatabaseError:
                continue
        return None, None

    def run(self, question: str):
        sql, rows = self.ask_sql(question)
        if sql:
            print(f"\n✔ SQL: {sql}")
            print("✔ Rows:", rows)
        else:
            print("\nNo executable SQL – add an example or raise k_samples.")

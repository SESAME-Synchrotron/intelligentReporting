import sqlite3
from db import DB

class DBSQLITE(DB):
    def __init__(self, DBName) -> None:
        super().__init__(DBName, 'sqlite3')
        self.connect()
    
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.DBName)
            self.cursor = self.conn.cursor()
            print("Connected to the database successfully")
            return  self.conn, self.cursor
        except Exception as e:
            print(f"Database error: {e}")
            return None

    def getTableNames (self):
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = self.cursor.fetchall()
            return tables
        except Exception as e:
            return None
        
    def getForeignKeys(self, tableName):
        self.cursor.execute(f"PRAGMA foreign_key_list({tableName})")
        foreignKeys = self.cursor.fetchall()
        return foreignKeys
    
    def getTableColumns(self, tableName):
        self.cursor.execute(f"PRAGMA table_info({tableName})")
        columns = self.cursor.fetchall()
        return columns

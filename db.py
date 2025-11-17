import sqlite3


class DB:
    def __init__(self, DBName, engine) -> None:
        self.DBName = DBName
        self.engine = engine

    def close(self):
        print("Closing the connection")
        self.conn.close()
    
    


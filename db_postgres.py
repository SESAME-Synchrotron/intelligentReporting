import psycopg2
from db import DB

class DBPostgres(DB):
    def __init__(self, DBName, user, password, host='localhost', port=5432) -> None:
        self.DBName = DBName
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        super().__init__(DBName, 'postgresql')
        self.connect()
    
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.DBName,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            print ('###########################')
            print("Connected to the PostgreSQL database successfully")
            return self.conn, self.cursor
        except Exception as e:
            print ('###########################')
            print(f"Database error: {e}")
            return None

    def getTableNames(self):
        try:
            self.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = self.cursor.fetchall()
            return tables
        except Exception as e:
            print(f"Error fetching table names: {e}")
            return None
        
    def getForeignKeys(self, tableName):
        try:
            self.cursor.execute(f"""
                SELECT
                    tc.constraint_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                WHERE constraint_type = 'FOREIGN KEY' AND tc.table_name='{tableName}';
            """)
            foreignKeys = self.cursor.fetchall()
            return foreignKeys
        except Exception as e:
            print(f"Error fetching foreign keys: {e}")
            return None
    
    def getTableColumns(self, tableName):
        try:
            self.cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{tableName}';
            """)
            columns = self.cursor.fetchall()
            return columns
        except Exception as e:
            print(f"Error fetching table columns: {e}")
            return None

import sqlite3
import sys

def extract_queries(filename):
    """
    Reads the file and returns a list of SQL queries found after each 'A:'.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    queries = []
    collecting = False
    current = []
    
    for line in lines:
        if line.startswith('A:'):
            if collecting and current:
                queries.append(' '.join(current).strip())
            collecting = True
            current = [line[len('A:'):].strip()]
        elif collecting:
            if line.strip() == '' or line.startswith('Q:'):
                if current:
                    queries.append(' '.join(current).strip())
                collecting = False
                current = []
            else:
                current.append(line.strip())
    if collecting and current:
        queries.append(' '.join(current).strip())
    
    return queries

def execute_and_report_failures(db_path, queries):
    """
    Executes each query and only prints those that raise an error.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    failures = []
    
    for i, q in enumerate(queries, 1):
        try:
            cursor.execute(q)
        except sqlite3.Error as e:
            failures.append((i, q, e))
    
    conn.close()
    
    if failures:
        print("\nThe following queries failed to execute:\n")
        for idx, query, err in failures:
            print(f"--- Query #{idx} ---")
            print(query)
            print(f"Error: {err}\n")
    else:
        print("All queries executed successfully.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python run_queries.py <examples_file.txt> <database.db>")
        sys.exit(1)
    
    examples_file = sys.argv[1]
    database_file = sys.argv[2]
    
    queries = extract_queries(examples_file)
    if not queries:
        print("No queries found in", examples_file)
        sys.exit(1)
    
    execute_and_report_failures(database_file, queries)

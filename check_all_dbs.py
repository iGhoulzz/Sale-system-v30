import sqlite3
import os

db_files = [
    'sales_system.db',
    'sales_db.db', 
    'database/store.db'
]

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"\n{'='*60}")
        print(f"Checking database: {db_file}")
        print(f"{'='*60}")
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {[table[0] for table in tables]}")
            
            # Look for products data
            for table_name, in tables:
                if 'product' in table_name.lower() or table_name.lower() == 'products':
                    print(f"\n--- Product table found: {table_name} ---")
                    cursor.execute(f'PRAGMA table_info({table_name})')
                    columns = cursor.fetchall()
                    print(f"Columns: {[col[1] for col in columns]}")
                    
                    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                    count = cursor.fetchone()[0]
                    print(f"Row count: {count}")
                    
                    if count > 0:
                        cursor.execute(f'SELECT * FROM {table_name} LIMIT 3')
                        rows = cursor.fetchall()
                        column_names = [col[1] for col in columns]
                        for i, row in enumerate(rows):
                            print(f"Product {i+1}: {dict(zip(column_names, row))}")
                
                # Look for categories data
                if 'categor' in table_name.lower():
                    print(f"\n--- Category table found: {table_name} ---")
                    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                    count = cursor.fetchone()[0]
                    print(f"Row count: {count}")
                    
                    if count > 0:
                        cursor.execute(f'SELECT * FROM {table_name}')
                        rows = cursor.fetchall()
                        print(f"Categories: {rows}")
            
            conn.close()
        except Exception as e:
            print(f"Error checking {db_file}: {e}")
    else:
        print(f"\nDatabase {db_file} does not exist")

import sqlite3

print("Checking database tables...")
conn = sqlite3.connect('sales_system.db')
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables found: {[table[0] for table in tables]}")

# If there's a table that might contain products, let's check it
for table_name, in tables:
    print(f"\nTable: {table_name}")
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    print(f"  Columns: {[col[1] for col in columns]}")
    
    # Check if it has product-like data
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f"  Row count: {count}")
    
    if count > 0:
        cursor.execute(f'SELECT * FROM {table_name} LIMIT 1')
        sample = cursor.fetchone()
        column_names = [col[1] for col in columns]
        if sample:
            print(f"  Sample data: {dict(zip(column_names, sample))}")

conn.close()

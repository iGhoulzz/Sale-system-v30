#!/usr/bin/env python3
"""
Check database schema to identify column mismatches
"""

from modules.db_manager import get_connection, return_connection

def check_database_schema():
    """Check the actual database schema"""
    print("=== DATABASE SCHEMA CHECK ===")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check specific table schemas
        for table in ['Invoices', 'Products', 'Debits', 'InvoiceItems']:
            if table in tables:
                print(f"\n{table} table columns:")
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
            else:
                print(f"\n❌ {table} table not found")
        
        return_connection(conn)
        
    except Exception as e:
        print(f"Error checking schema: {e}")

def check_invoices_data():
    """Check actual data in Invoices table"""
    print("\n=== INVOICES TABLE DATA CHECK ===")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Invoices LIMIT 3")
        rows = cursor.fetchall()
        
        if rows:
            cursor.execute("PRAGMA table_info(Invoices)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Columns: {columns}")
            
            for i, row in enumerate(rows):
                print(f"Row {i+1}: {dict(zip(columns, row))}")
        else:
            print("No data in Invoices table")
            
        return_connection(conn)
        
    except Exception as e:
        print(f"Error checking data: {e}")

if __name__ == "__main__":
    check_database_schema()
    check_invoices_data()

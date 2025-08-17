"""
Check actual database contents and data access methods
"""

import sys
import os
import sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def check_database_directly():
    print("=== CHECKING DATABASE DIRECTLY ===")
    
    # Try different database files
    db_files = ['sales_system.db', 'sales_db.db', 'database/store.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"\n--- Checking {db_file} ---")
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"Tables: {[t[0] for t in tables]}")
                
                # Check Products table if exists
                if any('products' in t[0].lower() for t in tables):
                    cursor.execute("SELECT COUNT(*) FROM Products")
                    count = cursor.fetchone()[0]
                    print(f"Products count: {count}")
                    
                    if count > 0:
                        cursor.execute("SELECT * FROM Products LIMIT 3")
                        products = cursor.fetchall()
                        print(f"Sample products: {products}")
                
                # Check Categories table if exists  
                if any('categories' in t[0].lower() for t in tables):
                    cursor.execute("SELECT COUNT(*) FROM Categories")
                    count = cursor.fetchone()[0]
                    print(f"Categories count: {count}")
                
                conn.close()
                
            except Exception as e:
                print(f"Error checking {db_file}: {e}")

def test_data_access_methods():
    print("\n=== TESTING DATA ACCESS METHODS ===")
    
    try:
        # Test regular data access
        from modules.data_access import get_products as regular_get_products
        print("Testing regular data_access.get_products()...")
        products = regular_get_products()
        print(f"Regular method returned: {len(products)} products")
        if products:
            print(f"First product: {products[0]}")
    except Exception as e:
        print(f"Error with regular data access: {e}")
    
    try:
        # Test enhanced data access
        from modules.enhanced_data_access import enhanced_data
        print("\nTesting enhanced_data_access.get_products()...")
        products = enhanced_data.get_products()
        print(f"Enhanced method returned: {len(products)} products")
        if products:
            print(f"First product: {products[0]}")
    except Exception as e:
        print(f"Error with enhanced data access: {e}")

if __name__ == "__main__":
    check_database_directly()
    test_data_access_methods()

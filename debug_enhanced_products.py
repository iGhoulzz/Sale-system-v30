"""
Debug the enhanced_data.get_products() method step by step
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from modules.enhanced_data_access import enhanced_data
from modules.db_manager import get_connection

def debug_enhanced_get_products():
    print("=== DEBUGGING ENHANCED GET_PRODUCTS ===")
    
    try:
        # Test the connection directly
        print("1. Testing database connection...")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Products")
            count = cursor.fetchone()[0]
            print(f"   Products count via get_connection(): {count}")
            
            # Test the exact query from enhanced_data_access
            print("2. Testing exact query from enhanced_data_access...")
            query = """
            SELECT p.*, c.Name as CategoryName 
            FROM Products p
            LEFT JOIN Categories c ON p.CategoryID = c.ID
            ORDER BY p.Name
            """
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            print(f"   Columns: {columns}")
            
            rows = cursor.fetchall()
            print(f"   Rows count: {len(rows)}")
            
            if rows:
                products = [dict(zip(columns, row)) for row in rows]
                print(f"   First product: {products[0]}")
                
        # Now test the actual method
        print("3. Testing enhanced_data.get_products()...")
        products = enhanced_data.get_products()
        print(f"   Method returned: {len(products)} products")
        
        if len(products) == 0:
            print("4. Investigating why method returns empty...")
            # Let's check if there's any error handling that might be swallowing results
            
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()

def check_categories_table():
    print("\n=== CHECKING CATEGORIES TABLE ===")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if Categories table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Categories'")
            table_exists = cursor.fetchone()
            print(f"Categories table exists: {table_exists is not None}")
            
            if table_exists:
                cursor.execute("SELECT * FROM Categories")
                categories = cursor.fetchall()
                print(f"Categories: {categories}")
            else:
                print("Categories table doesn't exist - this might cause the LEFT JOIN to fail")
                
    except Exception as e:
        print(f"Error checking categories: {e}")

if __name__ == "__main__":
    debug_enhanced_get_products()
    check_categories_table()

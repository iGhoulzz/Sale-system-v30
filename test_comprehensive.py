#!/usr/bin/env python3
"""
Comprehensive frontend-backend connectivity test
"""

import os
import sys
import traceback
import logging

# Setup logging to see detailed error messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=== COMPREHENSIVE FRONTEND-BACKEND TEST ===")

def test_all_pages():
    """Test all pages in the application"""
    print("\n1. Testing all page navigation...")
    
    try:
        # Mock a successful login to skip the login dialog
        import modules.Login
        modules.Login.current_user = {"Username": "test", "Role": "admin"}
        
        # Import and create the main application
        from main import MainApp
        
        print("Creating main application...")
        app = MainApp(themename="darkly")
        
        print("Initializing UI...")
        app._initialize_ui()
        
        # Test navigation to each page
        pages_to_test = ["MainMenuPage", "InventoryPage", "SalesPage", "DebitsPage"]
        
        for page_name in pages_to_test:
            print(f"Testing navigation to {page_name}...")
            try:
                app.show_frame(page_name)
                print(f"✅ {page_name} loaded successfully")
            except Exception as e:
                print(f"❌ {page_name} failed to load: {e}")
                
        # Test some basic backend operations
        print("\n2. Testing backend data operations...")
        
        # Test inventory data
        try:
            from modules.data_access import get_products, get_categories
            products = get_products()
            categories = get_categories()
            print(f"✅ Inventory: {len(products)} products, {len(categories)} categories")
        except Exception as e:
            print(f"❌ Inventory data access failed: {e}")
            
        # Test sales data
        try:
            from modules.data_access import get_recent_invoices
            invoices = get_recent_invoices(limit=10)
            print(f"✅ Sales: {len(invoices)} recent invoices")
        except Exception as e:
            print(f"❌ Sales data access failed: {e}")
            
        # Test debits data
        try:
            from modules.data_access import get_debits
            debits = get_debits()
            print(f"✅ Debits: {len(debits)} debit entries")
        except Exception as e:
            print(f"❌ Debits data access failed: {e}")
            
        # Clean up
        app.destroy()
        print("\n✅ All tests completed successfully")
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        traceback.print_exc()

def test_database_schema():
    """Test database schema and indexes"""
    print("\n3. Testing database schema...")
    
    try:
        from modules.db_manager import get_connection, return_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check main tables
        tables_to_check = ['Products', 'Invoices', 'InvoiceItems', 'Debits', 'Users', 'ActivityLog']
        
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
            result = cursor.fetchone()
            
            if result:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"✅ {table} table exists with {len(columns)} columns")
            else:
                print(f"❌ {table} table missing")
                
        return_connection(conn)
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        traceback.print_exc()

def test_enhanced_vs_standard():
    """Test both enhanced and standard page versions"""
    print("\n4. Testing enhanced vs standard pages...")
    
    try:
        # Test standard pages
        print("Testing standard pages...")
        from modules.pages.inventory_page import InventoryPage
        from modules.pages.sales_page import SalesPage
        from modules.pages.debits_page import DebitsPage
        print("✅ Standard pages import successfully")
        
        # Test enhanced pages  
        print("Testing enhanced pages...")
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        print("✅ Enhanced pages import successfully")
        
    except Exception as e:
        print(f"❌ Page comparison test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_all_pages()
    test_database_schema()
    test_enhanced_vs_standard()
    
    print("\n=== COMPREHENSIVE TEST COMPLETE ===")

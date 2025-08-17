#!/usr/bin/env python3
"""
Test script to diagnose debits page loading issues
"""

import os
import sys
import traceback
import logging

# Setup logging to see detailed error messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=== DEBITS PAGE LOADING TEST ===")
print("Testing individual components...")

# Test 1: Basic imports
print("\n1. Testing basic imports...")
try:
    import tkinter as tk
    import ttkbootstrap as ttk
    print("✅ Basic UI imports successful")
except Exception as e:
    print(f"❌ Basic UI imports failed: {e}")
    sys.exit(1)

# Test 2: Database imports
print("\n2. Testing database imports...")
try:
    from modules.db_manager import get_connection, return_connection
    print("✅ Database manager imports successful")
except Exception as e:
    print(f"❌ Database manager imports failed: {e}")
    traceback.print_exc()

# Test 3: Data access imports
print("\n3. Testing data access imports...")
try:
    from modules.data_access import get_debits, get_invoice_items, record_debit_payment, add_debit
    print("✅ Data access imports successful")
except Exception as e:
    print(f"❌ Data access imports failed: {e}")
    traceback.print_exc()

# Test 4: Enhanced data access imports
print("\n4. Testing enhanced data access imports...")
try:
    from modules.enhanced_data_access import enhanced_data, PagedResult
    print("✅ Enhanced data access imports successful")
except Exception as e:
    print(f"❌ Enhanced data access imports failed: {e}")
    traceback.print_exc()

# Test 5: UI components imports
print("\n5. Testing UI components imports...")
try:
    from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry
    print("✅ UI components imports successful")
except Exception as e:
    print(f"❌ UI components imports failed: {e}")
    traceback.print_exc()

# Test 6: Login module
print("\n6. Testing login module...")
try:
    from modules.Login import current_user
    print("✅ Login module imports successful")
except Exception as e:
    print(f"❌ Login module imports failed: {e}")
    traceback.print_exc()

# Test 7: I18n module
print("\n7. Testing internationalization module...")
try:
    from modules.i18n import _, register_refresh_callback, unregister_refresh_callback, set_widget_direction
    print("✅ I18n module imports successful")
except Exception as e:
    print(f"❌ I18n module imports failed: {e}")
    traceback.print_exc()

# Test 8: Try to import debits page
print("\n8. Testing debits page import...")
try:
    from modules.pages.debits_page import DebitsPage
    print("✅ Standard debits page imports successful")
except Exception as e:
    print(f"❌ Standard debits page imports failed: {e}")
    traceback.print_exc()

# Test 9: Try to import enhanced debits page
print("\n9. Testing enhanced debits page import...")
try:
    from modules.pages.enhanced_debits_page import EnhancedDebitsPage
    print("✅ Enhanced debits page imports successful")
except Exception as e:
    print(f"❌ Enhanced debits page imports failed: {e}")
    traceback.print_exc()

# Test 10: Database connection test
print("\n10. Testing database connection...")
try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Invoices';")
    result = cursor.fetchone()
    return_connection(conn)
    
    if result:
        print("✅ Database connection and Invoices table exists")
    else:
        print("❌ Invoices table does not exist")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    traceback.print_exc()

# Test 11: Test data access functions
print("\n11. Testing data access functions...")
try:
    # Mock current_user for testing
    import modules.Login
    modules.Login.current_user = {"Username": "test", "Role": "admin"}
    
    debits = get_debits()
    print(f"✅ get_debits() successful - returned {len(debits)} debits")
except Exception as e:
    print(f"❌ get_debits() failed: {e}")
    traceback.print_exc()

print("\n=== TEST COMPLETE ===")
print("Check the results above to identify what's causing the debits page loading issues.")

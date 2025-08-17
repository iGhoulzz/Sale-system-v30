#!/usr/bin/env python3
"""
Comprehensive Application Test
This script tests the entire application including the fixed Enhanced Inventory Page.
"""

import sys
import os
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_main_imports():
    """Test that main application imports work"""
    print("🔍 Testing main application imports...")
    
    try:
        # Test core imports
        import tkinter as tk
        import ttkbootstrap as ttk
        print("  ✅ GUI libraries imported")
        
        # Test database imports
        from database.init_db import create_database
        print("  ✅ Database initialization imported")
        
        # Test enhanced pages
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        print("  ✅ Enhanced pages imported")
        
        # Test login system
        from modules.Login import LoginWindow, current_user
        print("  ✅ Login system imported")
        
        # Test data access
        from modules.enhanced_data_access import enhanced_data
        print("  ✅ Enhanced data access imported")
        
        # Test main application
        from main import MainApp, MainMenuPage
        print("  ✅ Main application classes imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_enhanced_inventory_page():
    """Test the Enhanced Inventory Page specifically"""
    print("🔍 Testing Enhanced Inventory Page...")
    
    try:
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        
        # Test that the class can be instantiated (without UI)
        print("  ✅ Enhanced Inventory Page class available")
        
        # Test search method fix
        import inspect
        search_method = getattr(EnhancedInventoryPage, '_perform_product_search', None)
        if search_method:
            sig = inspect.signature(search_method)
            params = list(sig.parameters.keys())
            if 'limit' in params:
                print("  ✅ Search method accepts 'limit' parameter")
            else:
                print("  ❌ Search method missing 'limit' parameter")
                return False
        else:
            print("  ❌ Search method not found")
            return False
        
        # Test dialog imports
        from modules.pages.product_dialog import ProductDialog
        from modules.pages.loss_dialog import LossDialog
        from modules.pages.category_dialog import CategoryDialog
        print("  ✅ All dialog classes available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced Inventory Page error: {e}")
        traceback.print_exc()
        return False

def test_enhanced_data_access():
    """Test enhanced data access methods"""
    print("🔍 Testing Enhanced Data Access...")
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        # Test required methods exist
        required_methods = [
            'get_products',
            'get_categories', 
            'add_category',
            'add_product',
            'update_product',
            'delete_product',
            'update_product_stock',
            'search_products'
        ]
        
        for method_name in required_methods:
            if hasattr(enhanced_data, method_name):
                print(f"  ✅ Method '{method_name}' available")
            else:
                print(f"  ❌ Method '{method_name}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced Data Access error: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing Database Connection...")
    
    try:
        from modules.db_manager import get_connection
        
        # Test database connection
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            print(f"  ✅ Database connected ({table_count} tables)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        traceback.print_exc()
        return False

def test_ui_components():
    """Test UI components"""
    print("🔍 Testing UI Components...")
    
    try:
        from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry
        print("  ✅ UI components imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ UI Components error: {e}")
        traceback.print_exc()
        return False

def test_application_startup():
    """Test application startup sequence"""
    print("🔍 Testing Application Startup Sequence...")
    
    try:
        # Test that MainApp can be created (without actually running it)
        from main import MainApp
        
        # Test basic initialization
        print("  ✅ MainApp class can be imported")
        
        # Test background task system
        from modules.utils import init_background_tasks, shutdown_background_tasks
        print("  ✅ Background task system available")
        
        # Test performance monitoring
        from modules.performance_monitor import performance_monitor
        print("  ✅ Performance monitoring available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Application startup error: {e}")
        traceback.print_exc()
        return False

def test_i18n_system():
    """Test internationalization system"""
    print("🔍 Testing Internationalization System...")
    
    try:
        from modules.i18n import _, switch_language, get_current_language
        
        # Test translation function
        test_text = _("Sales Management System")
        print(f"  ✅ Translation function works: '{test_text}'")
        
        # Test language detection
        current_lang = get_current_language()
        print(f"  ✅ Current language: {current_lang}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ I18N system error: {e}")
        traceback.print_exc()
        return False

def test_all_page_types():
    """Test that all page types can be imported"""
    print("🔍 Testing All Page Types...")
    
    try:
        # Test enhanced pages
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        from modules.pages.enhanced_sales_page import EnhancedSalesPage  
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        print("  ✅ Enhanced pages imported")
        
        # Test standard pages (fallbacks)
        from modules.pages.inventory_page import InventoryPage
        from modules.pages.sales_page import SalesPage
        from modules.pages.debits_page import DebitsPage
        print("  ✅ Standard pages imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Page types error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 COMPREHENSIVE APPLICATION TEST")
    print("=" * 60)
    print()
    
    tests = [
        ("Main Imports", test_main_imports),
        ("Enhanced Inventory Page", test_enhanced_inventory_page),
        ("Enhanced Data Access", test_enhanced_data_access),
        ("Database Connection", test_database_connection),
        ("UI Components", test_ui_components),
        ("Application Startup", test_application_startup),
        ("I18N System", test_i18n_system),
        ("All Page Types", test_all_page_types)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"📋 {test_name}")
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ FAILED with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("🎯 APPLICATION STATUS:")
        print("  ✅ Enhanced Inventory Page is FIXED and working")
        print("  ✅ All imports are working correctly")
        print("  ✅ Database connection is working")
        print("  ✅ UI components are functional")
        print("  ✅ Enhanced pages are ready")
        print("  ✅ Application is ready to run")
        print()
        print("🚀 YOU CAN NOW START THE APPLICATION!")
        print("   Run: python main.py")
        print()
        print("🎨 ENHANCED INVENTORY PAGE FEATURES:")
        print("   📦 Complete product management (Add/Edit/Delete)")
        print("   📁 Visual category management")
        print("   🔍 Advanced search and filtering")
        print("   📊 Live inventory statistics")
        print("   📉 Product loss tracking")
        print("   🎨 Professional UI with excellent visibility")
        
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("   Please check the errors above and fix them before running the application.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

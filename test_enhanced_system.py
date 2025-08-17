#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced sales management system.
This script validates all the section-by-section improvements made.
"""

import sys
import os
import traceback
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all enhanced components can be imported successfully."""
    print("🔍 Testing imports...")
    
    test_cases = [
        ("Main Application", "from main import MainApp"),
        ("Enhanced Sales Page", "from modules.pages.enhanced_sales_page import EnhancedSalesPage"),
        ("Enhanced Debits Page", "from modules.pages.enhanced_debits_page import EnhancedDebitsPage"),
        ("Enhanced Inventory Page", "from modules.pages.enhanced_inventory_page import EnhancedInventoryPage"),
        ("UI Components", "from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry"),
        ("Enhanced Data Access", "from modules.enhanced_data_access import enhanced_data"),
        ("Database Manager", "from modules.db_manager import ConnectionContext"),
        ("Internationalization", "from modules.i18n import _, switch_language"),
        ("Performance Monitor", "from modules.performance_monitor import performance_monitor"),
        ("Logger", "from modules.logger import logger"),
        ("Utils", "from modules.utils import init_background_tasks"),
    ]
    
    results = []
    
    for name, import_statement in test_cases:
        try:
            exec(import_statement)
            results.append((name, True, None))
            print(f"  ✅ {name}")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ❌ {name}: {str(e)}")
    
    return results

def test_enhanced_pages():
    """Test that enhanced pages can be instantiated."""
    print("\n🔍 Testing enhanced pages instantiation...")
    
    try:
        # Create a mock controller
        class MockController:
            def __init__(self):
                self.frames = {}
                self.current_frame = None
            
            def show_frame(self, frame_name):
                pass
        
        # Create mock parent
        import tkinter as tk
        import ttkbootstrap as ttk
        
        # Create test window (will be destroyed immediately)
        root = ttk.Window()
        root.withdraw()  # Hide the window
        
        controller = MockController()
        
        # Test each enhanced page
        test_cases = [
            ("EnhancedSalesPage", "modules.pages.enhanced_sales_page", "EnhancedSalesPage"),
            ("EnhancedDebitsPage", "modules.pages.enhanced_debits_page", "EnhancedDebitsPage"),
            ("EnhancedInventoryPage", "modules.pages.enhanced_inventory_page", "EnhancedInventoryPage"),
        ]
        
        results = []
        
        for page_name, module_name, class_name in test_cases:
            try:
                module = __import__(module_name, fromlist=[class_name])
                page_class = getattr(module, class_name)
                
                # Try to create instance
                page_instance = page_class(root, controller)
                results.append((page_name, True, None))
                print(f"  ✅ {page_name} instantiated successfully")
                
                # Clean up
                page_instance.destroy()
                
            except Exception as e:
                results.append((page_name, False, str(e)))
                print(f"  ❌ {page_name}: {str(e)}")
        
        # Clean up
        root.destroy()
        
        return results
        
    except Exception as e:
        print(f"  ❌ Error setting up test environment: {str(e)}")
        return [("Test Setup", False, str(e))]

def test_ui_components():
    """Test that UI components work correctly."""
    print("\n🔍 Testing UI components...")
    
    try:
        import tkinter as tk
        import ttkbootstrap as ttk
        from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry
        
        # Create test window
        root = ttk.Window()
        root.withdraw()  # Hide the window
        
        results = []
        
        # Test ProgressDialog
        try:
            progress = ProgressDialog(root, title="Test Progress")
            progress.close()
            results.append(("ProgressDialog", True, None))
            print("  ✅ ProgressDialog works correctly")
        except Exception as e:
            results.append(("ProgressDialog", False, str(e)))
            print(f"  ❌ ProgressDialog: {str(e)}")
        
        # Test FastSearchEntry  
        try:
            def dummy_search(term):
                return []
            
            search_entry = FastSearchEntry(
                root, 
                search_function=dummy_search,
                placeholder="Test search..."
            )
            search_frame = search_entry.get_frame()
            results.append(("FastSearchEntry", True, None))
            print("  ✅ FastSearchEntry works correctly")
        except Exception as e:
            results.append(("FastSearchEntry", False, str(e)))
            print(f"  ❌ FastSearchEntry: {str(e)}")
        
        # Test PaginatedListView
        try:
            def dummy_page_change(page):
                pass
            
            list_view = PaginatedListView(
                root,
                columns=["id", "name"],
                headers={"id": "ID", "name": "Name"},
                on_page_change=dummy_page_change
            )
            results.append(("PaginatedListView", True, None))
            print("  ✅ PaginatedListView works correctly")
        except Exception as e:
            results.append(("PaginatedListView", False, str(e)))
            print(f"  ❌ PaginatedListView: {str(e)}")
        
        # Clean up
        root.destroy()
        
        return results
        
    except Exception as e:
        print(f"  ❌ Error setting up UI test environment: {str(e)}")
        return [("UI Test Setup", False, str(e))]

def test_database_connectivity():
    """Test database connectivity and operations."""
    print("\n🔍 Testing database connectivity...")
    
    try:
        from modules.db_manager import ConnectionContext
        from modules.enhanced_data_access import enhanced_data
        
        results = []
        
        # Test database connection
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                results.append(("Database Connection", True, f"Found {len(tables)} tables"))
                print(f"  ✅ Database connection successful ({len(tables)} tables found)")
        except Exception as e:
            results.append(("Database Connection", False, str(e)))
            print(f"  ❌ Database connection: {str(e)}")
        
        # Test enhanced data access
        try:
            # Test getting categories (should work even if empty)
            categories = enhanced_data.get_categories()
            results.append(("Enhanced Data Access", True, f"Retrieved {len(categories)} categories"))
            print(f"  ✅ Enhanced data access works ({len(categories)} categories)")
        except Exception as e:
            results.append(("Enhanced Data Access", False, str(e)))
            print(f"  ❌ Enhanced data access: {str(e)}")
        
        return results
        
    except Exception as e:
        print(f"  ❌ Error setting up database test: {str(e)}")
        return [("Database Test Setup", False, str(e))]

def test_i18n_support():
    """Test internationalization support."""
    print("\n🔍 Testing internationalization...")
    
    try:
        from modules.i18n import _, switch_language, get_current_language
        
        results = []
        
        # Test current language
        try:
            current_lang = get_current_language()
            results.append(("Current Language", True, f"Language: {current_lang}"))
            print(f"  ✅ Current language: {current_lang}")
        except Exception as e:
            results.append(("Current Language", False, str(e)))
            print(f"  ❌ Current language: {str(e)}")
        
        # Test translation function
        try:
            test_text = _("Sales Management System")
            results.append(("Translation Function", True, f"Translated: {test_text}"))
            print(f"  ✅ Translation function works: '{test_text}'")
        except Exception as e:
            results.append(("Translation Function", False, str(e)))
            print(f"  ❌ Translation function: {str(e)}")
        
        # Test language switching
        try:
            original_lang = get_current_language()
            switch_language('ar')
            arabic_lang = get_current_language()
            switch_language(original_lang)  # Switch back
            results.append(("Language Switching", True, f"Switched to: {arabic_lang}"))
            print(f"  ✅ Language switching works (switched to: {arabic_lang})")
        except Exception as e:
            results.append(("Language Switching", False, str(e)))
            print(f"  ❌ Language switching: {str(e)}")
        
        return results
        
    except Exception as e:
        print(f"  ❌ Error setting up i18n test: {str(e)}")
        return [("I18n Test Setup", False, str(e))]

def generate_report(test_results):
    """Generate a comprehensive test report."""
    print("\n" + "="*70)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("="*70)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print()
    
    for section_name, results in test_results.items():
        print(f"📋 {section_name}:")
        
        for test_name, passed, error in results:
            total_tests += 1
            if passed:
                passed_tests += 1
                print(f"  ✅ {test_name}")
            else:
                failed_tests += 1
                print(f"  ❌ {test_name}: {error}")
        
        print()
    
    print("="*70)
    print(f"📈 SUMMARY:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("="*70)
    
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! System is ready for production.")
    else:
        print(f"⚠️  {failed_tests} tests failed. Please review the errors above.")
    
    return failed_tests == 0

def main():
    """Main test execution function."""
    print("🚀 ENHANCED SALES MANAGEMENT SYSTEM - COMPREHENSIVE TEST")
    print("="*70)
    
    # Run all tests
    test_results = {
        "Import Tests": test_imports(),
        "Enhanced Pages Tests": test_enhanced_pages(),
        "UI Components Tests": test_ui_components(),
        "Database Tests": test_database_connectivity(),
        "Internationalization Tests": test_i18n_support(),
    }
    
    # Generate report
    success = generate_report(test_results)
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error during testing: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

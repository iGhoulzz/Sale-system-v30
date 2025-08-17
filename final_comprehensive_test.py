#!/usr/bin/env python3
"""
Final Comprehensive Test for Sales System Runtime Fixes
This script validates all fixes and ensures the application is ready for use.
"""

import sys
import os
import traceback
import time

def test_ui_components():
    """Test UI components with all fixes"""
    print("\n" + "="*50)
    print("TESTING UI COMPONENTS WITH FIXES")
    print("="*50)
    
    try:
        # Test PaginatedListView with enhanced constructor
        from modules.ui_components import PaginatedListView, ProgressDialog
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        # Test PaginatedListView with enhanced API
        listview = PaginatedListView(
            root,
            columns=["id", "name", "value"],
            headers={"id": "ID", "name": "Name", "value": "Value"},
            widths={"id": 50, "name": 100, "value": 80},
            on_page_change=lambda page: print(f"Page changed to {page}"),
            on_select=lambda item: print(f"Selected {item}"),
            height=10
        )
          # Test enhanced methods
        listview.pack()
        listview.update_items([
            {"id": "1", "name": "Test", "value": "100"},
            {"id": "2", "name": "Test2", "value": "200"}
        ], total_count=2, current_page=1, total_pages=1)
        
        frame = listview.get_frame()
        
        print("✓ PaginatedListView enhanced constructor: PASSED")
        print("✓ PaginatedListView enhanced methods: PASSED")
        
        # Test ProgressDialog with correct constructor
        progress = ProgressDialog(root, title="Test")
        progress.close()
        
        print("✓ ProgressDialog constructor: PASSED")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ UI Components test: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_enhanced_pages_import():
    """Test that enhanced pages import without errors"""
    print("\n" + "="*50)
    print("TESTING ENHANCED PAGES IMPORT")
    print("="*50)
    
    pages_to_test = [
        ("Enhanced Sales Page", "modules.pages.enhanced_sales_page"),
        ("Enhanced Inventory Page", "modules.pages.enhanced_inventory_page"),
        ("Enhanced Debits Page", "modules.pages.enhanced_debits_page")
    ]
    
    for page_name, module_name in pages_to_test:
        try:
            __import__(module_name)
            print(f"✓ {page_name}: IMPORTED SUCCESSFULLY")
        except Exception as e:
            print(f"✗ {page_name}: IMPORT FAILED - {str(e)}")
            return False
    
    return True

def test_enhanced_data_access():
    """Test enhanced data access methods"""
    print("\n" + "="*50)
    print("TESTING ENHANCED DATA ACCESS")
    print("="*50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        # Test that all required methods exist
        required_methods = [
            'get_debits_paged', 'add_debit', 'update_debit', 
            'delete_debit', 'mark_debit_as_paid', 'run_in_background'
        ]
        
        for method_name in required_methods:
            if hasattr(enhanced_data, method_name):
                print(f"✓ {method_name}: METHOD EXISTS")
            else:
                print(f"✗ {method_name}: METHOD MISSING")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Enhanced Data Access: FAILED - {str(e)}")
        return False

def test_main_application():
    """Test that main application can be created"""
    print("\n" + "="*50)
    print("TESTING MAIN APPLICATION")
    print("="*50)
    
    try:
        # Change to the application directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(app_dir)
        
        # Import main application
        from main import MainApp
        import tkinter as tk
        
        # Create root window
        root = tk.Tk()
        root.withdraw()
        
        # Create application instance
        app = MainApp(root)
        
        print("✓ MainApp creation: PASSED")
        
        # Test page registration
        if hasattr(app, 'frames') and app.frames:
            print("✓ Page registration: PASSED")
        else:
            print("✗ Page registration: FAILED")
            return False
        
        # Test enhanced pages flag
        if hasattr(app, 'use_enhanced_pages'):
            print(f"✓ Enhanced pages flag: {app.use_enhanced_pages}")
        else:
            print("✗ Enhanced pages flag: MISSING")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Main Application: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_navigation_fixes():
    """Test navigation method fixes"""
    print("\n" + "="*50)
    print("TESTING NAVIGATION FIXES")
    print("="*50)
    
    try:
        # Test enhanced inventory page navigation
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        class MockController:
            def show_frame(self, frame_name):
                return f"show_frame: {frame_name}"
        
        controller = MockController()
        page = EnhancedInventoryPage(root, controller)
        
        # Test back navigation method exists
        if hasattr(page, '_on_back_clicked'):
            print("✓ Enhanced Inventory Page navigation: PASSED")
        else:
            print("✗ Enhanced Inventory Page navigation: MISSING")
            return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Navigation fixes: FAILED - {str(e)}")
        return False

def run_final_validation():
    """Run final validation of all fixes"""
    print("="*60)
    print("FINAL COMPREHENSIVE TEST - SALES SYSTEM RUNTIME FIXES")
    print("="*60)
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("UI Components", test_ui_components),
        ("Enhanced Pages Import", test_enhanced_pages_import),
        ("Enhanced Data Access", test_enhanced_data_access),
        ("Main Application", test_main_application),
        ("Navigation Fixes", test_navigation_fixes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        if test_func():
            passed += 1
        
    print("\n" + "="*60)
    print("FINAL TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL RUNTIME FIXES ARE WORKING CORRECTLY!")
        print("✅ Application is ready for use")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        print("❌ Some fixes need attention")
        return False

if __name__ == "__main__":
    success = run_final_validation()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Simple test to validate runtime fixes
"""

import sys
import traceback

def test_imports():
    """Test that all modules import correctly"""
    print("Testing imports...")
    
    try:
        # Test UI components
        from modules.ui_components import PaginatedListView, ProgressDialog
        print("✓ UI Components imported successfully")
        
        # Test enhanced pages
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage  
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        print("✓ Enhanced pages imported successfully")
        
        # Test enhanced data access
        from modules.enhanced_data_access import enhanced_data
        print("✓ Enhanced data access imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        traceback.print_exc()
        return False

def test_ui_components():
    """Test UI components functionality"""
    print("Testing UI components...")
    
    try:
        import tkinter as tk
        from modules.ui_components import PaginatedListView, ProgressDialog
        
        root = tk.Tk()
        root.withdraw()
        
        # Test PaginatedListView with enhanced constructor
        listview = PaginatedListView(
            root,
            columns=["id", "name"],
            headers={"id": "ID", "name": "Name"},
            widths={"id": 50, "name": 100},
            on_page_change=lambda page: None,
            on_select=lambda item: None
        )
        
        # Test enhanced methods
        listview.pack()
        listview.update_items([], 0, 1, 1)
        frame = listview.get_frame()
        
        # Test ProgressDialog
        progress = ProgressDialog(root, title="Test")
        progress.close()
        
        root.destroy()
        print("✓ UI Components working correctly")
        return True
        
    except Exception as e:
        print(f"✗ UI Components test failed: {str(e)}")
        return False

def test_main_app():
    """Test main application creation"""
    print("Testing main application...")
    
    try:
        from main import MainApp
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        app = MainApp(root)
        
        root.destroy()
        print("✓ Main application created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Main application test failed: {str(e)}")
        return False

def main():
    print("="*50)
    print("RUNTIME FIXES VALIDATION")
    print("="*50)
    
    tests = [
        ("Imports", test_imports),
        ("UI Components", test_ui_components), 
        ("Main Application", test_main_app)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL RUNTIME FIXES WORKING!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    main()

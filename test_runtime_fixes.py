#!/usr/bin/env python3
"""
Test script to verify runtime fixes for the sales system application
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_pages_import():
    """Test that all enhanced pages can be imported without errors"""
    print("Testing enhanced pages import...")
    
    try:
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        print("✅ EnhancedSalesPage imports successfully")
    except Exception as e:
        print(f"❌ EnhancedSalesPage import failed: {e}")
        return False
    
    try:
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        print("✅ EnhancedDebitsPage imports successfully")
    except Exception as e:
        print(f"❌ EnhancedDebitsPage import failed: {e}")
        return False
    
    try:
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        print("✅ EnhancedInventoryPage imports successfully")
    except Exception as e:
        print(f"❌ EnhancedInventoryPage import failed: {e}")
        return False
    
    return True

def test_ui_components():
    """Test UI components import and basic functionality"""
    print("\nTesting UI components...")
    
    try:
        from modules.ui_components import PaginatedListView, ProgressDialog
        print("✅ UI components import successfully")
    except Exception as e:
        print(f"❌ UI components import failed: {e}")
        return False
    
    # Test ProgressDialog constructor
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Test ProgressDialog with correct parameters
        progress = ProgressDialog(root, title="Test", cancelable=False)
        progress.close()
        print("✅ ProgressDialog constructor works correctly")
        
        root.destroy()
    except Exception as e:
        print(f"❌ ProgressDialog constructor failed: {e}")
        return False
    
    return True

def test_main_application_creation():
    """Test that MainApp can be created without constructor errors"""
    print("\nTesting main application creation...")
    
    try:
        # Import the main application
        from main import MainApp
        
        # Create a root window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Try to create MainApp instance
        app = MainApp(root)
        print("✅ MainApp created successfully")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ MainApp creation failed: {e}")
        return False

def test_enhanced_pages_initialization():
    """Test that enhanced pages can be initialized without TTK errors"""
    print("\nTesting enhanced pages initialization...")
    
    try:
        # Create a mock controller
        class MockController:
            def show_frame(self, page_name):
                pass
            
            def get_current_user(self):
                return {"Username": "test_user"}
        
        root = tk.Tk()
        root.withdraw()
        
        controller = MockController()
        
        # Test EnhancedSalesPage initialization
        try:
            from modules.pages.enhanced_sales_page import EnhancedSalesPage
            sales_page = EnhancedSalesPage(root, controller)
            print("✅ EnhancedSalesPage initialized successfully")
        except Exception as e:
            print(f"❌ EnhancedSalesPage initialization failed: {e}")
            return False
        
        # Test EnhancedDebitsPage initialization  
        try:
            from modules.pages.enhanced_debits_page import EnhancedDebitsPage
            debits_page = EnhancedDebitsPage(root, controller)
            print("✅ EnhancedDebitsPage initialized successfully")
        except Exception as e:
            print(f"❌ EnhancedDebitsPage initialization failed: {e}")
            return False
        
        # Test EnhancedInventoryPage initialization
        try:
            from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
            inventory_page = EnhancedInventoryPage(root, controller)
            print("✅ EnhancedInventoryPage initialized successfully")
        except Exception as e:
            print(f"❌ EnhancedInventoryPage initialization failed: {e}")
            return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Enhanced pages initialization test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing Runtime Fixes for Sales System Application")
    print("=" * 60)
    
    tests = [
        test_enhanced_pages_import,
        test_ui_components,
        test_main_application_creation,
        test_enhanced_pages_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All runtime fixes are working correctly!")
        print("✅ The application should now start without constructor/TTK errors")
    else:
        print("⚠️  Some issues remain that need to be addressed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

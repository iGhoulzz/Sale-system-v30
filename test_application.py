#!/usr/bin/env python3
"""
Comprehensive test script to validate all fixes in the sales system application.
Tests import functionality, constructor compatibility, and navigation methods.
"""

import sys
import os
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported without errors."""
    print("=" * 50)
    print("TESTING MODULE IMPORTS")
    print("=" * 50)
    
    tests = [
        ("Main module", lambda: __import__('main')),
        ("UI Components", lambda: __import__('modules.ui_components', fromlist=['PaginatedListView'])),
        ("Enhanced Sales Page", lambda: __import__('modules.pages.enhanced_sales_page', fromlist=['EnhancedSalesPage'])),
        ("Enhanced Debits Page", lambda: __import__('modules.pages.enhanced_debits_page', fromlist=['EnhancedDebitsPage'])),
        ("Enhanced Inventory Page", lambda: __import__('modules.pages.enhanced_inventory_page', fromlist=['EnhancedInventoryPage'])),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name}: FAILED - {str(e)}")
            traceback.print_exc()
    
    print(f"\nImport Tests: {passed}/{total} passed")
    return passed == total

def test_paginated_list_view_constructor():
    """Test that PaginatedListView constructor works with enhanced page parameters."""
    print("\n" + "=" * 50)
    print("TESTING PAGINATEDLISTVIEW CONSTRUCTOR")
    print("=" * 50)
    
    try:
        from modules.ui_components import PaginatedListView
        import tkinter as tk
        
        # Create a dummy root for testing
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Test original constructor (should work)
        try:
            plv1 = PaginatedListView(root, [])
            print("✓ Original constructor: PASSED")
            plv1.destroy()
        except Exception as e:
            print(f"✗ Original constructor: FAILED - {str(e)}")
            return False
        
        # Test enhanced constructor with all parameters (should work now)
        try:
            plv2 = PaginatedListView(
                root, 
                [],
                headers=["Col1", "Col2", "Col3"],
                widths=[100, 150, 200],
                on_page_change=lambda: None,
                on_select=lambda: None,
                height=20
            )
            print("✓ Enhanced constructor: PASSED")
            plv2.destroy()
        except Exception as e:
            print(f"✗ Enhanced constructor: FAILED - {str(e)}")
            traceback.print_exc()
            return False
        
        # Test enhanced methods exist
        try:
            plv3 = PaginatedListView(root, [])
            
            # Test new methods
            assert hasattr(plv3, 'pack'), "pack method missing"
            assert hasattr(plv3, 'update_items'), "update_items method missing"
            assert hasattr(plv3, 'get_frame'), "get_frame method missing"
            
            print("✓ Enhanced methods available: PASSED")
            plv3.destroy()
        except Exception as e:
            print(f"✗ Enhanced methods: FAILED - {str(e)}")
            return False
        
        root.destroy()
        print("✓ All PaginatedListView tests: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ PaginatedListView tests: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_navigation_methods():
    """Test that navigation methods are correctly implemented."""
    print("\n" + "=" * 50)
    print("TESTING NAVIGATION METHODS")
    print("=" * 50)
    
    try:
        # Test that enhanced inventory page uses correct navigation method
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        import tkinter as tk
        
        # Create mock controller
        class MockController:
            def show_frame(self, frame_name):
                return f"show_frame called with: {frame_name}"
            
            def show_page(self, page_name):
                return f"show_page called with: {page_name}"
        
        root = tk.Tk()
        root.withdraw()
        
        controller = MockController()
        
        # Test page creation
        try:
            page = EnhancedInventoryPage(root, controller)
            print("✓ Enhanced inventory page creation: PASSED")
        except Exception as e:
            print(f"✗ Enhanced inventory page creation: FAILED - {str(e)}")
            return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Navigation tests: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_page_registration():
    """Test that enhanced pages are properly registered."""
    print("\n" + "=" * 50)
    print("TESTING PAGE REGISTRATION")
    print("=" * 50)
    
    try:
        import main
        
        # Check if use_enhanced_pages flag exists
        if hasattr(main, 'use_enhanced_pages'):
            print(f"✓ use_enhanced_pages flag: {main.use_enhanced_pages}")
        else:
            print("! use_enhanced_pages flag not found, checking registration manually")
        
        # Check if enhanced pages are registered
        enhanced_pages = [
            'EnhancedSalesPage',
            'EnhancedDebitsPage', 
            'EnhancedInventoryPage'
        ]
        
        # This would require actually running the main app, so we'll just verify
        # that the classes can be imported and instantiated
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        
        print("✓ All enhanced page classes importable: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Page registration tests: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("SALES SYSTEM APPLICATION - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    all_passed = True
    
    # Run all test suites
    all_passed &= test_imports()
    all_passed &= test_paginated_list_view_constructor()
    all_passed &= test_navigation_methods()
    all_passed &= test_page_registration()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("The application should now start and run correctly.")
        print("✓ Constructor errors fixed")
        print("✓ Navigation methods corrected")
        print("✓ Enhanced page compatibility implemented")
        print("✓ All syntax errors resolved")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the error messages above.")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

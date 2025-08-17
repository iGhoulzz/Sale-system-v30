#!/usr/bin/env python3
"""
Test script to verify the fixes for FastSearchEntry and i18n issues
"""

import sys
import os

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        # Test core modules
        from modules.enhanced_data_access import enhanced_data
        print("✓ Enhanced data access module imported successfully")
        
        from modules.ui_components import FastSearchEntry
        print("✓ UI components module imported successfully")
        
        from modules.i18n import _
        print("✓ i18n module imported successfully")
        
        # Test enhanced pages
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        print("✓ Enhanced sales page imported successfully")
        
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        print("✓ Enhanced debits page imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_fastsearchentry_constructor():
    """Test that FastSearchEntry constructor works with our parameters"""
    print("\nTesting FastSearchEntry constructor...")
    
    try:
        import tkinter as tk
        from modules.ui_components import FastSearchEntry
        
        # Create a test root window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Test search function
        def test_search(term):
            return [{'id': '1', 'display': f'Test result for {term}'}]
        
        # Test callback function
        def test_callback(result):
            print(f"Selected: {result}")
        
        # Try to create FastSearchEntry with our parameters
        entry = FastSearchEntry(
            root,
            search_function=test_search,
            on_select_callback=test_callback
        )
        
        print("✓ FastSearchEntry constructor works correctly")
        
        # Test that it has the required methods
        assert hasattr(entry, 'get_frame'), "Missing get_frame method"
        assert hasattr(entry, 'set_value'), "Missing set_value method"
        print("✓ FastSearchEntry has required methods")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ FastSearchEntry constructor error: {e}")
        return False

def test_enhanced_data_methods():
    """Test that enhanced data access has required methods"""
    print("\nTesting enhanced data access methods...")
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        # Check for required methods
        required_methods = [
            'search_products_fast',
            'search_debits',
            'get_debits_paged',
            'add_debit',
            'update_debit',
            'delete_debit',
            'mark_debit_as_paid'
        ]
        
        for method_name in required_methods:
            if hasattr(enhanced_data, method_name):
                print(f"✓ {method_name} method exists")
            else:
                print(f"✗ {method_name} method missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Enhanced data access error: {e}")
        return False

def test_i18n_callback_safety():
    """Test that i18n callback system is working"""
    print("\nTesting i18n callback system...")
    
    try:
        from modules.i18n import register_refresh_callback, unregister_refresh_callback
        
        # Test callback registration
        def test_callback():
            pass
        
        register_refresh_callback(test_callback)
        print("✓ Callback registration works")
        
        unregister_refresh_callback(test_callback)
        print("✓ Callback unregistration works")
        
        return True
        
    except Exception as e:
        print(f"✗ i18n callback error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING FASTSEARCHENTRY AND I18N FIXES")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_fastsearchentry_constructor,
        test_enhanced_data_methods,
        test_i18n_callback_safety
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The fixes appear to be working correctly.")
    else:
        print("❌ Some tests failed. Please review the output above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

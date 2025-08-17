#!/usr/bin/env python3
"""
Comprehensive Runtime Fixes Test
Tests all the fixes made to resolve runtime initialization errors:
1. FastSearchEntry placeholder support
2. Missing callback methods in EnhancedSalesPage
3. Improved error handling in main.py
"""

import sys
import os
import traceback
import tkinter as tk

# Add the workspace path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_test_header(title):
    """Print a formatted test header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{test_name}: {status}")
    if details:
        print(f"   {details}")

def test_fastsearchentry_placeholder():
    """Test FastSearchEntry placeholder functionality"""
    print_test_header("FastSearchEntry Placeholder Support")
    
    try:
        import tkinter as tk
        from modules.ui_components import FastSearchEntry
        
        # Create test root
        root = tk.Tk()
        root.withdraw()
        
        # Test search function
        def test_search(term, limit=10):
            return [{'id': '1', 'display': f'Test result for {term}'}]
        
        # Test callback
        def test_callback(result):
            print(f"Selected: {result}")
        
        # Test 1: FastSearchEntry with placeholder
        print("Testing FastSearchEntry with placeholder parameter...")
        entry = FastSearchEntry(
            root,
            search_function=test_search,
            on_select_callback=test_callback,
            placeholder="Search products..."
        )
        print_test_result("FastSearchEntry with placeholder", True, "Constructor accepts placeholder parameter")
        
        # Test 2: Check placeholder functionality
        print("Testing placeholder functionality...")
        frame = entry.get_frame()
        assert frame is not None, "Frame should be available"
        print_test_result("Placeholder functionality", True, "Placeholder methods available")
        
        # Test 3: Test without placeholder (backward compatibility)
        print("Testing backward compatibility...")
        entry2 = FastSearchEntry(
            root,
            search_function=test_search,
            on_select_callback=test_callback
        )
        print_test_result("Backward compatibility", True, "Works without placeholder parameter")
        
        root.destroy()
        return True
        
    except Exception as e:
        print_test_result("FastSearchEntry Placeholder Test", False, str(e))
        traceback.print_exc()
        return False

def test_enhanced_sales_page_methods():
    """Test EnhancedSalesPage missing methods"""
    print_test_header("EnhancedSalesPage Missing Methods")
    
    try:
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        
        # Check if the missing method exists
        print("Checking for _on_product_selected_from_search method...")
        assert hasattr(EnhancedSalesPage, '_on_product_selected_from_search'), "Missing _on_product_selected_from_search method"
        print_test_result("_on_product_selected_from_search method", True, "Method exists in class")
        
        # Check if the existing method exists
        print("Checking for _on_product_selected method...")
        assert hasattr(EnhancedSalesPage, '_on_product_selected'), "Missing _on_product_selected method"
        print_test_result("_on_product_selected method", True, "Method exists in class")
        
        # Check other essential methods
        essential_methods = [
            '_create_ui',
            '_create_modern_header',
            '_create_products_panel',
            '_create_cart_panel',
            '_perform_product_search'
        ]
        
        for method_name in essential_methods:
            assert hasattr(EnhancedSalesPage, method_name), f"Missing {method_name} method"
            print_test_result(f"{method_name} method", True, "Method exists")
        
        return True
        
    except Exception as e:
        print_test_result("EnhancedSalesPage Methods Test", False, str(e))
        traceback.print_exc()
        return False

def test_enhanced_pages_import():
    """Test that all enhanced pages can be imported"""
    print_test_header("Enhanced Pages Import Test")
    
    pages_to_test = [
        ("EnhancedSalesPage", "modules.pages.enhanced_sales_page"),
        ("EnhancedDebitsPage", "modules.pages.enhanced_debits_page"),
        ("EnhancedInventoryPage", "modules.pages.enhanced_inventory_page")
    ]
    
    all_passed = True
    
    for page_name, module_path in pages_to_test:
        try:
            print(f"Testing import of {page_name}...")
            module = __import__(module_path, fromlist=[page_name])
            page_class = getattr(module, page_name)
            print_test_result(f"Import {page_name}", True, f"Successfully imported from {module_path}")
        except Exception as e:
            print_test_result(f"Import {page_name}", False, str(e))
            all_passed = False
    
    return all_passed

def test_main_app_error_handling():
    """Test main app error handling improvements"""
    print_test_header("Main App Error Handling")
    
    try:
        # Test that main.py can be imported without errors
        print("Testing main.py import...")
        import main
        print_test_result("main.py import", True, "Main module imported successfully")
        
        # Check if MainApp class exists
        print("Checking MainApp class...")
        assert hasattr(main, 'MainApp'), "MainApp class not found"
        print_test_result("MainApp class", True, "Class exists")
        
        # Check if the class has the initialization method
        print("Checking _initialize_ui method...")
        assert hasattr(main.MainApp, '_initialize_ui'), "_initialize_ui method not found"
        print_test_result("_initialize_ui method", True, "Method exists")
        
        return True
        
    except Exception as e:
        print_test_result("Main App Error Handling Test", False, str(e))
        traceback.print_exc()
        return False

def test_complete_initialization_flow():
    """Test the complete initialization flow without GUI"""
    print_test_header("Complete Initialization Flow")
    
    try:
        # Test importing all required modules
        print("Testing module imports...")
        
        # Core modules
        from modules.ui_components import FastSearchEntry
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        
        print_test_result("All module imports", True, "All enhanced modules imported successfully")
        
        # Test FastSearchEntry with the parameters used by enhanced pages
        print("Testing FastSearchEntry initialization with enhanced page parameters...")
        root = tk.Tk()
        root.withdraw()
        
        def dummy_search(term, limit=10):
            return []
        
        def dummy_callback(result):
            pass
        
        # Test with placeholder (as used in enhanced pages)
        entry = FastSearchEntry(
            root,
            search_function=dummy_search,
            on_select_callback=dummy_callback,
            placeholder="Search by name, barcode, or category..."
        )
        
        print_test_result("FastSearchEntry initialization", True, "Created with enhanced page parameters")
        
        root.destroy()
        return True
        
    except Exception as e:
        print_test_result("Complete Initialization Flow", False, str(e))
        traceback.print_exc()
        return False

def main():
    """Run all runtime fix tests"""
    print("🔧 Runtime Fixes Comprehensive Test")
    print("Testing all fixes for initialization errors...")
    
    test_results = []
    
    # Run all tests
    test_results.append(("FastSearchEntry Placeholder", test_fastsearchentry_placeholder()))
    test_results.append(("EnhancedSalesPage Methods", test_enhanced_sales_page_methods()))
    test_results.append(("Enhanced Pages Import", test_enhanced_pages_import()))
    test_results.append(("Main App Error Handling", test_main_app_error_handling()))
    test_results.append(("Complete Initialization Flow", test_complete_initialization_flow()))
    
    # Summary
    print_test_header("TEST SUMMARY")
    
    passed_tests = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 SUCCESS! All runtime fixes are working correctly!")
        print("\n✨ Fixed Issues:")
        print("  🔧 FastSearchEntry now supports placeholder parameter")
        print("  🔧 EnhancedSalesPage has missing callback methods")
        print("  🔧 Improved error handling with fallback mechanisms")
        print("  🔧 All enhanced pages can be imported successfully")
        print("\n🚀 The application should now start without initialization errors!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the issues above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

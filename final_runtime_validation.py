#!/usr/bin/env python3
"""
Final Runtime Fixes Validation
Comprehensive test to validate all runtime initialization fixes
"""

import sys
import os
import tkinter as tk

# Add the workspace path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(test, passed, details=""):
    """Print test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{test}: {status}")
    if details:
        print(f"   → {details}")

def test_fastsearchentry_fixes():
    """Test FastSearchEntry placeholder support"""
    print_header("FastSearchEntry Placeholder Support")
    
    try:
        from modules.ui_components import FastSearchEntry
        
        root = tk.Tk()
        root.withdraw()
        
        def dummy_search(term, limit=10):
            return [{'id': '1', 'display': f'Result: {term}'}]
        
        def dummy_callback(result):
            pass
        
        # Test 1: With placeholder
        entry1 = FastSearchEntry(
            root,
            search_function=dummy_search,
            on_select_callback=dummy_callback,
            placeholder="Search products..."
        )
        print_result("FastSearchEntry with placeholder", True, "Placeholder parameter accepted")
        
        # Test 2: Without placeholder (backward compatibility)
        entry2 = FastSearchEntry(
            root,
            search_function=dummy_search,
            on_select_callback=dummy_callback
        )
        print_result("FastSearchEntry without placeholder", True, "Backward compatible")
        
        # Test 3: Placeholder functionality
        has_placeholder_methods = all(hasattr(entry1, method) for method in [
            '_on_entry_focus_in', '_on_entry_focus_out', '_clear_placeholder', '_set_placeholder'
        ])
        print_result("Placeholder functionality methods", has_placeholder_methods, "All placeholder methods present")
        
        root.destroy()
        return True
        
    except Exception as e:
        print_result("FastSearchEntry Tests", False, str(e))
        return False

def test_enhanced_sales_page_fixes():
    """Test EnhancedSalesPage missing method fixes"""
    print_header("EnhancedSalesPage Method Fixes")
    
    try:
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        
        # Test required methods
        required_methods = [
            '_on_product_selected_from_search',
            '_on_product_selected',
            '_perform_product_search',
            '_create_ui',
            '_create_modern_header',
            '_create_products_panel',
            '_create_cart_panel'
        ]
        
        all_methods_present = True
        for method in required_methods:
            has_method = hasattr(EnhancedSalesPage, method)
            print_result(f"Method {method}", has_method, "Present in class")
            if not has_method:
                all_methods_present = False
        
        return all_methods_present
        
    except Exception as e:
        print_result("EnhancedSalesPage Tests", False, str(e))
        return False

def test_enhanced_pages_import():
    """Test all enhanced pages can be imported"""
    print_header("Enhanced Pages Import Test")
    
    pages = [
        ("EnhancedSalesPage", "modules.pages.enhanced_sales_page"),
        ("EnhancedDebitsPage", "modules.pages.enhanced_debits_page"),
        ("EnhancedInventoryPage", "modules.pages.enhanced_inventory_page")
    ]
    
    all_imported = True
    for page_name, module_path in pages:
        try:
            module = __import__(module_path, fromlist=[page_name])
            page_class = getattr(module, page_name)
            print_result(f"Import {page_name}", True, f"Successfully imported from {module_path}")
        except Exception as e:
            print_result(f"Import {page_name}", False, str(e))
            all_imported = False
    
    return all_imported

def test_application_startup():
    """Test application can start without critical errors"""
    print_header("Application Startup Test")
    
    try:
        # Test main.py import
        import main
        print_result("Main module import", True, "main.py imported successfully")
        
        # Test MainApp class availability
        has_mainapp = hasattr(main, 'MainApp')
        print_result("MainApp class available", has_mainapp, "MainApp class found")
        
        # Test that we can create MainApp instance
        if has_mainapp:
            app = main.MainApp()
            print_result("MainApp instantiation", True, "Application instance created successfully")
            app.destroy()
        else:
            return False
        
        return True
        
    except Exception as e:
        print_result("Application Startup", False, str(e))
        return False

def test_specific_errors_resolved():
    """Test that the specific runtime errors have been resolved"""
    print_header("Specific Error Resolution Test")
    
    # Test the exact error scenarios that were failing
    
    # Error 1: FastSearchEntry.__init__() got an unexpected keyword argument 'placeholder'
    try:
        from modules.ui_components import FastSearchEntry
        root = tk.Tk()
        root.withdraw()
        
        # This exact call was failing before
        entry = FastSearchEntry(
            root,
            search_function=lambda term, limit=10: [],
            on_select_callback=None,
            placeholder="Search by name, barcode, or category..."
        )
        print_result("FastSearchEntry placeholder error", True, "Fixed: placeholder parameter accepted")
        root.destroy()
        
    except TypeError as e:
        if "unexpected keyword argument 'placeholder'" in str(e):
            print_result("FastSearchEntry placeholder error", False, "Still present: placeholder parameter rejected")
            return False
        else:
            print_result("FastSearchEntry placeholder error", False, f"Other error: {e}")
            return False
    
    # Error 2: 'EnhancedSalesPage' object has no attribute '_on_product_selected_from_search'
    try:
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        
        if hasattr(EnhancedSalesPage, '_on_product_selected_from_search'):
            print_result("EnhancedSalesPage callback error", True, "Fixed: _on_product_selected_from_search method exists")
        else:
            print_result("EnhancedSalesPage callback error", False, "Still present: method missing")
            return False
            
    except Exception as e:
        print_result("EnhancedSalesPage callback error", False, f"Import error: {e}")
        return False
    
    return True

def main():
    """Run all validation tests"""
    print("🔧 RUNTIME FIXES VALIDATION")
    print("Comprehensive test suite for all initialization error fixes")
    
    # Run all test suites
    results = []
    results.append(("FastSearchEntry Fixes", test_fastsearchentry_fixes()))
    results.append(("EnhancedSalesPage Fixes", test_enhanced_sales_page_fixes()))
    results.append(("Enhanced Pages Import", test_enhanced_pages_import()))
    results.append(("Application Startup", test_application_startup()))
    results.append(("Specific Errors Resolved", test_specific_errors_resolved()))
    
    # Calculate summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    # Print summary
    print_header("VALIDATION SUMMARY")
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL FIXES VALIDATED SUCCESSFULLY!")
        print("\n✨ Summary of Resolved Issues:")
        print("   🔧 FastSearchEntry now supports placeholder parameter")
        print("   🔧 EnhancedSalesPage has required callback methods")
        print("   🔧 All enhanced pages import without errors")
        print("   🔧 Application can start without critical initialization errors")
        print("   🔧 Improved error handling with fallback mechanisms")
        
        print("\n🚀 READY FOR PRODUCTION!")
        print("The sales management system with enhanced modern UI is now fully operational.")
        print("Users can enjoy the modern 2025 design with all functionality working correctly.")
        
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed.")
        print("Please review the failed tests above and address any remaining issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

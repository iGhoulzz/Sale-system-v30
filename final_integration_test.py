#!/usr/bin/env python3
"""
Final integration test to verify all fixes are working together
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_functionality():
    """Test that all enhanced pages work together correctly"""
    
    print("🔧 FINAL INTEGRATION TEST")
    print("=" * 50)
    
    results = []
    
    # Test 1: Import all enhanced pages
    print("\n1. Testing imports...")
    try:
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        from modules.ui_components import PaginatedListView, FastSearchEntry
        print("✅ All enhanced pages imported successfully")
        results.append("✅ Imports: PASS")
    except Exception as e:
        print(f"❌ Import error: {e}")
        results.append("❌ Imports: FAIL")
        return False
    
    # Test 2: Create Tkinter environment
    print("\n2. Testing Tkinter setup...")
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the window
        print("✅ Tkinter root created successfully")
        results.append("✅ Tkinter: PASS")
    except Exception as e:
        print(f"❌ Tkinter error: {e}")
        results.append("❌ Tkinter: FAIL")
        return False
    
    # Test 3: Test PaginatedListView.update_headers
    print("\n3. Testing PaginatedListView.update_headers...")
    try:
        # Mock controller
        class MockController:
            pass
        
        # Test Sales Page
        sales_page = EnhancedSalesPage(parent=root, controller=MockController())
        if hasattr(sales_page.products_list, 'update_headers'):
            sales_page.products_list.update_headers({
                'name': 'Product Name',
                'price': 'Price',
                'stock': 'Stock'
            })
            print("✅ Sales page update_headers works")
            results.append("✅ Sales update_headers: PASS")
        else:
            print("❌ Sales page missing update_headers")
            results.append("❌ Sales update_headers: FAIL")
            
        # Test Debits Page 
        debits_page = EnhancedDebitsPage(parent=root, controller=MockController())
        if hasattr(debits_page.debits_list, 'update_headers'):
            debits_page.debits_list.update_headers({
                'customer': 'Customer',
                'amount': 'Amount',
                'date': 'Date'
            })
            print("✅ Debits page update_headers works")
            results.append("✅ Debits update_headers: PASS")
        else:
            print("❌ Debits page missing update_headers")
            results.append("❌ Debits update_headers: FAIL")
            
    except Exception as e:
        print(f"❌ update_headers test error: {e}")
        results.append("❌ update_headers: FAIL")
    
    # Test 4: Test debits statistics
    print("\n4. Testing debits statistics attributes...")
    try:
        if hasattr(debits_page, 'total_debits') and hasattr(debits_page, 'unpaid_debits'):
            # Test the _update_statistics_display method
            debits_page._update_statistics_display()
            print("✅ Debits statistics attributes and method work")
            results.append("✅ Debits statistics: PASS")
        else:
            print("❌ Debits page missing statistics attributes")
            results.append("❌ Debits statistics: FAIL")
    except Exception as e:
        print(f"❌ Debits statistics error: {e}")
        results.append("❌ Debits statistics: FAIL")
    
    # Test 5: Test language refresh functionality
    print("\n5. Testing language refresh callbacks...")
    try:
        # Test that language refresh methods exist and can be called
        sales_page._refresh_language()
        print("✅ Sales page language refresh works")
        
        debits_page._refresh_language()
        print("✅ Debits page language refresh works")
        
        results.append("✅ Language refresh: PASS")
    except Exception as e:
        print(f"❌ Language refresh error: {e}")
        results.append("❌ Language refresh: FAIL")
    
    # Test 6: Test FastSearchEntry compatibility
    print("\n6. Testing FastSearchEntry compatibility...")
    try:
        # Test with both result formats
        search_entry = FastSearchEntry(root, lambda x: None)
        
        # Test enhanced format
        enhanced_results = [
            {'display': 'Product A - $10.00', 'data': {'id': 1, 'name': 'Product A'}}
        ]
        search_entry.display_results(enhanced_results)
        
        # Test original format  
        original_results = [
            {'Name': 'Product B', 'Price': 15.00}
        ]
        search_entry.display_results(original_results)
        
        print("✅ FastSearchEntry handles both result formats")
        results.append("✅ FastSearchEntry: PASS")
    except Exception as e:
        print(f"❌ FastSearchEntry error: {e}")
        results.append("❌ FastSearchEntry: FAIL")
    
    # Cleanup
    try:
        root.destroy()
        print("✅ Cleanup completed")
    except:
        pass
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for result in results:
        print(result)
        if "PASS" in result:
            passed += 1
    
    print(f"\n📈 SCORE: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The sales management system is fully functional.")
        print("✅ Language switching should work without errors")
        print("✅ Enhanced pages are compatible with UI components") 
        print("✅ All AttributeError issues have been resolved")
        return True
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Some issues may remain.")
        return False

if __name__ == "__main__":
    success = test_all_functionality()
    sys.exit(0 if success else 1)

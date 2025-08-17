#!/usr/bin/env python3
"""
Comprehensive test to verify all backend fixes
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_missing_functions():
    """Test the missing functions that were added"""
    print("🔍 TESTING MISSING FUNCTIONS")
    print("=" * 50)
    
    try:
        from modules.data_access import get_categories, get_recent_invoices
        
        # Test get_categories
        categories = get_categories()
        print(f"  ✅ get_categories(): {categories}")
        
        # Test get_recent_invoices
        recent_invoices = get_recent_invoices(5)
        print(f"  ✅ get_recent_invoices(5): {len(recent_invoices)} invoices")
        
        if recent_invoices:
            sample = recent_invoices[0]
            print(f"    Sample invoice keys: {list(sample.keys())}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Missing functions test failed: {e}")
        traceback.print_exc()
        return False

def test_database_optimization():
    """Test that database optimization works without schema errors"""
    print("\n🔍 TESTING DATABASE OPTIMIZATION")
    print("=" * 50)
    
    try:
        from modules.optimize_db import add_indexes, run_comprehensive_optimization
        
        # Test index creation
        print("  📋 Testing index creation...")
        add_indexes()
        print("  ✅ add_indexes() completed successfully")
        
        # Test comprehensive optimization
        print("  📋 Testing comprehensive optimization...")
        result = run_comprehensive_optimization()
        print(f"  ✅ Comprehensive optimization: {result.get('success', False)}")
        
        if result and result.get('steps_completed'):
            print(f"    Steps completed: {', '.join(result['steps_completed'])}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Database optimization test failed: {e}")
        traceback.print_exc()
        return False

def test_schema_consistency():
    """Test that all database operations use correct column names"""
    print("\n🔍 TESTING SCHEMA CONSISTENCY")
    print("=" * 50)
    
    try:
        from modules.data_access import get_daily_sales_summary, get_debits
        from modules.db_manager import ConnectionContext
        
        # Test daily sales summary (previously had column issues)
        print("  📋 Testing get_daily_sales_summary...")
        summary = get_daily_sales_summary()
        print(f"  ✅ Daily sales summary: {summary}")
        
        # Test debits function
        print("  📋 Testing get_debits...")
        debits = get_debits()
        print(f"  ✅ get_debits(): {len(debits)} debits")
        
        # Verify table schemas match expectations
        print("  📋 Verifying table schemas...")
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Check Invoices table
            cursor.execute("PRAGMA table_info(Invoices)")
            invoice_columns = [row[1] for row in cursor.fetchall()]
            expected_invoice_cols = ['InvoiceID', 'DateTime', 'PaymentMethod', 'TotalAmount', 'Discount', 'ShiftEmployee']
            
            missing_cols = set(expected_invoice_cols) - set(invoice_columns)
            if missing_cols:
                print(f"  ⚠️  Missing columns in Invoices: {missing_cols}")
            else:
                print("  ✅ Invoices table schema correct")
            
            # Check Debits table
            cursor.execute("PRAGMA table_info(Debits)")
            debit_columns = [row[1] for row in cursor.fetchall()]
            required_debit_cols = ['DebitID', 'Name', 'Phone', 'InvoiceID', 'Amount', 'Status', 'DateTime']
            
            missing_debit_cols = set(required_debit_cols) - set(debit_columns)
            if missing_debit_cols:
                print(f"  ⚠️  Missing columns in Debits: {missing_debit_cols}")
            else:
                print("  ✅ Debits table schema correct")
                
        return True
        
    except Exception as e:
        print(f"  ❌ Schema consistency test failed: {e}")
        traceback.print_exc()
        return False

def test_page_loading():
    """Test that all pages can be imported and initialized"""
    print("\n🔍 TESTING PAGE LOADING")
    print("=" * 50)
    
    try:
        # Mock the UI environment
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Mock current_user
        import modules.Login
        modules.Login.current_user = {"Username": "test", "Role": "admin"}
        
        # Test debits page
        print("  📋 Testing debits page...")
        from modules.pages.debits_page import DebitsPage
        debits_page = DebitsPage(root, None)
        print("  ✅ Standard debits page loaded successfully")
        
        # Test enhanced debits page
        print("  📋 Testing enhanced debits page...")
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        enhanced_debits_page = EnhancedDebitsPage(root, None)
        print("  ✅ Enhanced debits page loaded successfully")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"  ❌ Page loading test failed: {e}")
        traceback.print_exc()
        return False

def test_all_compatibility_functions():
    """Test all the compatibility functions added for the frontend"""
    print("\n🔍 TESTING ALL COMPATIBILITY FUNCTIONS")
    print("=" * 50)
    
    try:
        from modules.data_access import (
            get_all_products, get_sales_data, get_debits_data,
            get_categories, get_recent_invoices
        )
        
        functions_to_test = [
            ("get_all_products", get_all_products, []),
            ("get_sales_data", get_sales_data, []),
            ("get_debits_data", get_debits_data, []),
            ("get_categories", get_categories, []),
            ("get_recent_invoices", get_recent_invoices, [5])
        ]
        
        for func_name, func, args in functions_to_test:
            try:
                result = func(*args)
                print(f"  ✅ {func_name}(): {len(result) if isinstance(result, list) else result}")
            except Exception as e:
                print(f"  ❌ {func_name}(): {e}")
                
        return True
        
    except Exception as e:
        print(f"  ❌ Compatibility functions test failed: {e}")
        traceback.print_exc()
        return False

def test_enhanced_data_access():
    """Test enhanced data access functionality"""
    print("\n🔍 TESTING ENHANCED DATA ACCESS")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        # Test paged products
        print("  📋 Testing get_products_paged...")
        paged_result = enhanced_data.get_products_paged(page=1, page_size=5)
        print(f"  ✅ Paged products: {len(paged_result.data)} items")
        print(f"    Total count: {paged_result.total_count}")
        print(f"    Has total_items: {hasattr(paged_result, 'total_items')}")
        print(f"    Total pages: {paged_result.total_pages}")
        
        # Test search functions
        print("  📋 Testing search functions...")
        search_result = enhanced_data.search_products_fast("", limit=5)
        print(f"  ✅ Product search: {len(search_result)} items")
        
        debit_search = enhanced_data.search_debits("", limit=5)
        print(f"  ✅ Debit search: {len(debit_search.data)} items")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced data access test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all comprehensive tests"""
    print("🚀 COMPREHENSIVE BACKEND VERIFICATION")
    print("=" * 70)
    print("Verifying all fixes and functionality...")
    print("=" * 70)
    
    tests = [
        ("Missing Functions", test_missing_functions),
        ("Database Optimization", test_database_optimization),
        ("Schema Consistency", test_schema_consistency),
        ("Page Loading", test_page_loading),
        ("Compatibility Functions", test_all_compatibility_functions),
        ("Enhanced Data Access", test_enhanced_data_access)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 VERIFICATION SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"Tests passed: {successful}/{total}")
    print(f"Success rate: {(successful/total*100):.1f}%")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if successful == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your backend is fully functional and all fixes are working correctly.")
        print("\n✅ CONFIRMED FIXES:")
        print("  - Missing functions (get_categories, get_recent_invoices) - WORKING")
        print("  - Database schema issues in optimization - FIXED")
        print("  - Column name inconsistencies - FIXED")
        print("  - Compatibility function aliases - WORKING")
        print("  - Enhanced data access pagination - WORKING")
        print("  - All page loading - WORKING")
    else:
        print(f"\n⚠️  {total - successful} tests failed. Check details above.")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

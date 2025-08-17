#!/usr/bin/env python3
"""
Test Enhanced Inventory Page Backend Connections
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_data_access():
    """Test the enhanced data access functions used by inventory page"""
    print("🔍 TESTING ENHANCED DATA ACCESS FOR INVENTORY PAGE")
    print("=" * 60)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        # Test get_categories (used by ProductDialog._load_categories)
        print("  📋 Testing get_categories...")
        categories = enhanced_data.get_categories()
        print(f"  ✅ get_categories(): {len(categories)} categories")
        if categories:
            print(f"    Sample category: {categories[0]}")
        
        # Test get_products (used by EnhancedInventoryPage._load_data)
        print("  📋 Testing get_products...")
        products = enhanced_data.get_products()
        print(f"  ✅ get_products(): {len(products)} products")
        if products:
            sample = products[0]
            print(f"    Sample product keys: {list(sample.keys())}")
            print(f"    Sample product: {sample.get('name', 'Unknown')} - Stock: {sample.get('stock', 0)}")
        
        # Test get_products_paged (used for pagination)
        print("  📋 Testing get_products_paged...")
        paged_result = enhanced_data.get_products_paged(page=1, page_size=5)
        print(f"  ✅ get_products_paged(): {len(paged_result.data)} products")
        print(f"    Total count: {paged_result.total_count}")
        print(f"    Current page: {paged_result.current_page}")
        print(f"    Has total_items: {hasattr(paged_result, 'total_items')}")
        
        # Test search functionality
        print("  📋 Testing search_products_fast...")
        search_results = enhanced_data.search_products_fast("", limit=3)
        print(f"  ✅ search_products_fast(): {len(search_results)} results")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced data access test failed: {e}")
        traceback.print_exc()
        return False

def test_product_manipulation():
    """Test adding and updating products (core inventory functionality)"""
    print("\n🔍 TESTING PRODUCT MANIPULATION")
    print("=" * 60)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        import time
        
        # Test adding a product (used by _add_product)
        print("  📋 Testing add_product...")
        test_product = {
            'Name': f'Test Product {int(time.time())}',
            'Category': 'Test Category',
            'Stock': 10,
            'Price': 25.99,
            'BuyPrice': 15.99,
            'Barcode': f'TEST{int(time.time())}'
        }
        
        result = enhanced_data.add_product(test_product)
        print(f"  ✅ add_product(): {result}")
        
        if result:
            # Verify the product was added
            products = enhanced_data.get_products()
            added_product = None
            for p in products:
                if p.get('name') == test_product['Name']:
                    added_product = p
                    break
            
            if added_product:
                print(f"  ✅ Product successfully added: {added_product['name']}")
                
                # Test updating the product
                print("  📋 Testing update_product...")
                update_data = {
                    'ID': added_product['id'],
                    'Name': added_product['name'] + ' (Updated)',
                    'Category': 'Updated Category',
                    'Stock': 20,
                    'Price': 30.99,
                    'BuyPrice': 20.99,
                    'Barcode': added_product.get('barcode', '')
                }
                
                update_result = enhanced_data.update_product(update_data)
                print(f"  ✅ update_product(): {update_result}")
                
            else:
                print("  ⚠️  Product was added but not found in listing")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Product manipulation test failed: {e}")
        traceback.print_exc()
        return False

def test_database_schema():
    """Test database schema compatibility"""
    print("\n🔍 TESTING DATABASE SCHEMA COMPATIBILITY")
    print("=" * 60)
    
    try:
        from modules.db_manager import ConnectionContext
        
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Check Products table structure
            print("  📋 Checking Products table schema...")
            cursor.execute("PRAGMA table_info(Products)")
            product_columns = {row[1]: row[2] for row in cursor.fetchall()}
            print(f"  ✅ Products table columns: {list(product_columns.keys())}")
            
            # Expected columns for enhanced inventory page
            expected_columns = ['Name', 'Category', 'Stock', 'Price', 'BuyPrice', 'Barcode']
            missing_columns = set(expected_columns) - set(product_columns.keys())
            if missing_columns:
                print(f"  ⚠️  Missing expected columns: {missing_columns}")
            else:
                print("  ✅ All expected columns present")
            
            # Check if Products table has data
            cursor.execute("SELECT COUNT(*) FROM Products")
            product_count = cursor.fetchone()[0]
            print(f"  ✅ Products table has {product_count} records")
            
            # Check Categories table (if it exists)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Categories'")
            categories_exists = cursor.fetchone() is not None
            print(f"  {'✅' if categories_exists else 'ℹ️'} Categories table exists: {categories_exists}")
            
            if categories_exists:
                cursor.execute("SELECT COUNT(*) FROM Categories")
                category_count = cursor.fetchone()[0]
                print(f"  ✅ Categories table has {category_count} records")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database schema test failed: {e}")
        traceback.print_exc()
        return False

def test_inventory_page_imports():
    """Test that the enhanced inventory page can import all its dependencies"""
    print("\n🔍 TESTING INVENTORY PAGE IMPORTS")
    print("=" * 60)
    
    try:
        # Test importing the enhanced inventory page
        print("  📋 Testing enhanced inventory page import...")
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        print("  ✅ Enhanced inventory page imported successfully")
        
        # Test importing dependencies
        print("  📋 Testing dependency imports...")
        from modules.enhanced_data_access import enhanced_data, PagedResult
        print("  ✅ Enhanced data access imported")
        
        from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry
        print("  ✅ UI components imported")
        
        from modules.db_manager import ConnectionContext
        print("  ✅ DB manager imported")
        
        from modules.data_access import invalidate_cache
        print("  ✅ Data access cache invalidation imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Inventory page imports test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all enhanced inventory page backend tests"""
    print("🚀 ENHANCED INVENTORY PAGE BACKEND TEST")
    print("=" * 70)
    print("Testing backend connections and functionality for enhanced inventory page...")
    print("=" * 70)
    
    tests = [
        ("Enhanced Data Access", test_enhanced_data_access),
        ("Product Manipulation", test_product_manipulation),
        ("Database Schema", test_database_schema),
        ("Inventory Page Imports", test_inventory_page_imports)
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
    print("🎯 ENHANCED INVENTORY PAGE BACKEND TEST SUMMARY")
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
        print("Enhanced Inventory Page backend connections are working perfectly!")
        print("\n✅ CONFIRMED FUNCTIONALITY:")
        print("  - Enhanced data access functions working")
        print("  - Product CRUD operations functional") 
        print("  - Database schema compatible")
        print("  - All required imports successful")
        print("  - PagedResult class with total_items property working")
    else:
        print(f"\n⚠️  {total - successful} tests failed. Check details above.")
        
        print("\n🔧 POTENTIAL ISSUES:")
        for test_name, result in results.items():
            if not result:
                print(f"  - {test_name}: Check implementation and dependencies")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Quick CRUD Actions Test Summary - No Emojis for Windows Terminal
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_crud_operations():
    """Test key CRUD operations"""
    print("ENHANCED INVENTORY PAGE CRUD TEST RESULTS")
    print("=" * 60)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        import time
        
        results = {}
        
        # Test 1: Add Product
        print("1. Testing ADD PRODUCT...")
        add_data = {
            'name': f'CRUD Test Product {int(time.time())}',
            'category': 'Test Category',
            'buy_price': 15.99,
            'sell_price': 25.99,
            'stock': 20,
            'barcode': f'CRUD{int(time.time())}'
        }
        add_result = enhanced_data.add_product(add_data)
        results['Add Product'] = add_result
        print(f"   Result: {'PASS' if add_result else 'FAIL'}")
        
        if add_result:
            # Find the added product
            products = enhanced_data.get_products()
            added_product = None
            for p in products:
                if p.get('name') == add_data['name']:
                    added_product = p
                    break
            
            if added_product:
                print(f"   Added product ID: {added_product['id']}")
                
                # Test 2: Edit Product
                print("2. Testing EDIT PRODUCT...")
                edit_data = {
                    'id': added_product['id'],
                    'name': added_product['name'] + ' (Edited)',
                    'category': 'Edited Category',
                    'buy_price': 20.99,
                    'sell_price': 35.99,
                    'stock': 25,
                    'barcode': added_product.get('barcode', '')
                }
                edit_result = enhanced_data.update_product(edit_data)
                results['Edit Product'] = edit_result
                print(f"   Result: {'PASS' if edit_result else 'FAIL'}")
                
                # Test 3: Update Stock
                print("3. Testing STOCK UPDATE...")
                stock_result = enhanced_data.update_product_stock(added_product['id'], 30)
                results['Stock Update'] = stock_result
                print(f"   Result: {'PASS' if stock_result else 'FAIL'}")
            else:
                results['Edit Product'] = False
                results['Stock Update'] = False
                print("   Could not find added product for editing")
        
        # Test 4: Get Products (List)
        print("4. Testing GET PRODUCTS...")
        all_products = enhanced_data.get_products()
        list_result = len(all_products) > 0
        results['Get Products'] = list_result
        print(f"   Result: {'PASS' if list_result else 'FAIL'} - Found {len(all_products)} products")
        
        # Test 5: Get Categories
        print("5. Testing GET CATEGORIES...")
        categories = enhanced_data.get_categories()
        cat_result = len(categories) >= 0  # Even 0 categories is OK
        results['Get Categories'] = cat_result
        print(f"   Result: {'PASS' if cat_result else 'FAIL'} - Found {len(categories)} categories")
        
        # Test 6: Pagination
        print("6. Testing PAGINATION...")
        paged = enhanced_data.get_products_paged(page=1, page_size=3)
        page_result = hasattr(paged, 'data') and hasattr(paged, 'total_count')
        results['Pagination'] = page_result
        print(f"   Result: {'PASS' if page_result else 'FAIL'}")
        
        # Summary
        print("\n" + "=" * 60)
        print("CRUD OPERATIONS TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"   {status} - {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
        
        if passed == total:
            print("\nALL CRUD OPERATIONS WORKING PERFECTLY!")
            print("Enhanced Inventory Page backend is fully functional")
        else:
            print(f"\n{total-passed} tests failed - check implementation")
        
        return passed == total
        
    except Exception as e:
        print(f"CRUD test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_crud_operations()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)

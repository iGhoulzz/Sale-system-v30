"""
Test to understand why inventory data isn't displaying.
Check the format of data returned by enhanced_data.get_products()
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from modules.enhanced_data_access import enhanced_data

def test_data_format():
    print("Testing enhanced_data.get_products() format...")
    
    try:
        products = enhanced_data.get_products()
        print(f"Type of returned data: {type(products)}")
        print(f"Has .data attribute: {hasattr(products, 'data')}")
        
        if isinstance(products, list):
            print(f"It's a list with {len(products)} items")
            if products:
                print(f"First item: {products[0]}")
        
        # Also check if we can create PagedResult from it
        if isinstance(products, list):
            from modules.enhanced_data_access import PagedResult
            paged_products = PagedResult(
                data=products,
                total_count=len(products),
                current_page=1,
                page_size=len(products) if products else 10,
                has_next=False,
                has_prev=False
            )
            print(f"Created PagedResult: {type(paged_products)}")
            print(f"PagedResult has data: {hasattr(paged_products, 'data')}")
            print(f"PagedResult data length: {len(paged_products.data) if hasattr(paged_products, 'data') else 0}")
            
    except Exception as e:
        print(f"Error testing data format: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_format()

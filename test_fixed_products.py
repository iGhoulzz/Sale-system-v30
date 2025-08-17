"""
Test the fixed enhanced_data.get_products() and check field mapping
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from modules.enhanced_data_access import enhanced_data

def test_fixed_method():
    print("=== TESTING FIXED ENHANCED_DATA.GET_PRODUCTS ===")
    
    try:
        products = enhanced_data.get_products()
        print(f"Method returned: {len(products)} products")
        
        if products:
            print(f"First product keys: {list(products[0].keys())}")
            print(f"First product: {products[0]}")
            
            # Check field mapping for UI
            product = products[0]
            print(f"\nField mapping for UI:")
            print(f"ID: {product.get('ID', 'N/A')}")
            print(f"Name: {product.get('Name', 'N/A')}")
            print(f"Category: {product.get('Category', 'N/A')}")
            print(f"Stock: {product.get('Stock', 'N/A')}")
            print(f"Price: {product.get('Price', 'N/A')}")
            print(f"BuyPrice: {product.get('BuyPrice', 'N/A')}")
            print(f"Barcode: {product.get('Barcode', 'N/A')}")
            
    except Exception as e:
        print(f"Error testing fixed method: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_method()

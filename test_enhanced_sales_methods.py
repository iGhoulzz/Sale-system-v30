#!/usr/bin/env python3
"""
Test EnhancedSalesPage missing method fix
"""

import sys
import os

# Add the workspace path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_sales_page_methods():
    """Test EnhancedSalesPage missing methods"""
    print("Testing EnhancedSalesPage missing methods...")
    
    try:
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        
        # Check if the missing method exists
        print("Checking for _on_product_selected_from_search method...")
        if hasattr(EnhancedSalesPage, '_on_product_selected_from_search'):
            print("✅ SUCCESS: _on_product_selected_from_search method exists!")
        else:
            print("❌ ERROR: _on_product_selected_from_search method missing!")
            return False
        
        # Check if the existing method exists
        print("Checking for _on_product_selected method...")
        if hasattr(EnhancedSalesPage, '_on_product_selected'):
            print("✅ SUCCESS: _on_product_selected method exists!")
        else:
            print("❌ ERROR: _on_product_selected method missing!")
            return False
        
        # Check other essential methods
        essential_methods = [
            '_create_ui',
            '_create_modern_header',
            '_create_products_panel',
            '_create_cart_panel',
            '_perform_product_search'
        ]
        
        for method_name in essential_methods:
            if hasattr(EnhancedSalesPage, method_name):
                print(f"✅ SUCCESS: {method_name} method exists!")
            else:
                print(f"❌ ERROR: {method_name} method missing!")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_sales_page_methods()
    if success:
        print("\n🎉 EnhancedSalesPage method fixes are working!")
    else:
        print("\n💥 EnhancedSalesPage method fixes failed!")
    sys.exit(0 if success else 1)

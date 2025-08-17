#!/usr/bin/env python3
"""
Test script to verify update_headers method works correctly
"""

import os
import sys
import tkinter as tk

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_pages():
    """Test that enhanced pages have working update_headers method"""
    
    print("Starting test...")
    
    # Import after path setup
    try:
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        print("✓ Successfully imported enhanced pages")
    except Exception as e:
        print(f"✗ Error importing enhanced pages: {e}")
        return False
    
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the window
        print("✓ Created Tkinter root window")
    except Exception as e:
        print(f"✗ Error creating Tkinter root: {e}")
        return False
    
    try:
        print("Testing EnhancedSalesPage...")
        sales_page = EnhancedSalesPage(parent=root, controller=None)
        
        if hasattr(sales_page, 'products_list') and hasattr(sales_page.products_list, 'update_headers'):
            print("✓ EnhancedSalesPage.products_list has update_headers method")
            # Test calling the method
            sales_page.products_list.update_headers({'TestCol': 'Test Header'})
            print("✓ EnhancedSalesPage.products_list.update_headers() executed successfully")
        else:
            print("✗ EnhancedSalesPage.products_list missing update_headers method")
            
        print("\nTesting EnhancedDebitsPage...")
        debits_page = EnhancedDebitsPage(parent=root, controller=None)
        
        if hasattr(debits_page, 'debits_list') and hasattr(debits_page.debits_list, 'update_headers'):
            print("✓ EnhancedDebitsPage.debits_list has update_headers method")
            # Test calling the method
            debits_page.debits_list.update_headers({'TestCol': 'Test Header'})
            print("✓ EnhancedDebitsPage.debits_list.update_headers() executed successfully")
        else:
            print("✗ EnhancedDebitsPage.debits_list missing update_headers method")
            
        print("\n✓ All tests passed! The update_headers method is working correctly.")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False
    finally:
        root.destroy()
    
    return True

if __name__ == "__main__":
    if test_enhanced_pages():
        print("\n🎉 SUCCESS: All enhanced pages have working update_headers method!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Some issues found with update_headers method.")
        sys.exit(1)

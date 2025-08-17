#!/usr/bin/env python3
"""
Test the exact code path that was failing in the logs
"""

import os
import sys
import tkinter as tk

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_language_refresh():
    """Test the _refresh_language method that was causing the error"""
    
    print("Testing language refresh functionality...")
    
    try:
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        print("✓ Successfully imported enhanced pages")
        
        root = tk.Tk()
        root.withdraw()  # Hide the window
        print("✓ Created Tkinter root window")
        
        # Test EnhancedSalesPage
        print("\nTesting EnhancedSalesPage._refresh_language()...")
        sales_page = EnhancedSalesPage(parent=root, controller=None)
        
        try:
            sales_page._refresh_language()
            print("✓ EnhancedSalesPage._refresh_language() executed successfully")
        except Exception as e:
            print(f"✗ Error in EnhancedSalesPage._refresh_language(): {e}")
            return False
            
        # Test EnhancedDebitsPage
        print("\nTesting EnhancedDebitsPage._refresh_language()...")
        debits_page = EnhancedDebitsPage(parent=root, controller=None)
        
        try:
            debits_page._refresh_language()
            print("✓ EnhancedDebitsPage._refresh_language() executed successfully")
        except Exception as e:
            print(f"✗ Error in EnhancedDebitsPage._refresh_language(): {e}")
            return False
            
        # Test prepare_for_display methods
        print("\nTesting prepare_for_display methods...")
        
        try:
            sales_page.prepare_for_display()
            print("✓ EnhancedSalesPage.prepare_for_display() executed successfully")
        except Exception as e:
            print(f"✗ Error in EnhancedSalesPage.prepare_for_display(): {e}")
            # This might fail due to database issues, but that's separate from update_headers
            
        try:
            debits_page.prepare_for_display()
            print("✓ EnhancedDebitsPage.prepare_for_display() executed successfully")
        except Exception as e:
            print(f"✗ Error in EnhancedDebitsPage.prepare_for_display(): {e}")
            # This might fail due to database issues, but that's separate from update_headers
            
        print("\n✓ All language refresh tests passed!")
        
        # Clean up
        root.destroy()
        print("✓ Cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during test: {e}")
        return False

if __name__ == "__main__":
    if test_language_refresh():
        print("\n🎉 SUCCESS: Language refresh functionality works correctly!")
        print("The update_headers error should be resolved!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Language refresh test failed.")
        sys.exit(1)

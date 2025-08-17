#!/usr/bin/env python3
"""Test script to verify the enhanced debits page fix"""

import sys
import os
sys.path.append('.')

# Test if we can import and initialize the enhanced debits page
try:
    from modules.pages.enhanced_debits_page import EnhancedDebitsPage
    print("✅ EnhancedDebitsPage imports successfully")
    
    # Test that the class has the required attributes without creating UI
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    class MockController:
        pass
    
    # Create an instance to test initialization
    page = EnhancedDebitsPage(root, MockController())
    
    # Check if attributes exist
    if hasattr(page, 'total_debits'):
        print("✅ total_debits attribute exists")
    else:
        print("❌ total_debits attribute missing")
        
    if hasattr(page, 'unpaid_debits'):
        print("✅ unpaid_debits attribute exists")
    else:
        print("❌ unpaid_debits attribute missing")
        
    # Test the update_statistics_display method
    if hasattr(page, '_update_statistics_display'):
        try:
            page._update_statistics_display()
            print("✅ _update_statistics_display method works")
        except Exception as e:
            print(f"❌ _update_statistics_display failed: {e}")
    
    root.destroy()
    print("✅ Test completed successfully")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

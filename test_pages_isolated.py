#!/usr/bin/env python3
"""
Simple test to isolate the enhanced pages issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import ttkbootstrap as ttk

def test_enhanced_pages():
    """Test enhanced pages one by one"""
    print("Testing enhanced pages individually...")
    
    # Create test window
    root = ttk.Window()
    root.withdraw()  # Hide the window
    
    # Mock controller
    class MockController:
        def __init__(self):
            self.frames = {}
            self.current_frame = None
        
        def show_frame(self, frame_name):
            pass
    
    controller = MockController()
    
    # Test Enhanced Sales Page
    try:
        print("Testing Enhanced Sales Page...")
        from modules.pages.enhanced_sales_page import EnhancedSalesPage
        sales_page = EnhancedSalesPage(root, controller)
        sales_page.destroy()
        print("✅ Enhanced Sales Page works!")
    except Exception as e:
        print(f"❌ Enhanced Sales Page error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test Enhanced Debits Page
    try:
        print("\nTesting Enhanced Debits Page...")
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        debits_page = EnhancedDebitsPage(root, controller)
        debits_page.destroy()
        print("✅ Enhanced Debits Page works!")
    except Exception as e:
        print(f"❌ Enhanced Debits Page error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test Enhanced Inventory Page
    try:
        print("\nTesting Enhanced Inventory Page...")
        from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
        inventory_page = EnhancedInventoryPage(root, controller)
        inventory_page.destroy()
        print("✅ Enhanced Inventory Page works!")
    except Exception as e:
        print(f"❌ Enhanced Inventory Page error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    root.destroy()

if __name__ == "__main__":
    test_enhanced_pages()

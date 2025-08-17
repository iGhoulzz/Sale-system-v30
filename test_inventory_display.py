#!/usr/bin/env python3
"""
Test inventory data display issues
"""

import os
import sys
import traceback
import logging

# Setup logging 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=== INVENTORY DATA DISPLAY TEST ===")

def test_inventory_data():
    """Test if inventory data is accessible"""
    print("\n1. Testing inventory data access...")
    
    try:
        from modules.data_access import get_products, get_categories
        
        # Test categories
        categories = get_categories()
        print(f"✅ Categories found: {categories}")
        
        # Test products
        products = get_products()
        print(f"✅ Products found: {len(products)} items")
        
        if products:
            print("   Sample products:")
            for i, product in enumerate(products[:3]):  # Show first 3
                print(f"     {i+1}. {product.get('Name')} - Stock: {product.get('Stock')} - Category: {product.get('Category')}")
        
        return products, categories
        
    except Exception as e:
        print(f"❌ Data access error: {e}")
        traceback.print_exc()
        return [], []

def test_inventory_page_loading():
    """Test if the inventory page loads correctly"""
    print("\n2. Testing inventory page loading...")
    
    try:
        # Mock login
        import modules.Login
        modules.Login.current_user = {"Username": "admin", "Role": "admin", "UserID": 1}
        
        # Create a simple test window to check inventory page
        import tkinter as tk
        import ttkbootstrap as ttk
        
        root = ttk.Window(themename="darkly")
        root.withdraw()  # Hide test window
        
        # Create a mock controller
        class MockController:
            def show_frame(self, frame_name):
                print(f"Mock controller showing frame: {frame_name}")
        
        controller = MockController()
        
        # Try to load the enhanced inventory page
        print("   Testing Enhanced Inventory Page...")
        try:
            from modules.pages.enhanced_inventory_page import EnhancedInventoryPage
            enhanced_page = EnhancedInventoryPage(parent=root, controller=controller)
            print("   ✅ Enhanced inventory page created")
            
            # Check if it has data loading methods
            if hasattr(enhanced_page, 'load_data'):
                print("   ✅ Has load_data method")
            else:
                print("   ❌ Missing load_data method")
                
            if hasattr(enhanced_page, 'refresh_data'):
                print("   ✅ Has refresh_data method")
            else:
                print("   ❌ Missing refresh_data method")
                
            # Try to trigger data loading
            if hasattr(enhanced_page, 'load_products'):
                try:
                    enhanced_page.load_products()
                    print("   ✅ load_products executed")
                except Exception as e:
                    print(f"   ❌ load_products failed: {e}")
                    
        except Exception as e:
            print(f"   ❌ Enhanced inventory page failed: {e}")
            traceback.print_exc()
            
        # Try standard inventory page as fallback
        print("   Testing Standard Inventory Page...")
        try:
            from modules.pages.inventory_page import InventoryPage
            standard_page = InventoryPage(parent=root, controller=controller)
            print("   ✅ Standard inventory page created")
            
            # Check if it has data loading methods
            if hasattr(standard_page, 'load_products'):
                print("   ✅ Has load_products method")
            else:
                print("   ❌ Missing load_products method")
                
        except Exception as e:
            print(f"   ❌ Standard inventory page failed: {e}")
            traceback.print_exc()
        
        root.destroy()
        
    except Exception as e:
        print(f"❌ Page loading test failed: {e}")
        traceback.print_exc()

def test_specific_inventory_ui():
    """Test the specific inventory UI components"""
    print("\n3. Testing inventory UI components...")
    
    try:
        # Mock login
        import modules.Login
        modules.Login.current_user = {"Username": "admin", "Role": "admin", "UserID": 1}
        
        from main import MainApp
        app = MainApp(themename="darkly")
        app._initialize_ui()
        
        # Get the inventory frame
        inventory_frame = app.frames.get("InventoryPage")
        if inventory_frame:
            print("   ✅ Inventory frame found")
            
            # Check for treeview or list widget
            widgets = []
            for child in inventory_frame.winfo_children():
                widgets.extend(child.winfo_children())
            
            # Look for data display widgets
            treeview_found = False
            listbox_found = False
            
            def find_widgets(widget):
                nonlocal treeview_found, listbox_found
                
                if hasattr(widget, 'winfo_class'):
                    widget_class = widget.winfo_class()
                    if 'Treeview' in widget_class:
                        treeview_found = True
                        print(f"   ✅ Found Treeview widget")
                        
                        # Try to check if it has data
                        try:
                            if hasattr(widget, 'get_children'):
                                children = widget.get_children()
                                print(f"     Treeview has {len(children)} items")
                        except:
                            pass
                            
                    elif 'Listbox' in widget_class:
                        listbox_found = True
                        print(f"   ✅ Found Listbox widget")
                        
                        try:
                            if hasattr(widget, 'size'):
                                size = widget.size()
                                print(f"     Listbox has {size} items")
                        except:
                            pass
                
                # Recursively check children
                try:
                    for child in widget.winfo_children():
                        find_widgets(child)
                except:
                    pass
            
            find_widgets(inventory_frame)
            
            if not treeview_found and not listbox_found:
                print("   ❌ No data display widgets found!")
                
            # Check for refresh/load methods
            if hasattr(inventory_frame, 'refresh'):
                print("   ✅ Has refresh method")
                try:
                    inventory_frame.refresh()
                    print("   ✅ Refresh executed successfully")
                except Exception as e:
                    print(f"   ❌ Refresh failed: {e}")
            else:
                print("   ❌ No refresh method found")
                
        else:
            print("   ❌ Inventory frame not found!")
            
        app.destroy()
        
    except Exception as e:
        print(f"❌ UI component test failed: {e}")
        traceback.print_exc()

def suggest_fixes():
    """Suggest potential fixes for inventory display issues"""
    print("\n" + "="*50)
    print("POTENTIAL INVENTORY DISPLAY ISSUES & FIXES:")
    print("="*50)
    
    print("\n🔧 Common Issues:")
    print("1. Data not loaded on page initialization")
    print("2. UI widgets not properly populated with data")
    print("3. Enhanced page has different data loading mechanism")
    print("4. Category filtering preventing data display")
    print("5. Search filters blocking initial data load")
    
    print("\n💡 Recommended Fixes:")
    print("1. Check if enhanced inventory page calls load_products() in __init__")
    print("2. Verify data is being populated in the treeview/listbox")
    print("3. Ensure refresh() method reloads data from database")
    print("4. Check for any filters that might hide all data")
    print("5. Add debug logging to see what data is being loaded")

if __name__ == "__main__":
    products, categories = test_inventory_data()
    test_inventory_page_loading()
    test_specific_inventory_ui()
    suggest_fixes()
    
    print("\n=== INVENTORY DISPLAY TEST COMPLETE ===")

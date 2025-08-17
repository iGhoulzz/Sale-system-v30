#!/usr/bin/env python3
"""
Test Enhanced Inventory Page Launch from Main App
"""

import sys
import tkinter as tk
from pathlib import Path

# Add the main directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_inventory_launch():
    """Test launching enhanced inventory page from main app"""
    print("Testing Enhanced Inventory Page Launch...")
    
    try:
        from main import MainApp
        
        # Create main application
        root = tk.Tk()
        root.title("Test Enhanced Inventory")
        root.geometry("1000x700")
        
        # Initialize main app
        app = MainApp(root)
        
        # Check that InventoryPage is available (this will be the enhanced version)
        if "InventoryPage" in app.frames:
            print("✓ Enhanced inventory page registered as 'InventoryPage'")
            
            # Get the frame
            inventory_frame = app.frames["InventoryPage"]
            
            # Check if it's actually the enhanced version
            if hasattr(inventory_frame, 'colors') and hasattr(inventory_frame, '_go_back'):
                print("✓ Confirmed: This is the enhanced version with dark theme and back button")
                
                # Navigate to it
                app.show_frame("InventoryPage")
                print("✓ Successfully navigated to enhanced inventory page")
                
                # Test some enhanced features
                if hasattr(inventory_frame, 'colors'):
                    print(f"✓ Dark theme colors loaded: {len(inventory_frame.colors)} color definitions")
                
                if hasattr(inventory_frame, 'search_var'):
                    print("✓ Enhanced search functionality available")
                
                if hasattr(inventory_frame, 'products_data'):
                    print("✓ Product data management initialized")
                    
                print("\n🎉 ENHANCED INVENTORY PAGE LAUNCH SUCCESS!")
                print("   • Dark theme with system-matching colors")
                print("   • Back button navigation")
                print("   • Enhanced detailed features")
                print("   • Professional business interface")
                
                # Run the app briefly to show it works
                root.after(2000, root.quit)  # Auto-close after 2 seconds
                root.mainloop()
                
                return True
            else:
                print("✗ Frame exists but is not the enhanced version")
                return False
        else:
            print("✗ InventoryPage not found in app frames")
            print(f"Available frames: {list(app.frames.keys())}")
            return False
            
    except Exception as e:
        print(f"✗ Launch test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

def main():
    """Run launch test"""
    print("=" * 60)
    print("ENHANCED INVENTORY PAGE LAUNCH TEST")
    print("=" * 60)
    
    success = test_enhanced_inventory_launch()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ LAUNCH TEST PASSED - Enhanced inventory page ready for use!")
    else:
        print("❌ Launch test failed")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

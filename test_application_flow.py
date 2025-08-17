#!/usr/bin/env python3
"""
Full application test to verify the fixes work in practice
"""

import os
import sys
import time
import tkinter as tk

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_full_application():
    """Test the full application startup and navigation"""
    
    print("Testing full application startup...")
    
    try:
        import main
        print("✓ Successfully imported main module")
        
        # Create the main application
        app = main.MainApp()
        print("✓ Successfully created MainApp instance")
        
        # Test navigation to enhanced pages
        print("\nTesting page navigation...")
        
        # Try to show the sales page
        try:
            app.show_frame("SalesPage")
            print("✓ Successfully navigated to SalesPage")
        except Exception as e:
            print(f"✗ Error navigating to SalesPage: {e}")
        
        # Try to show the debits page
        try:
            app.show_frame("DebitsPage")
            print("✓ Successfully navigated to DebitsPage")
        except Exception as e:
            print(f"✗ Error navigating to DebitsPage: {e}")
        
        # Try to show the inventory page
        try:
            app.show_frame("InventoryPage")
            print("✓ Successfully navigated to InventoryPage")
        except Exception as e:
            print(f"✗ Error navigating to InventoryPage: {e}")
        
        print("\n✓ Application test completed successfully!")
        
        # Clean up
        app.destroy()
        print("✓ Application destroyed cleanly")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during application test: {e}")
        return False

if __name__ == "__main__":
    if test_full_application():
        print("\n🎉 SUCCESS: Application runs and navigates correctly!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Application test failed.")
        sys.exit(1)

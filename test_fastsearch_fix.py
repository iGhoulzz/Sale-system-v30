#!/usr/bin/env python3
"""
Simple test for FastSearchEntry placeholder support
"""

import sys
import os
import tkinter as tk

# Add the workspace path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fastsearchentry():
    """Test FastSearchEntry with placeholder"""
    print("Testing FastSearchEntry placeholder support...")
    
    try:
        from modules.ui_components import FastSearchEntry
        
        # Create test root
        root = tk.Tk()
        root.withdraw()
        
        def dummy_search(term, limit=10):
            return [{'id': '1', 'display': f'Test: {term}'}]
        
        def dummy_callback(result):
            print(f"Selected: {result}")
        
        # Test with placeholder
        print("Creating FastSearchEntry with placeholder...")
        entry = FastSearchEntry(
            root,
            search_function=dummy_search,
            on_select_callback=dummy_callback,
            placeholder="Search products..."
        )
        
        print("✅ SUCCESS: FastSearchEntry created with placeholder!")
        
        # Test without placeholder
        print("Creating FastSearchEntry without placeholder...")
        entry2 = FastSearchEntry(
            root,
            search_function=dummy_search,
            on_select_callback=dummy_callback
        )
        
        print("✅ SUCCESS: FastSearchEntry created without placeholder!")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fastsearchentry()
    if success:
        print("\n🎉 FastSearchEntry placeholder fix is working!")
    else:
        print("\n💥 FastSearchEntry placeholder fix failed!")
    sys.exit(0 if success else 1)

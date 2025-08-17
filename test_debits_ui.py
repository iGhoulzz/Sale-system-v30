#!/usr/bin/env python3
"""
Test script to diagnose UI initialization issues for debits page
"""

import os
import sys
import traceback
import logging
import tkinter as tk
import ttkbootstrap as ttk

# Setup logging to see detailed error messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=== DEBITS PAGE UI INITIALIZATION TEST ===")

# Mock current_user for testing
import modules.Login
modules.Login.current_user = {"Username": "test", "Role": "admin"}

def test_debits_page_creation():
    """Test creating the debits page UI"""
    print("\n1. Testing standard debits page creation...")
    
    try:
        # Create a test window
        root = ttk.Window(themename="darkly")
        root.withdraw()  # Hide the test window
        
        # Create a mock controller
        class MockController:
            def show_frame(self, frame_name):
                print(f"Mock: Showing frame {frame_name}")
        
        controller = MockController()
        
        # Try to create the standard debits page
        from modules.pages.debits_page import DebitsPage
        debits_page = DebitsPage(parent=root, controller=controller)
        print("✅ Standard debits page created successfully")
        
        # Clean up
        debits_page.destroy()
        root.destroy()
        
    except Exception as e:
        print(f"❌ Standard debits page creation failed: {e}")
        traceback.print_exc()
        try:
            root.destroy()
        except:
            pass

def test_enhanced_debits_page_creation():
    """Test creating the enhanced debits page UI"""
    print("\n2. Testing enhanced debits page creation...")
    
    try:
        # Create a test window
        root = ttk.Window(themename="darkly")
        root.withdraw()  # Hide the test window
        
        # Create a mock controller
        class MockController:
            def show_frame(self, frame_name):
                print(f"Mock: Showing frame {frame_name}")
        
        controller = MockController()
        
        # Try to create the enhanced debits page
        from modules.pages.enhanced_debits_page import EnhancedDebitsPage
        enhanced_debits_page = EnhancedDebitsPage(parent=root, controller=controller)
        print("✅ Enhanced debits page created successfully")
        
        # Clean up
        enhanced_debits_page.destroy()
        root.destroy()
        
    except Exception as e:
        print(f"❌ Enhanced debits page creation failed: {e}")
        traceback.print_exc()
        try:
            root.destroy()
        except:
            pass

def test_data_loading():
    """Test data loading functionality"""
    print("\n3. Testing data loading...")
    
    try:
        from modules.data_access import get_debits
        debits = get_debits()
        print(f"✅ get_debits() returned {len(debits)} items")
        
        if debits:
            print("Sample debit:", debits[0])
            
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_debits_page_creation()
    test_enhanced_debits_page_creation()
    test_data_loading()
    
    print("\n=== UI INITIALIZATION TEST COMPLETE ===")

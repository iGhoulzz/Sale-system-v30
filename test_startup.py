#!/usr/bin/env python3
"""
Test script to start the main application and capture the actual runtime error
"""

import os
import sys
import traceback
import logging

# Setup logging to see detailed error messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=== MAIN APPLICATION STARTUP TEST ===")

try:
    # Mock a successful login to skip the login dialog
    import modules.Login
    modules.Login.current_user = {"Username": "test", "Role": "admin"}
    
    # Import and create the main application
    from main import MainApp
    
    print("Creating main application...")
    app = MainApp(themename="darkly")
    
    print("Initializing UI...")
    app._initialize_ui()
    
    print("Testing navigation to debits page...")
    app.show_frame("DebitsPage")
    
    print("✅ Application started successfully and navigated to debits page")
    
    # Clean up
    app.destroy()
    
except Exception as e:
    print(f"❌ Application startup failed: {e}")
    traceback.print_exc()

print("\n=== STARTUP TEST COMPLETE ===")

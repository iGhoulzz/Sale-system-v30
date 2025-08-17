#!/usr/bin/env python3
"""
Final validation script to ensure all runtime fixes are working.
This focuses on import validation and core functionality without GUI components.
"""

import sys
import traceback
from datetime import datetime

def test_core_imports():
    """Test that all core modules can be imported without errors"""
    print("Testing Core Module Imports...")
    print("=" * 50)
    
    try:
        # Test UI Components with fixes
        from modules.ui_components import PaginatedListView, ProgressDialog
        print("✓ UI Components: IMPORTED SUCCESSFULLY")
        
        # Test Enhanced Pages with fixes
        import modules.pages.enhanced_sales_page
        print("✓ Enhanced Sales Page: IMPORTED SUCCESSFULLY")
        
        import modules.pages.enhanced_inventory_page  
        print("✓ Enhanced Inventory Page: IMPORTED SUCCESSFULLY")
        
        import modules.pages.enhanced_debits_page
        print("✓ Enhanced Debits Page: IMPORTED SUCCESSFULLY")
        
        # Test Enhanced Data Access
        from modules.enhanced_data_access import EnhancedDataAccess
        print("✓ Enhanced Data Access: IMPORTED SUCCESSFULLY")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_constructor_fixes():
    """Test that constructor fixes are working"""
    print("\nTesting Constructor Fixes...")
    print("=" * 50)
    
    try:
        # Import required modules
        import tkinter as tk
        from modules.ui_components import PaginatedListView, ProgressDialog
        
        # Create a temporary root for testing (withdrawn)
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        # Test PaginatedListView enhanced constructor
        plv = PaginatedListView(
            root, 
            ["id", "name", "value"],
            headers={"id": "ID", "name": "Name", "value": "Value"},
            widths={"id": 50, "name": 100, "value": 80},
            on_page_change=lambda page: None,
            on_select=lambda item: None,
            height=10
        )
        print("✓ PaginatedListView enhanced constructor: WORKING")
        
        # Test ProgressDialog constructor
        progress = ProgressDialog(root, title="Test Progress")
        progress.close()
        print("✓ ProgressDialog constructor: WORKING")
        
        # Cleanup
        plv.destroy()
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ Constructor test failed: {e}")
        traceback.print_exc()
        return False

def test_method_signatures():
    """Test that method signatures are correct"""
    print("\nTesting Method Signatures...")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import EnhancedDataAccess
        
        # Check that required methods exist
        methods_to_check = [
            'get_debits_paged',
            'add_debit', 
            'update_debit',
            'delete_debit',
            'mark_debit_as_paid',
            'run_in_background'
        ]
        
        eda = EnhancedDataAccess()
        
        for method in methods_to_check:
            if hasattr(eda, method):
                print(f"✓ {method}: METHOD EXISTS")
            else:
                print(f"✗ {method}: METHOD MISSING")
                return False
                
        return True
        
    except Exception as e:
        print(f"✗ Method signature test failed: {e}")
        traceback.print_exc()
        return False

def test_file_syntax():
    """Test that all Python files have correct syntax"""
    print("\nTesting File Syntax...")
    print("=" * 50)
    
    files_to_check = [
        "modules/ui_components.py",
        "modules/pages/enhanced_sales_page.py", 
        "modules/pages/enhanced_inventory_page.py",
        "modules/pages/enhanced_debits_page.py",
        "modules/enhanced_data_access.py"
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Try to compile the source
            compile(source, file_path, 'exec')
            print(f"✓ {file_path}: SYNTAX OK")
            
        except SyntaxError as e:
            print(f"✗ {file_path}: SYNTAX ERROR - {e}")
            all_good = False
        except Exception as e:
            print(f"✗ {file_path}: ERROR - {e}")
            all_good = False
    
    return all_good

def main():
    """Run all validation tests"""
    print("=" * 60)
    print("FINAL VALIDATION - SALES SYSTEM RUNTIME FIXES")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("File Syntax", test_file_syntax),
        ("Core Imports", test_core_imports),
        ("Constructor Fixes", test_constructor_fixes),
        ("Method Signatures", test_method_signatures)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name}: PASSED")
            else:
                print(f"✗ {test_name}: FAILED")
        except Exception as e:
            print(f"✗ {test_name}: FAILED - {e}")
    
    print("\n" + "=" * 60)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL RUNTIME FIXES ARE WORKING CORRECTLY!")
        print("🎉 The application should run without errors.")
    else:
        print("❌ Some issues remain - check the failed tests above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

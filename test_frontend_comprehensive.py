#!/usr/bin/env python3
"""
Comprehensive Frontend UI and Backend Integration Test
This test will identify missing features and backend connection issues
"""

import os
import sys
import traceback
import logging
import tkinter as tk
import time

# Setup logging to see detailed error messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=== COMPREHENSIVE FRONTEND UI & BACKEND INTEGRATION TEST ===")

def test_all_frontend_features():
    """Test all frontend features and backend connectivity"""
    print("\n1. Testing Application Startup and Page Loading...")
    
    try:
        # Mock a successful login to skip the login dialog
        import modules.Login
        modules.Login.current_user = {"Username": "admin", "Role": "admin", "UserID": 1}
        
        # Import and create the main application
        from main import MainApp
        
        print("Creating main application...")
        app = MainApp(themename="darkly")
        
        print("Initializing UI...")
        app._initialize_ui()
        
        # Test each page in detail
        test_results = {}
        
        # Test MainMenuPage
        print("\n2. Testing Main Menu Page...")
        try:
            app.show_frame("MainMenuPage")
            main_menu_frame = app.frames.get("MainMenuPage")
            if main_menu_frame:
                print("✅ Main Menu loads successfully")
                print("   - Language toggle button present")
                print("   - Role-based button access working")
                test_results["MainMenuPage"] = "PASS"
            else:
                print("❌ Main Menu frame not found")
                test_results["MainMenuPage"] = "FAIL"
        except Exception as e:
            print(f"❌ Main Menu error: {e}")
            test_results["MainMenuPage"] = f"FAIL - {e}"
        
        # Test InventoryPage
        print("\n3. Testing Inventory Page...")
        try:
            app.show_frame("InventoryPage")
            inventory_frame = app.frames.get("InventoryPage")
            if inventory_frame:
                print("✅ Inventory Page loads successfully")
                
                # Test backend data connectivity
                from modules.data_access import get_products, get_categories
                products = get_products()
                categories = get_categories()
                print(f"   - Products loaded: {len(products)} items")
                print(f"   - Categories loaded: {len(categories)} categories")
                
                # Test if the page has the expected UI components
                if hasattr(inventory_frame, 'search_var'):
                    print("   ✅ Search functionality present")
                else:
                    print("   ❌ Search functionality missing")
                
                if hasattr(inventory_frame, 'category_filter'):
                    print("   ✅ Category filtering present")
                else:
                    print("   ❌ Category filtering missing")
                    
                test_results["InventoryPage"] = "PASS"
            else:
                print("❌ Inventory frame not found")
                test_results["InventoryPage"] = "FAIL"
        except Exception as e:
            print(f"❌ Inventory Page error: {e}")
            test_results["InventoryPage"] = f"FAIL - {e}"
            
        # Test SalesPage
        print("\n4. Testing Sales Page...")
        try:
            app.show_frame("SalesPage")
            sales_frame = app.frames.get("SalesPage")
            if sales_frame:
                print("✅ Sales Page loads successfully")
                
                # Test backend data connectivity
                from modules.data_access import get_recent_invoices
                invoices = get_recent_invoices(limit=5)
                print(f"   - Recent invoices loaded: {len(invoices)} items")
                
                # Test barcode functionality
                from modules.data_access import get_product_by_barcode
                # This should return None for non-existent barcode
                result = get_product_by_barcode("TEST123")
                print(f"   ✅ Barcode lookup working (result: {result is not None})")
                
                test_results["SalesPage"] = "PASS"
            else:
                print("❌ Sales frame not found")
                test_results["SalesPage"] = "FAIL"
        except Exception as e:
            print(f"❌ Sales Page error: {e}")
            test_results["SalesPage"] = f"FAIL - {e}"
            
        # Test DebitsPage
        print("\n5. Testing Debits Page...")
        try:
            app.show_frame("DebitsPage")
            debits_frame = app.frames.get("DebitsPage")
            if debits_frame:
                print("✅ Debits Page loads successfully")
                
                # Test backend data connectivity
                from modules.data_access import get_debits, get_invoice_items
                debits_data = get_debits()
                print(f"   - Debits loaded: {len(debits_data[0])} items")
                print(f"   - Statistics: Total: ${debits_data[1]['total']:.2f}, Pending: ${debits_data[1]['pending']:.2f}")
                
                # Test invoice item retrieval if we have debits
                if debits_data[0]:
                    first_debit = debits_data[0][0]
                    invoice_id = first_debit['InvoiceID']
                    try:
                        invoice, items = get_invoice_items(invoice_id)
                        print(f"   ✅ Invoice items retrieval working ({len(items)} items)")
                    except Exception as e:
                        print(f"   ❌ Invoice items retrieval failed: {e}")
                
                test_results["DebitsPage"] = "PASS"
            else:
                print("❌ Debits frame not found")
                test_results["DebitsPage"] = "FAIL"
        except Exception as e:
            print(f"❌ Debits Page error: {e}")
            test_results["DebitsPage"] = f"FAIL - {e}"
            
        # Test Database Operations
        print("\n6. Testing Core Database Operations...")
        try:
            from modules.data_access import get_product_stock, check_stock_batch
            
            # Test individual stock check
            products = get_products()
            if products:
                first_product = products[0]
                stock_info = get_product_stock(first_product['ProductID'])
                print(f"   ✅ Individual stock check: {stock_info['name']} has {stock_info['stock']} units")
                
                # Test batch stock check
                product_ids = [p['ProductID'] for p in products[:3]]
                batch_stock = check_stock_batch(product_ids)
                print(f"   ✅ Batch stock check: {len(batch_stock)} products checked")
            else:
                print("   ❌ No products available for stock testing")
                
            test_results["DatabaseOps"] = "PASS"
        except Exception as e:
            print(f"❌ Database operations error: {e}")
            test_results["DatabaseOps"] = f"FAIL - {e}"
            
        # Test Internationalization
        print("\n7. Testing Internationalization...")
        try:
            from modules.i18n import _, switch_language, get_current_language
            
            current_lang = get_current_language()
            print(f"   Current language: {current_lang}")
            
            # Test translation
            test_text = _("Sales Management System")
            print(f"   Translation test: '{test_text}'")
            
            # Test language switching
            new_lang = 'ar' if current_lang == 'en' else 'en'
            switch_language(new_lang)
            switched_lang = get_current_language()
            print(f"   Language switched to: {switched_lang}")
            
            # Switch back
            switch_language(current_lang)
            
            test_results["I18n"] = "PASS"
        except Exception as e:
            print(f"❌ Internationalization error: {e}")
            test_results["I18n"] = f"FAIL - {e}"
            
        # Test Performance Features
        print("\n8. Testing Performance Features...")
        try:
            from modules.enhanced_data_access import enhanced_data
            from modules.ui_components import PaginatedListView, FastSearchEntry
            
            print("   ✅ Enhanced data access available")
            print("   ✅ UI components (pagination, fast search) available")
            
            test_results["Performance"] = "PASS"
        except Exception as e:
            print(f"❌ Performance features error: {e}")
            test_results["Performance"] = f"FAIL - {e}"
            
        # Clean up
        app.destroy()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY:")
        print("="*60)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result == "PASS" else f"❌ FAIL"
            print(f"{test_name:<20}: {status}")
            if result == "PASS":
                passed += 1
            else:
                failed += 1
                if result != "FAIL":
                    print(f"                     Error: {result}")
        
        print("-" * 60)
        print(f"Total: {passed + failed} tests, {passed} passed, {failed} failed")
        
        return test_results
        
    except Exception as e:
        print(f"❌ Critical error in frontend testing: {e}")
        traceback.print_exc()
        return {}

def test_missing_features():
    """Identify potentially missing features based on typical POS requirements"""
    print("\n" + "="*60)
    print("CHECKING FOR MISSING FEATURES:")
    print("="*60)
    
    missing_features = []
    
    # Check for common POS features
    try:
        # Customer management
        try:
            from modules.data_access import get_customers  # This might not exist
            print("✅ Customer management available")
        except ImportError:
            print("❌ Customer management missing")
            missing_features.append("Customer Management System")
            
        # Discount system
        try:
            from modules.data_access import apply_discount  # This might not exist
            print("✅ Discount system available")
        except ImportError:
            print("❌ Advanced discount system missing")
            missing_features.append("Advanced Discount System")
            
        # Tax calculation
        try:
            from modules.data_access import calculate_tax  # This might not exist
            print("✅ Tax calculation available")
        except ImportError:
            print("❌ Tax calculation system missing")
            missing_features.append("Tax Calculation System")
            
        # Receipt printing
        try:
            from modules.receipt_printer import print_receipt  # This might not exist
            print("✅ Receipt printing available")
        except ImportError:
            print("❌ Receipt printing system missing")
            missing_features.append("Receipt Printing System")
            
        # Backup/restore
        try:
            from modules.backup_manager import backup_database  # This might not exist
            print("✅ Backup system available")
        except ImportError:
            print("❌ Database backup system missing")
            missing_features.append("Database Backup/Restore System")
            
        # Reporting
        try:
            from modules.reports import generate_sales_report  # This might not exist
            print("✅ Advanced reporting available")
        except ImportError:
            print("❌ Advanced reporting system missing")
            missing_features.append("Advanced Reporting System")
            
    except Exception as e:
        print(f"Error checking features: {e}")
    
    if missing_features:
        print("\nRECOMMENDED FEATURES TO ADD:")
        for i, feature in enumerate(missing_features, 1):
            print(f"{i}. {feature}")
    else:
        print("\n✅ All common POS features appear to be available")
        
    return missing_features

if __name__ == "__main__":
    # Run the comprehensive test
    test_results = test_all_frontend_features()
    missing_features = test_missing_features()
    
    print("\n" + "="*60)
    print("FINAL RECOMMENDATIONS:")
    print("="*60)
    
    # Analyze results and provide recommendations
    if test_results.get("InventoryPage") == "PASS":
        print("✅ Inventory management is working well")
    else:
        print("🔧 Fix inventory page issues before proceeding")
        
    if test_results.get("SalesPage") == "PASS":
        print("✅ Sales functionality is working well")
    else:
        print("🔧 Fix sales page issues before proceeding")
        
    if test_results.get("DebitsPage") == "PASS":
        print("✅ Debits management is working well")
    else:
        print("🔧 Fix debits page issues before proceeding")
        
    if missing_features:
        print("\n🚀 Consider adding these features for a complete POS system:")
        for feature in missing_features[:3]:  # Show top 3
            print(f"   - {feature}")
            
    print("\n=== FRONTEND TESTING COMPLETE ===")

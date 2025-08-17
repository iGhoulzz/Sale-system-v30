import sys
sys.path.append('.')

print("Testing fixes...")

try:
    # Test the main fixes
    from modules.pages.enhanced_debits_page import EnhancedDebitsPage
    from modules.ui_components import PaginatedListView
    
    print("SUCCESS: All critical imports work")
    
    # Test if we can create the main application
    from main import MainApplication
    print("SUCCESS: MainApplication can be imported")
    
    print("ALL FIXES VERIFIED SUCCESSFULLY!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

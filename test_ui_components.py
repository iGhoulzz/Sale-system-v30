#!/usr/bin/env python3
"""
Test UI Components
This script tests the modernized UI components to ensure they work properly.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
try:
    from modules.ui_components import ProgressDialog, PaginatedListView, FastSearchEntry
    print("✓ UI components imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

class TestDataLoader:
    """Mock data loader for testing"""
    
    def __init__(self):
        # Generate test data
        self.data = []
        for i in range(100):
            self.data.append({
                'id': i + 1,
                'name': f'Item {i + 1}',
                'category': f'Category {(i % 5) + 1}',
                'price': f'${(i + 1) * 10:.2f}',
                'stock': (i + 1) * 2
            })
    
    def load_page(self, page=1, page_size=10, search=None):
        """Mock data loader function"""
        # Filter data based on search
        filtered_data = self.data
        if search:
            filtered_data = [
                item for item in self.data 
                if search.lower() in item['name'].lower() or 
                   search.lower() in item['category'].lower()
            ]
        
        # Calculate pagination
        total_count = len(filtered_data)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]
        
        # Return mock result object
        class MockResult:
            def __init__(self, data, total_count):
                self.data = data
                self.total_count = total_count
        
        return MockResult(page_data, total_count)
    
    def search_items(self, search_term, limit=10):
        """Mock search function"""
        results = []
        for item in self.data:
            if (search_term.lower() in item['name'].lower() or 
                search_term.lower() in item['category'].lower()):
                results.append(item)
                if len(results) >= limit:
                    break
        return results

def test_progress_dialog():
    """Test ProgressDialog component"""
    print("Testing ProgressDialog...")
    
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    try:
        # Test basic progress dialog
        progress = ProgressDialog(root, "Test Progress", cancelable=True)
        progress.update_status("Testing progress dialog...")
        progress.set_progress(50)
        
        # Test auto-close after delay
        root.after(2000, progress.close)
        root.after(2500, root.quit)
        
        root.mainloop()
        print("✓ ProgressDialog test passed")
        return True
        
    except Exception as e:
        print(f"✗ ProgressDialog test failed: {e}")
        return False
    finally:
        root.destroy()

def test_paginated_list_view():
    """Test PaginatedListView component"""
    print("Testing PaginatedListView...")
    
    root = tk.Tk()
    root.title("PaginatedListView Test")
    root.geometry("800x600")
    
    try:
        # Create test data loader
        data_loader = TestDataLoader()
        
        # Create paginated list view
        columns = ['id', 'name', 'category', 'price', 'stock']
        headers = {
            'id': 'ID',
            'name': 'Name',
            'category': 'Category',
            'price': 'Price',
            'stock': 'Stock'
        }
        widths = {
            'id': 50,
            'name': 200,
            'category': 150,
            'price': 100,
            'stock': 100
        }
        
        list_view = PaginatedListView(
            root,
            columns=columns,
            data_loader=data_loader.load_page,
            page_size=15,
            headers=headers,
            widths=widths,
            height=12
        )
        
        # Load initial data
        list_view.load_data()
        
        # Test auto-close after delay
        root.after(5000, root.quit)
        
        root.mainloop()
        print("✓ PaginatedListView test passed")
        return True
        
    except Exception as e:
        print(f"✗ PaginatedListView test failed: {e}")
        return False
    finally:
        root.destroy()

def test_fast_search_entry():
    """Test FastSearchEntry component"""
    print("Testing FastSearchEntry...")
    
    root = tk.Tk()
    root.title("FastSearchEntry Test")
    root.geometry("400x300")
    
    try:
        # Create test data loader
        data_loader = TestDataLoader()
        
        # Create frame for search
        frame = tk.Frame(root)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create search entry
        def on_select(item):
            print(f"Selected item: {item}")
        
        search_entry = FastSearchEntry(
            frame,
            data_loader.search_items,
            on_select_callback=on_select,
            placeholder="Search items..."
        )
        search_entry.get_frame().pack(fill='x', pady=10)
        
        # Add instruction label
        instruction = tk.Label(
            frame,
            text="Type to search for items...",
            font=('Segoe UI', 10)
        )
        instruction.pack(pady=10)
        
        # Test auto-close after delay
        root.after(8000, root.quit)
        
        root.mainloop()
        print("✓ FastSearchEntry test passed")
        return True
        
    except Exception as e:
        print(f"✗ FastSearchEntry test failed: {e}")
        return False
    finally:
        root.destroy()

def main():
    """Run all UI component tests"""
    print("=== UI Components Test Suite ===")
    print()
    
    tests = [
        test_progress_dialog,
        test_paginated_list_view,
        test_fast_search_entry
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=== Test Summary ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("✓ All UI component tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

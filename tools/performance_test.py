"""
Performance Test Script

This script runs a series of tests to measure the performance of both
standard and enhanced pages to verify the improvements.
"""

import tkinter as tk
import ttkbootstrap as ttk
import time
import threading
import logging
import sys
import os
from functools import partial
from queue import Queue
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules from the sales system
from modules.enhanced_data_access import enhanced_data
from modules.db_manager import initialize_connection_pool, shutdown_pool
from modules.Login import current_user
from modules.logger import logger
from modules.utils import init_background_tasks, shutdown_background_tasks

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestResult:
    """Class to store test results"""
    
    def __init__(self, name):
        self.name = name
        self.standard_time = None
        self.enhanced_time = None
        self.improvement = None
    
    def set_standard(self, time_ms):
        self.standard_time = time_ms
    
    def set_enhanced(self, time_ms):
        self.enhanced_time = time_ms
        if self.standard_time:
            self.improvement = ((self.standard_time - self.enhanced_time) / self.standard_time) * 100
    
    def __str__(self):
        imp = f"{self.improvement:.2f}%" if self.improvement is not None else "N/A"
        return f"{self.name}: Standard={self.standard_time:.2f}ms, Enhanced={self.enhanced_time:.2f}ms, Improvement={imp}"

class PerformanceTestApp(ttk.Window):
    """Application to run performance tests on the sales system"""
    
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Sales System Performance Test")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Initialize system
        initialize_connection_pool()
        init_background_tasks()
        
        # Mock login
        current_user["Username"] = "test_user"
        current_user["Role"] = "admin"
        
        # Setup UI
        self._create_ui()
        
        # Results
        self.results = {}
        
        # Test queue
        self.test_queue = Queue()
        self.running = False
        
        # Start the event processor
        self.after(100, self._process_events)
    
    def _create_ui(self):
        """Create the UI"""
        # Main container
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            container,
            text="Sales System Performance Test",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=10)
        
        # Description
        desc_label = ttk.Label(
            container,
            text="This tool tests the performance difference between standard and enhanced pages",
            font=("Arial", 12)
        )
        desc_label.pack(pady=10)
        
        # Tests frame
        tests_frame = ttk.LabelFrame(container, text="Available Tests")
        tests_frame.pack(fill="both", expand=True, pady=10)
        
        # Test buttons
        self.test_buttons = []
        
        tests = [
            ("Load Products Test (Small)", self._run_load_products_test_small),
            ("Load Products Test (Large)", self._run_load_products_test_large),
            ("Search Products Test", self._run_search_test),
            ("Product Add/Edit Test", self._run_product_edit_test),
            ("Run All Tests", self._run_all_tests)
        ]
        
        for i, (name, cmd) in enumerate(tests):
            btn = ttk.Button(
                tests_frame,
                text=name,
                command=cmd,
                bootstyle="primary"
            )
            btn.pack(fill="x", pady=5, padx=20)
            self.test_buttons.append(btn)
        
        # Results frame
        results_frame = ttk.LabelFrame(container, text="Test Results")
        results_frame.pack(fill="both", expand=True, pady=10)
        
        # Results text
        self.results_text = tk.Text(
            results_frame,
            height=12,
            width=80,
            font=("Courier New", 10)
        )
        self.results_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Progress bar
        self.progress_var = ttk.IntVar()
        self.progress_bar = ttk.Progressbar(
            container,
            variable=self.progress_var,
            maximum=100,
            bootstyle="success"
        )
        self.progress_bar.pack(fill="x", pady=10)
        
        # Status label
        self.status_var = ttk.StringVar(value="Ready")
        status_label = ttk.Label(
            container,
            textvariable=self.status_var,
            font=("Arial", 10)
        )
        status_label.pack(pady=5)
        
        # Close button
        close_btn = ttk.Button(
            container,
            text="Close",
            command=self._on_close,
            bootstyle="danger"
        )
        close_btn.pack(pady=10)
    
    def _process_events(self):
        """Process events from the test queue"""
        if not self.test_queue.empty():
            event = self.test_queue.get()
            event_type = event.get('type')
            
            if event_type == 'start_test':
                self._update_status(f"Running test: {event.get('name', 'Unknown')}")
                self.progress_var.set(0)
                
            elif event_type == 'test_progress':
                progress = event.get('progress', 0)
                self.progress_var.set(progress)
                
            elif event_type == 'test_complete':
                result = event.get('result')
                self._display_result(result)
                self.progress_var.set(100)
                
                # If there are more tests in the queue, start the next one
                if hasattr(self, '_current_test_index') and self._current_test_index < len(self._tests_to_run) - 1:
                    self._current_test_index += 1
                    self.after(500, self._run_next_test)
                else:
                    self._update_status("Testing complete")
                    self.running = False
                
            elif event_type == 'error':
                error = event.get('error', 'Unknown error')
                self._update_status(f"Error: {error}")
                self.running = False
        
        # Schedule next check
        self.after(100, self._process_events)
    
    def _update_status(self, status):
        """Update the status text"""
        self.status_var.set(status)
    
    def _display_result(self, result):
        """Display a test result"""
        if not isinstance(result, TestResult):
            return
        
        self.results_text.insert("end", str(result) + "\n")
        self.results_text.see("end")
        self.results[result.name] = result
    
    def _run_all_tests(self):
        """Run all available tests"""
        if self.running:
            return
        
        self.running = True
        self.results_text.delete("1.0", "end")
        self._update_status("Running all tests...")
        
        # Define the tests to run
        self._tests_to_run = [
            self._run_load_products_test_small,
            self._run_load_products_test_large,
            self._run_search_test,
            self._run_product_edit_test
        ]
        
        self._current_test_index = 0
        self._run_next_test()
    
    def _run_next_test(self):
        """Run the next test in the queue"""
        if self._current_test_index < len(self._tests_to_run):
            test_func = self._tests_to_run[self._current_test_index]
            test_func()
    
    def _run_load_products_test_small(self):
        """Test loading a small number of products"""
        self._run_performance_test(
            "Load Products (Small)",
            lambda: self._test_standard_products_load(20),
            lambda: self._test_enhanced_products_load(20)
        )
    
    def _run_load_products_test_large(self):
        """Test loading a large number of products"""
        self._run_performance_test(
            "Load Products (Large)",
            lambda: self._test_standard_products_load(100),
            lambda: self._test_enhanced_products_load(100)
        )
    
    def _run_search_test(self):
        """Test product search performance"""
        self._run_performance_test(
            "Product Search",
            lambda: self._test_standard_search("product"),
            lambda: self._test_enhanced_search("product")
        )
    
    def _run_product_edit_test(self):
        """Test product edit performance"""
        self._run_performance_test(
            "Product Edit",
            self._test_standard_product_edit,
            self._test_enhanced_product_edit
        )
    
    def _run_performance_test(self, name, standard_func, enhanced_func):
        """Run a performance test comparing standard vs enhanced implementation"""
        if self.running:
            return
        
        self.running = True
        result = TestResult(name)
        
        # Create and start a background thread for the test
        def run_test():
            try:
                # Queue start event
                self.test_queue.put({
                    'type': 'start_test',
                    'name': name
                })
                
                # Test standard implementation
                self.test_queue.put({
                    'type': 'test_progress',
                    'progress': 10
                })
                
                start_time = time.time()
                standard_func()
                standard_time = (time.time() - start_time) * 1000
                result.set_standard(standard_time)
                
                # Test enhanced implementation
                self.test_queue.put({
                    'type': 'test_progress',
                    'progress': 50
                })
                
                start_time = time.time()
                enhanced_func()
                enhanced_time = (time.time() - start_time) * 1000
                result.set_enhanced(enhanced_time)
                
                # Queue completion event
                self.test_queue.put({
                    'type': 'test_progress',
                    'progress': 90
                })
                
                self.test_queue.put({
                    'type': 'test_complete',
                    'result': result
                })
                
            except Exception as e:
                logger.error(f"Error in test '{name}': {e}")
                self.test_queue.put({
                    'type': 'error',
                    'error': str(e)
                })
        
        # Start the thread
        threading.Thread(target=run_test, daemon=True).start()
    
    def _test_standard_products_load(self, count):
        """Test standard product loading"""
        from modules.data_access import get_products
        
        start = time.time()
        products = get_products(limit=count)
        elapsed = time.time() - start
        
        logger.info(f"Standard product load: {len(products)} products in {elapsed:.3f}s")
        return products
    
    def _test_enhanced_products_load(self, count):
        """Test enhanced product loading"""
        event = threading.Event()
        result = None
        
        def on_success(data):
            nonlocal result
            result = data
            event.set()
        
        def on_error(error):
            logger.error(f"Error loading products: {error}")
            event.set()
        
        # Call the enhanced function
        enhanced_data.get_products_paged(
            page=1,
            page_size=count,
            on_success=on_success,
            on_error=on_error
        )
        
        # Wait for completion
        event.wait(timeout=10)
        
        if result:
            logger.info(f"Enhanced product load: {len(result.items)} products")
        
        return result
    
    def _test_standard_search(self, term):
        """Test standard product search"""
        from modules.data_access import search_products
        
        start = time.time()
        products = search_products(term)
        elapsed = time.time() - start
        
        logger.info(f"Standard search: found {len(products)} products in {elapsed:.3f}s")
        return products
    
    def _test_enhanced_search(self, term):
        """Test enhanced product search"""
        event = threading.Event()
        result = None
        
        def on_success(data):
            nonlocal result
            result = data
            event.set()
        
        def on_error(error):
            logger.error(f"Error searching products: {error}")
            event.set()
        
        # Call the enhanced function
        enhanced_data.get_products_paged(
            page=1,
            page_size=50,
            search_term=term,
            on_success=on_success,
            on_error=on_error
        )
        
        # Wait for completion
        event.wait(timeout=10)
        
        if result:
            logger.info(f"Enhanced search: found {result.total_items} products")
        
        return result
    
    def _test_standard_product_edit(self):
        """Test standard product edit"""
        from modules.data_access import get_products, update_product
        from modules.db_manager import ConnectionContext
        
        # Get a product first
        products = get_products(limit=1)
        if not products:
            logger.warning("No products found for edit test")
            return False
        
        product = products[0]
        product_id = product["ProductID"]
        
        # Create updated product data
        updated_product = {
            "ProductID": product_id,
            "ProductName": product["ProductName"] + " (updated)",
            "Price": float(product["Price"]) + 0.5,
            "Stock": int(product["Stock"]) + 1,
            "Category": product["Category"]
        }
        
        # Measure performance of update
        start = time.time()
        
        # Update the product
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            result = update_product(cursor, updated_product)
            conn.commit()
        
        elapsed = time.time() - start
        logger.info(f"Standard product edit completed in {elapsed:.3f}s")
        
        return result
    
    def _test_enhanced_product_edit(self):
        """Test enhanced product edit"""
        # First get a product
        event = threading.Event()
        product = None
        
        def on_product_loaded(result):
            nonlocal product
            if result and result.items:
                product = result.items[0]
            event.set()
        
        # Get a product
        enhanced_data.get_products_paged(
            page=1,
            page_size=1,
            on_success=on_product_loaded,
            on_error=lambda e: event.set()
        )
        
        # Wait for completion
        event.wait(timeout=10)
        
        if not product:
            logger.warning("No products found for enhanced edit test")
            return False
        
        # Create updated product data
        updated_product = {
            "ProductID": product["ProductID"],
            "ProductName": product["ProductName"] + " (enhanced update)",
            "Price": float(product["Price"]) + 0.75,
            "Stock": int(product["Stock"]) + 2,
            "Category": product["Category"]
        }
        
        # Reset event
        event.clear()
        result = None
        
        def on_update_complete(res):
            nonlocal result
            result = res
            event.set()
        
        # Update the product
        enhanced_data.update_product(
            updated_product,
            on_success=on_update_complete,
            on_error=lambda e: event.set()
        )
        
        # Wait for completion
        event.wait(timeout=10)
        
        logger.info("Enhanced product edit completed")
        return result
    
    def _on_close(self):
        """Handle window close"""
        if self.running:
            if not tk.messagebox.askyesno(
                "Confirm Exit",
                "Tests are still running. Are you sure you want to exit?"
            ):
                return
        
        # Clean up resources
        shutdown_background_tasks()
        shutdown_pool()
        
        # Destroy window
        self.destroy()

def main():
    """Main function"""
    try:
        app = PerformanceTestApp()
        app.mainloop()
    except Exception as e:
        logger.error(f"Error in performance test app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

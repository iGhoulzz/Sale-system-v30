"""
Test script for the enhanced pages implementation
This script will run tests to verify that the enhanced pages are working correctly
and measure their performance compared to the standard pages.
"""

import time
import sys
import os
import logging
import threading

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the necessary modules from the sales system
from modules.enhanced_data_access import enhanced_data, PagedResult
from modules.db_manager import ConnectionContext, init_pool, shutdown_pool

def test_enhanced_data_access():
    """Test the enhanced data access module"""
    logger.info("Testing enhanced data access...")
    
    # Initialize the connection pool
    init_pool()
    
    # Test product pagination
    test_pagination()
    
    # Test search performance
    test_search_performance()
    
    # Test background processing
    test_background_processing()
    
    # Shutdown the connection pool
    shutdown_pool()
    
    logger.info("Enhanced data access tests completed")

def test_pagination():
    """Test pagination functionality"""
    logger.info("Testing pagination...")
    
    # Test parameters
    page_sizes = [10, 20, 50, 100]
    
    for page_size in page_sizes:
        start_time = time.time()
        
        # Create a threading event to wait for the async operation
        event = threading.Event()
        result = None
        
        def on_success(data):
            nonlocal result
            result = data
            event.set()
            
        def on_error(error):
            logger.error(f"Error in pagination test: {error}")
            event.set()
        
        # Call the paginated data function
        enhanced_data.get_products_paged(
            page=1, 
            page_size=page_size,
            on_success=on_success,
            on_error=on_error
        )
        
        # Wait for the result (with timeout)
        event.wait(timeout=10)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log results
        if result:
            logger.info(f"Pagination test with page_size={page_size}: Loaded {len(result.items)} items "
                       f"(page {result.page}/{result.total_pages}, total: {result.total_items}) "
                       f"in {duration:.3f} seconds")
        else:
            logger.error(f"Pagination test failed for page_size={page_size}")

def test_search_performance():
    """Test search performance"""
    logger.info("Testing search performance...")
    
    # Test search terms
    search_terms = ["a", "product", "123", ""]
    
    for term in search_terms:
        start_time = time.time()
        
        # Create a threading event to wait for the async operation
        event = threading.Event()
        result = None
        
        def on_success(data):
            nonlocal result
            result = data
            event.set()
            
        def on_error(error):
            logger.error(f"Error in search test: {error}")
            event.set()
        
        # Call the search function
        enhanced_data.get_products_paged(
            page=1, 
            page_size=20,
            search_term=term,
            on_success=on_success,
            on_error=on_error
        )
        
        # Wait for the result (with timeout)
        event.wait(timeout=10)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log results
        if result:
            logger.info(f"Search test with term='{term}': Found {result.total_items} items "
                       f"in {duration:.3f} seconds")
        else:
            logger.error(f"Search test failed for term='{term}'")

def test_background_processing():
    """Test background task processing"""
    logger.info("Testing background processing...")
    
    # Test multiple concurrent tasks
    task_count = 5
    completed_count = 0
    start_time = time.time()
    
    # Create a threading event to wait for all tasks
    event = threading.Event()
    
    def test_task(task_id, delay):
        """Test task that simulates work with a delay"""
        time.sleep(delay)
        return f"Task {task_id} completed after {delay} seconds"
    
    def on_task_complete(result):
        nonlocal completed_count
        logger.info(f"Background task result: {result}")
        completed_count += 1
        if completed_count == task_count:
            event.set()
    
    # Start multiple background tasks
    logger.info(f"Starting {task_count} background tasks...")
    for i in range(task_count):
        delay = 0.2 + (i * 0.1)  # Different delay for each task
        enhanced_data.run_in_background(
            lambda task_id=i, delay=delay: test_task(task_id, delay),
            on_success=on_task_complete,
            on_error=lambda error: logger.error(f"Background task error: {error}")
        )
    
    # Wait for all tasks to complete (with timeout)
    event.wait(timeout=10)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log results
    logger.info(f"Background processing test: Completed {completed_count}/{task_count} tasks "
               f"in {duration:.3f} seconds")

if __name__ == "__main__":
    test_enhanced_data_access()

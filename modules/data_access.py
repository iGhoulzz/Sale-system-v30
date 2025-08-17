"""
modules/data_access.py - Data Access Layer
-----------------------------------------
Centralizes all database access operations to:
1. Reduce SQL duplication across UI modules
2. Provide consistent error handling and logging
3. Implement proper transaction management
4. Enable unit testing through abstraction
"""

import sqlite3
import datetime
import logging
import queue
import threading
import time
import functools
import sys
import codecs
from typing import Dict, List, Tuple, Any, Optional, Union

from modules.db_manager import get_connection, return_connection, ConnectionContext
from modules.Login import current_user

# Configure logging with UTF-8 encoding to support all languages
if sys.platform == 'win32':
    # Windows needs special handling for Unicode in console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app.log',
        filemode='a',
        encoding='utf-8'  # Explicitly set file encoding to UTF-8
    )
else:
    # Other platforms handle Unicode better
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app.log',
        filemode='a',
        encoding='utf-8'  # Explicitly set file encoding to UTF-8
    )

logger = logging.getLogger('data_access')

# If running in console mode, add UTF-8 compatible console handler
if not hasattr(sys, 'frozen'):  # Not a frozen executable
    # Custom handler for console output that respects encoding
    class EncodedStdoutHandler(logging.StreamHandler):
        def __init__(self, stream=None):
            if stream is None and sys.platform == 'win32':
                stream = codecs.getwriter('utf-8')(sys.stdout.buffer)
            super().__init__(stream)
            
    console_handler = EncodedStdoutHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# ===== Helper Functions =====

# Create logging queue and worker thread
_log_queue = queue.Queue(maxsize=500)  # Limit queue size to prevent memory issues
_log_worker_thread = None
_log_worker_lock = threading.RLock()
_log_batch_size = 50  # Process logs in batches

def _log_worker():
    """Background worker that processes logging operations."""
    while True:
        try:
            # Collect a batch of log operations
            batch = []
            log_item = _log_queue.get()
            
            # None is the signal to exit
            if log_item is None:
                break
                
            # Add first item to batch
            batch.append(log_item)
            
            # Try to collect more items up to batch size
            try:
                for _ in range(_log_batch_size - 1):
                    # Get more items without blocking
                    item = _log_queue.get_nowait()
                    if item is None:  # Exit signal
                        break
                    batch.append(item)
            except queue.Empty:
                # If no more items, continue with what we have
                pass
                
            # Process the batch in a single transaction
            try:
                with ConnectionContext() as conn:
                    cursor = conn.cursor()
                    
                    # Prepare batch parameters
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    params = [(user_id, operation, timestamp) for operation, user_id in batch]
                    
                    # Execute batch insert
                    cursor.executemany(
                        """
                        INSERT INTO ActivityLog (UserID, Action, DateTime)
                        VALUES (?, ?, ?)
                        """,
                        params
                    )
                    conn.commit()
            except Exception as e:
                # Log error but don't propagate - logging should never break the app
                logger.error(f"Failed to record batch of {len(batch)} activity logs: {str(e)}")
            finally:
                # Mark all batch items as done
                for _ in range(len(batch)):
                    _log_queue.task_done()
                
        except Exception as e:
            # Handle any unexpected errors in the worker thread
            logger.error(f"Error in log worker thread: {str(e)}")
            
            # Don't exit the loop - just continue to the next item

def start_log_worker():
    """Start the background logging worker thread if not already running."""
    global _log_worker_thread
    
    with _log_worker_lock:
        if _log_worker_thread is None or not _log_worker_thread.is_alive():
            _log_worker_thread = threading.Thread(
                target=_log_worker,
                name="LogWorkerThread",
                daemon=True  # Make thread a daemon so it exits when main thread exits
            )
            _log_worker_thread.start()

def stop_log_worker():
    """Stop the background logging worker thread."""
    global _log_worker_thread
    
    with _log_worker_lock:
        if _log_worker_thread is not None and _log_worker_thread.is_alive():
            # Send sentinel to signal exit
            _log_queue.put(None)
            # Wait for thread to exit (with timeout)
            _log_worker_thread.join(timeout=2.0)
            _log_worker_thread = None

# Start the log worker thread when module is imported
start_log_worker()

def log_db_operation(operation: str) -> None:
    """
    Log a database operation with the current user information.
    Only logs critical operations based on keywords.
    
    Args:
        operation: Description of the operation being performed
    """
    # Define keywords that indicate critical operations worth logging
    critical_keywords = [
        "Added", "Created", "Updated", "Deleted", "Recorded",
        "Payment", "Completed sale", "debit sale", 
        "Marked", "Stock", "inventory", "loss",
        "logged in", "logged out", "Invoice", "Error"
    ]
    
    # Only log if the operation contains critical keywords
    should_log = any(keyword.lower() in operation.lower() for keyword in critical_keywords)
    
    if not should_log:
        return  # Skip non-critical operations
    
    try:
        uid = current_user.get("UserID")
        if not uid:
            return
        
        # Queue the log operation to be processed in the background
        _log_queue.put((operation, uid))
        
        # Ensure the worker thread is running
        start_log_worker()
        
    except Exception as e:
        logger.error(f"Failed to queue log operation: {str(e)}")

def execute_transaction(func):
    """Decorator that handles transaction management"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from modules.db_manager import get_connection, return_connection
        conn = get_connection()
        cursor = conn.cursor()  # Create a cursor to pass to the function
        try:
            result = func(cursor, *args, **kwargs)  # Pass cursor instead of connection
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction error in {func.__name__}: {e}")
            raise
        finally:
            # Return connection to the pool instead of closing it
            return_connection(conn)
    return wrapper

# ===== Cache for frequently accessed data =====
_cache = {
    'product_categories': {
        'data': None,
        'timestamp': 0,
        'ttl': 300  # 5 minutes TTL for categories
    },
    'products': {
        'data': {},  # Will store products with query parameters as key
        'timestamp': {},  # Timestamp for each query
        'ttl': 10  # 10 seconds TTL for products - balance between freshness and performance
    }
}

def get_product_categories() -> List[str]:
    """
    Get a list of all unique product categories with caching.
    
    Returns:
        List of category names
    """
    cache_entry = _cache['product_categories']
    now = time.time()
    
    # Return cached data if still valid
    if cache_entry['data'] is not None and now - cache_entry['timestamp'] < cache_entry['ttl']:
        return cache_entry['data']
    
    # Cache expired or empty, fetch fresh data
    try:
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT Category FROM Products ORDER BY Category")
            categories = [row[0] for row in cursor.fetchall()]
        
        # Update cache
        cache_entry['data'] = categories
        cache_entry['timestamp'] = now
        
        return categories
    
    except Exception as e:
        logger.error(f"Error fetching product categories: {str(e)}")
        # If we have cached data but it's expired, still return it rather than failing
        if cache_entry['data'] is not None:
            logger.warning("Returning stale cached categories due to fetch error")
            return cache_entry['data']
        raise

def invalidate_cache(key: str = None) -> None:
    """
    Invalidate cache entries.
    
    Args:
        key: Specific cache key to invalidate, or None for all keys
    """
    if key is None:
        # Invalidate all caches
        for cache_key in _cache:
            if isinstance(_cache[cache_key]['data'], dict):
                # Clear dictionaries like the products cache
                _cache[cache_key]['data'] = {}
                _cache[cache_key]['timestamp'] = {}
            else:
                # Reset simple caches like categories
                _cache[cache_key]['data'] = None
                _cache[cache_key]['timestamp'] = 0
    elif key in _cache:
        # Invalidate specific cache
        if isinstance(_cache[key]['data'], dict):
            _cache[key]['data'] = {}
            _cache[key]['timestamp'] = {}
        else:
            _cache[key]['data'] = None
            _cache[key]['timestamp'] = 0

def clear_cache(older_than_seconds=300):
    """
    Clear cached data older than the specified time.
    
    Args:
        older_than_seconds: Clear cache entries older than this many seconds
    """
    now = time.time()
    entries_cleared = 0
    
    for cache_key in _cache:
        if isinstance(_cache[cache_key]['data'], dict):
            # Handle dictionary caches like products cache
            to_remove = []
            for key, timestamp in _cache[cache_key]['timestamp'].items():
                if now - timestamp > older_than_seconds:
                    to_remove.append(key)
            
            # Remove expired entries
            for key in to_remove:
                if key in _cache[cache_key]['data']:
                    del _cache[cache_key]['data'][key]
                if key in _cache[cache_key]['timestamp']:
                    del _cache[cache_key]['timestamp'][key]
                entries_cleared += 1
        else:
            # Handle simple cache entries
            if now - _cache[cache_key]['timestamp'] > older_than_seconds:
                _cache[cache_key]['data'] = None
                _cache[cache_key]['timestamp'] = 0
                entries_cleared += 1
    
    logger.info(f"Cache cleanup: {entries_cleared} expired cache entries removed")
    return entries_cleared

# Schedule periodic cache cleanup
def schedule_cache_cleanup(interval_seconds=1800):
    """
    Schedule periodic cache cleanup to prevent memory leaks.
    
    Args:
        interval_seconds: How often to run cache cleanup (default: 30 minutes)
    """
    def _cleanup_task():
        while True:
            time.sleep(interval_seconds)
            try:
                clear_cache()
            except Exception as e:
                logger.error(f"Error during scheduled cache cleanup: {str(e)}")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(
        target=_cleanup_task,
        name="CacheCleanupThread",
        daemon=True
    )
    cleanup_thread.start()
    logger.info(f"Scheduled cache cleanup every {interval_seconds/60:.1f} minutes")

# Start the cache cleanup thread when module is imported
schedule_cache_cleanup()

def get_products(
    category: Optional[str] = None,
    search_term: Optional[str] = None,
    show_out_of_stock: bool = False
) -> List[Dict[str, Any]]:
    """
    Get products from the database with optional filtering.
    
    Args:
        category: Filter by product category
        search_term: Search in product name or barcode
        show_out_of_stock: Whether to include out-of-stock products
    
    Returns:
        List of product dictionaries
    """
    # Create a cache key based on query parameters
    cache_key = f"{category}:{search_term}:{show_out_of_stock}"
    cache_entry = _cache['products']
    now = time.time()
    
    # Check if we have a fresh cached result for this query
    if (cache_key in cache_entry['data'] and 
        cache_key in cache_entry['timestamp'] and 
        now - cache_entry['timestamp'][cache_key] < cache_entry['ttl']):
        return cache_entry['data'][cache_key]
    
    try:
        # Use ConnectionContext for thread safety
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Build optimized query with proper indexing hints
            query = """
                SELECT 
                    ProductID, Name, SellingPrice, BuyingPrice, 
                    Stock, Category, Barcode
                FROM 
                    Products
                WHERE 
                    1=1
            """
            params = []
            
            # Apply filters in order of selectivity for better performance
            if category and category != "All Categories":
                query += " AND Category = ? /* index: idx_products_category */"
                params.append(category)
            
            if not show_out_of_stock:
                query += " AND Stock > 0 /* index: idx_products_stock */"
            
            if search_term:
                query += " AND (Name LIKE ? OR Barcode LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])
            
            # Add optimized ordering
            if category and category != "All Categories":
                # If filtering by category, don't need to sort by category
                query += " ORDER BY Name"
            else:
                # Otherwise sort by category and then name
                query += " ORDER BY Category, Name"
            
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            products = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Store in cache
            cache_entry['data'][cache_key] = products
            cache_entry['timestamp'][cache_key] = now
            
            return products
    
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        # If we have cached data for this query but it's expired, still return it rather than failing
        if cache_key in cache_entry['data']:
            logger.warning(f"Returning stale cached products due to fetch error for query: {cache_key}")
            return cache_entry['data'][cache_key]
        # Return empty list instead of raising
        return []

@execute_transaction
def add_or_update_product(cursor, product_data: Dict[str, Any], is_update: bool = False) -> int:
    """
    Add a new product or update an existing one.
    
    Args:
        cursor: Database cursor from the transaction decorator
        product_data: Dictionary containing product information
        is_update: Whether this is an update to an existing product
    
    Returns:
        Product ID
    """
    try:
        if is_update:
            product_id = product_data.get('ProductID')
            
            cursor.execute("""
                UPDATE Products
                SET 
                    Name = ?, 
                    BuyingPrice = ?, 
                    SellingPrice = ?, 
                    Stock = ?,
                    Category = ?,
                    Barcode = ?
                WHERE 
                    ProductID = ?
            """, (
                product_data.get('Name'),
                product_data.get('BuyingPrice'),
                product_data.get('SellingPrice'),
                product_data.get('Stock'),
                product_data.get('Category'),
                product_data.get('Barcode'),
                product_id
            ))
            
            log_message = f"Updated product: {product_data.get('Name')} (ID: {product_id})"
        else:
            cursor.execute("""
                INSERT INTO Products 
                (Name, BuyingPrice, SellingPrice, Stock, Category, Barcode)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                product_data.get('Name'),
                product_data.get('BuyingPrice'),
                product_data.get('SellingPrice'),
                product_data.get('Stock'),
                product_data.get('Category'),
                product_data.get('Barcode')
            ))
            
            product_id = cursor.lastrowid
            log_message = f"Added new product: {product_data.get('Name')} (ID: {product_id})"
        
        log_db_operation(log_message)
        
        return product_id
    except Exception as e:
        logger.error(f"Error {'updating' if is_update else 'adding'} product: {str(e)}")
        raise

@execute_transaction
def update_product_stock(cursor, product_id: int, quantity_change: int, reason: str = None) -> None:
    """
    Update the stock quantity for a product.
    
    Args:
        cursor: Database cursor from the transaction decorator
        product_id: ID of the product to update
        quantity_change: Amount to add (positive) or remove (negative) from stock
        reason: Reason for the stock change (for logging)
    """
    # First get the current stock to verify operation is valid
    cursor.execute("SELECT Name, Stock FROM Products WHERE ProductID = ?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        raise ValueError(f"Product with ID {product_id} not found")
    
    product_name, current_stock = product
    new_stock = current_stock + quantity_change
    
    if new_stock < 0:
        raise ValueError(f"Cannot reduce stock below zero (current: {current_stock}, change: {quantity_change})")
    
    cursor.execute(
        "UPDATE Products SET Stock = ? WHERE ProductID = ?",
        (new_stock, product_id)
    )
    
    # Invalidate products cache after stock change
    invalidate_cache('products')
    
    action_type = "increased" if quantity_change > 0 else "decreased"
    log_message = f"Stock {action_type} for {product_name} by {abs(quantity_change)} units"
    if reason:
        log_message += f" - Reason: {reason}"
    
    log_db_operation(log_message)

@execute_transaction
def record_product_loss(cursor, product_id: int, quantity: int, reason: str) -> None:
    """
    Record a product loss (damage, expiry, etc.) and update inventory.
    
    Args:
        cursor: Database cursor from the transaction decorator
        product_id: ID of the product that was lost/damaged
        quantity: Amount of product lost
        reason: Reason for the loss
    """
    # Get product details
    cursor.execute("SELECT Name, Stock FROM Products WHERE ProductID = ?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        raise ValueError(f"Product with ID {product_id} not found")
    
    product_name, current_stock = product
    
    if quantity > current_stock:
        raise ValueError(f"Cannot record loss of {quantity} units when only {current_stock} are in stock")
    
    # Record the loss in a Losses table (create if it doesn't exist)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ProductLosses (
            LossID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductID INTEGER,
            Quantity INTEGER,
            Reason TEXT,
            DateTime TEXT,
            RecordedBy INTEGER,
            FOREIGN KEY (ProductID) REFERENCES Products(ProductID),
            FOREIGN KEY (RecordedBy) REFERENCES Users(UserID)
        )
    """)
    
    cursor.execute("""
        INSERT INTO ProductLosses (ProductID, Quantity, Reason, DateTime, RecordedBy)
        VALUES (?, ?, ?, ?, ?)
    """, (
        product_id,
        quantity,
        reason,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        current_user.get("UserID", 1)
    ))
    
    # Update the product stock
    cursor.execute(
        "UPDATE Products SET Stock = Stock - ? WHERE ProductID = ?",
        (quantity, product_id)
    )
    
    log_message = f"Recorded loss of {quantity} {product_name} - Reason: {reason}"
    log_db_operation(log_message)

@execute_transaction
def delete_product(cursor, product_id: int) -> str:
    """
    Delete a product from the database.
    
    Args:
        cursor: Database cursor from the transaction decorator
        product_id: ID of the product to delete
    
    Returns:
        Name of the deleted product
    """
    # Get product name for logging
    cursor.execute("SELECT Name FROM Products WHERE ProductID = ?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        raise ValueError(f"Product with ID {product_id} not found")
    
    product_name = product[0]
    
    # Check if the product is used in any sales
    cursor.execute("""
        SELECT COUNT(*) FROM InvoiceItems WHERE ProductID = ?
    """, (product_id,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        # Instead of deleting, mark as discontinued
        cursor.execute("""
            UPDATE Products 
            SET Discontinued = 1, Stock = 0 
            WHERE ProductID = ?
        """, (product_id,))
        log_message = f"Marked product as discontinued: {product_name} (ID: {product_id})"
    else:
        # Safe to delete if not referenced anywhere
        cursor.execute("DELETE FROM Products WHERE ProductID = ?", (product_id,))
        log_message = f"Deleted product: {product_name} (ID: {product_id})"
    
    log_db_operation(log_message)
    return product_name

# ===== Sales Management =====

def get_product_by_barcode(barcode: str) -> Optional[Dict[str, Any]]:
    """
    Look up a product by its barcode.
    
    Args:
        barcode: The product barcode to search for
    
    Returns:
        Product information or None if not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ProductID, Name, SellingPrice, BuyingPrice, 
                Stock, Category, Barcode
            FROM 
                Products
            WHERE 
                Barcode = ?
        """
        
        cursor.execute(query, (barcode,))
        
        product = cursor.fetchone()
        return_connection(conn)
        
        if not product:
            return None
        
        columns = ['ProductID', 'Name', 'SellingPrice', 'BuyingPrice', 
                  'Stock', 'Category', 'Barcode']
        
        return dict(zip(columns, product))
    
    except Exception as e:
        logger.error(f"Error looking up product by barcode: {str(e)}")
        raise

@execute_transaction
def complete_sale(cursor, cart_items: List[Dict[str, Any]], payment_method: str, 
                  customer_name: str = None, customer_phone: str = None, 
                  as_debit: bool = False, discount: float = 0.0) -> int:
    """
    Complete a sale transaction, creating invoice and updating stock.
    
    Args:
        cursor: Database cursor from transaction decorator
        cart_items: List of items in the cart
        payment_method: Method of payment (cash, card, etc.)
        customer_name: Optional customer name
        customer_phone: Optional customer phone
        as_debit: Whether this is a debit sale
        discount: Discount amount to apply to the sale
        
    Returns:
        ID of the created invoice
    """
    if not cart_items:
        raise ValueError("Cannot complete sale with empty cart")
        
    # Get current date/time
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate total (consider any discount)
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Apply discount if present
    if discount > 0:
        total = max(0, total - discount)
    
    # Determine status based on debit setting
    status = "Pending" if as_debit else "Paid"
    
    # Get current user
    user_id = current_user.get("UserID")
    employee_name = current_user.get("Username")
    
    # Get list of product IDs for batch stock check
    product_ids = [item['product_id'] for item in cart_items]
    
    # Check stock for all products in one query
    stock_levels = check_stock_batch(product_ids)
    
    # Verify stock for all items before proceeding
    insufficient_stock = []
    for item in cart_items:
        product_id = item['product_id']
        required_qty = item['quantity']
        
        # Check if product exists in stock_levels
        if product_id not in stock_levels:
            insufficient_stock.append(f"Product {item['name']} (ID: {product_id}) not found")
            continue
            
        available_qty = stock_levels[product_id]
        if available_qty < required_qty:
            insufficient_stock.append(f"Insufficient stock for {item['name']}: Need {required_qty}, have {available_qty}")
    
    # If any items have insufficient stock, raise exception
    if insufficient_stock:
        error_msg = "Cannot complete sale due to stock issues:\n" + "\n".join(insufficient_stock)
        raise ValueError(error_msg)
    
    # Create invoice record - matching the actual schema in init_db.py
    cursor.execute("""
        INSERT INTO Invoices 
        (DateTime, PaymentMethod, TotalAmount, Discount, ShiftEmployee)
        VALUES (?, ?, ?, ?, ?)
    """, (
        now, 
        payment_method,
        total, 
        discount or 0.0,
        employee_name
    ))
    
    # Get invoice ID
    invoice_id = cursor.lastrowid
    
    # Create invoice items
    for item in cart_items:
        cursor.execute("""
            INSERT INTO InvoiceItems
            (InvoiceID, ProductID, ProductName, Price, Quantity, Total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            item['product_id'],
            item['name'],
            item['price'],
            item['quantity'],
            item['price'] * item['quantity']
        ))
        
        # Update stock
        cursor.execute("""
            UPDATE Products
            SET Stock = Stock - ?
            WHERE ProductID = ?
        """, (item['quantity'], item['product_id']))
        
    # If this is a debit sale, create a debit record
    if as_debit and customer_name and customer_phone:
        cursor.execute("""
            INSERT INTO Debits
            (Name, Phone, InvoiceID, Amount, Status, DateTime)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            customer_name,
            customer_phone,
            invoice_id,
            total,
            status,
            now
        ))
    
    # Log the operation
    sale_type = "debit sale" if as_debit else "sale"
    log_db_operation(f"Completed {sale_type} with {len(cart_items)} items, invoice #{invoice_id}")
    
    return invoice_id

# ===== Debits Management =====

def get_debits(
    name_filter: str = None,
    phone_filter: str = None,
    date_filter: str = None,
    status_filter: str = None
) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    """
    Get debits with optional filtering.
    
    Args:
        name_filter: Filter by customer name
        phone_filter: Filter by customer phone
        date_filter: Filter by date
        status_filter: Filter by status (Pending, Paid, All)
    
    Returns:
        Tuple of (list of debits, statistics dict)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                d.InvoiceID, 
                d.Name, 
                d.Phone, 
                d.DateTime, 
                d.Amount, 
                CASE WHEN d.Status = 'Paid' THEN d.Amount ELSE 0 END as AmountPaid, 
                d.Status,
                CASE WHEN d.Status = 'Pending' THEN d.Amount ELSE 0 END as Balance
            FROM 
                Debits d
            WHERE 
                1=1
        """
        
        params = []
        if name_filter:
            query += " AND LOWER(d.Name) LIKE ?"
            params.append(f"%{name_filter.lower()}%")
        
        if phone_filter:
            query += " AND d.Phone LIKE ?"
            params.append(f"%{phone_filter}%")
        
        if date_filter:
            query += " AND d.DateTime LIKE ?"
            params.append(f"%{date_filter}%")
        
        if status_filter and status_filter != "All":
            query += " AND d.Status = ?"
            params.append(status_filter)
        
        query += " ORDER BY d.DateTime DESC"
        
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        debits = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Calculate statistics
        total_debits = 0
        pending_amount = 0
        paid_amount = 0
        
        for debit in debits:
            total_debits += debit['Amount']
            if debit['Status'] == "Pending":
                pending_amount += debit['Balance']
            else:
                paid_amount += debit['Amount']
        
        statistics = {
            'total': total_debits,
            'pending': pending_amount,
            'paid': paid_amount
        }
        
        return_connection(conn)
        return debits, statistics
    
    except Exception as e:
        logger.error(f"Error fetching debits: {str(e)}")
        raise

def get_invoice_items(invoice_id: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Get details of an invoice and its items.
    
    Args:
        invoice_id: The ID of the invoice to fetch
    
    Returns:
        Tuple of (invoice details, list of invoice items)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get invoice information from Debits table
        cursor.execute("""
            SELECT 
                d.InvoiceID, 
                d.Name as customer_name, 
                d.DateTime as date, 
                d.Amount as total,
                CASE WHEN d.Status = 'Paid' THEN d.Amount ELSE 0 END as paid,
                d.Phone as phone,
                CASE WHEN d.Status = 'Pending' THEN d.Amount ELSE 0 END as balance,
                d.Status as status
            FROM 
                Debits d
            WHERE 
                d.InvoiceID = ?
        """, (invoice_id,))
        
        invoice_row = cursor.fetchone()
        
        if not invoice_row:
            raise ValueError(f"Invoice #{invoice_id} not found")
        
        invoice_cols = ["invoice_id", "customer_name", "date", "total", 
                        "paid", "phone", "balance", "status"]
        invoice = dict(zip(invoice_cols, invoice_row))
        
        # Get invoice items
        cursor.execute("""
            SELECT 
                ProductID,
                ProductName,
                Price,
                Quantity,
                (Price * Quantity) as ItemTotal
            FROM 
                InvoiceItems
            WHERE 
                InvoiceID = ?
        """, (invoice_id,))
        
        item_cols = ["product_id", "product_name", "price", "quantity", "item_total"]
        items = [dict(zip(item_cols, row)) for row in cursor.fetchall()]
        
        return_connection(conn)
        return invoice, items
    
    except Exception as e:
        logger.error(f"Error fetching invoice items: {str(e)}")
        raise

def record_debit_payment(cursor=None, invoice_id=None, payment_amount=None, payment_method=None) -> None:
    """
    Record a payment for a debit.
    
    Args:
        cursor: Database cursor from the transaction decorator (can be None for direct calls)
        invoice_id: ID of the invoice being paid
        payment_amount: Amount being paid
        payment_method: Method of payment
    """
    # Check if we're being called directly without the transaction decorator
    # If cursor is None and invoice_id is provided, this is a direct call
    if cursor is None and invoice_id is not None:
        # We're being called directly, use the decorator
        @execute_transaction
        def _record_payment(cursor, invoice_id, payment_amount, payment_method):
            return record_debit_payment(cursor, invoice_id, payment_amount, payment_method)
        
        return _record_payment(invoice_id, payment_amount, payment_method)
    
    # If we have a cursor, we're being called within a transaction
    # Get debit information
    cursor.execute("""
        SELECT 
            DebitID, Amount, AmountPaid, Status
        FROM 
            Debits
        WHERE 
            InvoiceID = ?
    """, (invoice_id,))
    
    debit = cursor.fetchone()
    
    if not debit:
        raise ValueError(f"Invoice #{invoice_id} not found")
    
    debit_id, total_amount, amount_paid, status = debit
    
    if status == "Paid":
        raise ValueError("This invoice is already fully paid")
    
    # Calculate new amount paid
    new_amount_paid = (amount_paid or 0) + payment_amount
    
    # Determine if the debit is now fully paid
    new_status = "Paid" if new_amount_paid >= total_amount else "Pending"
    
    # Update debit with new payment information
    cursor.execute("""
        UPDATE Debits
        SET Status = ?, AmountPaid = ?
        WHERE DebitID = ?
    """, (new_status, new_amount_paid, debit_id))
    
    # Record payment in Payments table
    cursor.execute("""
        INSERT INTO Payments (DebitID, Amount, PaymentMethod, DateTime, RecordedBy)
        VALUES (?, ?, ?, ?, ?)
    """, (
        debit_id,
        payment_amount,
        payment_method,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        current_user.get("UserID", 1)
    ))
    
    # Log the payment
    log_message = f"Payment of ${payment_amount:.2f} recorded for invoice #{invoice_id} via {payment_method}"
    log_db_operation(log_message)

@execute_transaction
def add_debit(cursor, name: str, phone: str, invoice_id: int, amount: float, notes: str = None) -> int:
    """
    Add a new debit record with proper validation.
    
    Args:
        cursor: Database cursor from the transaction decorator
        name: Customer name
        phone: Customer phone number
        invoice_id: Invoice ID reference
        amount: Debit amount
        notes: Optional notes about the debit
        
    Returns:
        The ID of the newly created debit record
        
    Raises:
        ValueError: If any of the inputs are invalid or if the invoice already exists
    """
    # Validate inputs
    if not name or not name.strip():
        raise ValueError("Customer name is required")
        
    if not phone or not phone.strip():
        raise ValueError("Phone number is required")
        
    if not invoice_id:
        raise ValueError("Invoice ID is required")
        
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    
    # Check if invoice ID already exists to prevent duplicates
    cursor.execute("SELECT COUNT(*) FROM Debits WHERE InvoiceID = ?", (invoice_id,))
    count = cursor.fetchone()[0]
    if count > 0:
        raise ValueError(f"A debit record for invoice #{invoice_id} already exists")
    
    # Create debit record
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO Debits
        (Name, Phone, InvoiceID, Amount, Status, DateTime, Notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, phone, invoice_id, amount, "Pending", current_date, notes)
    )
    
    debit_id = cursor.lastrowid
    
    # Log the creation
    log_message = f"Created new debit #{debit_id} for {name} with amount ${amount:.2f}"
    log_db_operation(log_message)
    
    return debit_id

# ===== Financial Dashboard =====

def get_daily_sales_summary(date: str = None) -> Dict[str, Any]:
    """
    Get sales summary for a specific date or today.
    
    Args:
        date: Date to get summary for (format: YYYY-MM-DD) or None for today
    
    Returns:
        Dictionary with sales statistics
    """
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get total sales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(TotalAmount) as total_amount,
                SUM(TotalAmount) as paid_amount,
                SUM(0) as pending_amount
            FROM 
                Invoices
            WHERE 
                DATE(DateTime) = ?
        """, (date,))
        
        row = cursor.fetchone()
        
        if not row or not row[0]:
            return {
                'date': date,
                'total_invoices': 0,
                'total_amount': 0,
                'paid_amount': 0,
                'pending_amount': 0,
                'payment_methods': {}
            }
        
        total_invoices, total_amount, paid_amount, pending_amount = row
        
        # Get payment method breakdown
        cursor.execute("""
            SELECT 
                PaymentMethod, 
                COUNT(*) as count,
                SUM(TotalAmount) as amount
            FROM 
                Invoices
            WHERE 
                DATE(DateTime) = ?
            GROUP BY 
                PaymentMethod
        """, (date,))
        
        payment_methods = {row[0]: {'count': row[1], 'amount': row[2]} 
                          for row in cursor.fetchall()}
        
        return_connection(conn)
        
        return {
            'date': date,
            'total_invoices': total_invoices,
            'total_amount': total_amount or 0,
            'paid_amount': paid_amount or 0,
            'pending_amount': pending_amount or 0,
            'payment_methods': payment_methods
        }
    
    except Exception as e:
        logger.error(f"Error fetching daily sales summary: {str(e)}")
        raise

def get_monthly_sales_summary(year: int, month: int) -> Dict[str, Any]:
    """
    Get monthly sales summary.
    
    Args:
        year: Year to get summary for
        month: Month to get summary for (1-12)
    
    Returns:
        Dictionary with monthly sales statistics and daily breakdown
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Format month for SQL queries
        month_str = f"{year}-{month:02d}"
        
        # Get monthly totals
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(TotalAmount) as total_amount,
                SUM(TotalAmount) as paid_amount,
                SUM(0) as pending_amount
            FROM 
                Invoices
            WHERE 
                strftime('%Y-%m', DateTime) = ?
        """, (month_str,))
        
        row = cursor.fetchone()
        total_invoices, total_amount, paid_amount, pending_amount = row if row[0] else (0, 0, 0, 0)
        
        # Get daily breakdown
        cursor.execute("""
            SELECT 
                strftime('%Y-%m-%d', DateTime) as sale_date,
                COUNT(*) as invoice_count,
                SUM(TotalAmount) as total
            FROM 
                Invoices
            WHERE 
                strftime('%Y-%m', DateTime) = ?
            GROUP BY 
                sale_date
            ORDER BY 
                sale_date
        """, (month_str,))
        
        daily_sales = {row[0]: {'count': row[1], 'amount': row[2]} 
                      for row in cursor.fetchall()}
        
        # Get payment method breakdown
        cursor.execute("""
            SELECT 
                PaymentMethod, 
                COUNT(*) as count,
                SUM(TotalAmount) as amount
            FROM 
                Invoices
            WHERE 
                strftime('%Y-%m', DateTime) = ?
            GROUP BY 
                PaymentMethod
        """, (month_str,))
        
        payment_methods = {row[0]: {'count': row[1], 'amount': row[2]} 
                          for row in cursor.fetchall()}
        
        return_connection(conn)
        
        return {
            'year': year,
            'month': month,
            'total_invoices': total_invoices,
            'total_amount': total_amount or 0,
            'paid_amount': paid_amount or 0,
            'pending_amount': pending_amount or 0,
            'daily_sales': daily_sales,
            'payment_methods': payment_methods
        }
    
    except Exception as e:
        logger.error(f"Error fetching monthly sales summary: {str(e)}")
        raise

def get_product_stock(product_id: int) -> Optional[Dict[str, Any]]:
    """
    Get current stock information for a specific product.
    
    Args:
        product_id: ID of the product to check
        
    Returns:
        Dictionary with stock information or None if product not found
    """
    try:
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.ProductID, 
                    p.Name,
                    p.Stock,
                    p.Category
                FROM Products p
                WHERE p.ProductID = ?
            """, (product_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Return stock information
            return {
                'id': row[0],
                'name': row[1],
                'stock': row[2],
                'category': row[3]
            }
            
    except Exception as e:
        logger.error(f"Failed to get product stock for ID {product_id}: {str(e)}")
        raise Exception(f"Error checking product stock: {str(e)}")

def check_stock_batch(product_ids: List[int]) -> Dict[int, int]:
    """
    Check stock for multiple products in a single database query.
    
    This is a performance optimization for operations that need to check
    multiple products at once (like checking cart items before sale).
    Instead of making separate database calls for each product, this
    fetches all products in one query.
    
    Args:
        product_ids: List of product IDs to check
        
    Returns:
        Dictionary mapping product IDs to their current stock levels
    """
    if not product_ids:
        return {}
        
    try:
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Create placeholders for SQL IN clause
            placeholders = ','.join('?' * len(product_ids))
            
            # Execute single query for all products
            cursor.execute(f"""
                SELECT ProductID, Stock 
                FROM Products 
                WHERE ProductID IN ({placeholders})
            """, product_ids)
            
            # Build dictionary of product_id -> stock
            stock_dict = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Check if any products were not found
            missing_ids = set(product_ids) - set(stock_dict.keys())
            if missing_ids:
                logger.warning(f"Products not found in batch stock check: {missing_ids}")
                
            return stock_dict
            
    except Exception as e:
        logger.error(f"Error in batch stock check: {str(e)}")
        # Return empty dict on error
        return {}

@execute_transaction
def batch_execute(cursor, query: str, params_list: List[Tuple]) -> None:
    """
    Execute a batch operation with many parameter sets.
    This is much more efficient than executing the same query multiple times.
    
    Args:
        cursor: Database cursor from the transaction decorator
        query: SQL query to execute
        params_list: List of parameter tuples for batch execution
        
    Example:
        batch_execute(
            "UPDATE Products SET Stock = ? WHERE ProductID = ?",
            [(5, 1), (10, 2), (15, 3)]  # Updates 3 products' stock in one operation
        )
    """
    if not params_list:
        return
        
    try:
        # Execute the query for all parameter sets
        cursor.executemany(query, params_list)
        
        # Log the operation
        log_message = f"Executed batch operation: {len(params_list)} items processed"
        log_db_operation(log_message)
    except Exception as e:
        logger.error(f"Error executing batch operation: {str(e)}")
        raise 

# ===== Missing Function Aliases for Compatibility =====

def get_all_products():
    """Alias for get_products() for backward compatibility"""
    return get_products()

def get_sales_data(limit=None):
    """Get sales data with optional limit"""
    try:
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            if limit:
                cursor.execute("""
                    SELECT s.SaleID, s.Date, s.TotalAmount,
                           COUNT(si.SaleItemID) as item_count
                    FROM Sales s
                    LEFT JOIN SaleItems si ON s.SaleID = si.SaleID
                    GROUP BY s.SaleID, s.Date, s.TotalAmount
                    ORDER BY s.Date DESC
                    LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT s.SaleID, s.Date, s.TotalAmount,
                           COUNT(si.SaleItemID) as item_count
                    FROM Sales s
                    LEFT JOIN SaleItems si ON s.SaleID = si.SaleID
                    GROUP BY s.SaleID, s.Date, s.TotalAmount
                    ORDER BY s.Date DESC
                """)
            
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Error fetching sales data: {e}")
        return []

def get_debits_data(limit=None):
    """Get debits data with optional limit"""
    try:
        # Use the existing get_debits function with proper parameters
        return get_debits(limit=limit) if limit else get_debits()
    except Exception as e:
        logger.error(f"Error fetching debits data: {e}")
        return []

# Add missing functions that the frontend expects
def get_categories():
    """Alias for get_product_categories for backward compatibility"""
    return get_product_categories()

def get_recent_invoices(limit=10):
    """Get recent invoices from the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT InvoiceID, DateTime, PaymentMethod, TotalAmount, ShiftEmployee
            FROM Invoices 
            ORDER BY DateTime DESC 
            LIMIT ?
        """, (limit,))
        
        invoices = []
        for row in cursor.fetchall():
            invoices.append({
                'InvoiceID': row[0],
                'DateTime': row[1],
                'PaymentMethod': row[2],
                'TotalAmount': row[3],
                'ShiftEmployee': row[4]
            })
            
        return_connection(conn)
        return invoices
        
    except Exception as e:
        logger.error(f"Error getting recent invoices: {e}")
        return []
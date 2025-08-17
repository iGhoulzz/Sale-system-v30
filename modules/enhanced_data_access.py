"""
Enhanced data access module with pagination and background processing support.
Extends the core data_access functionality with performance optimizations.
"""

import sqlite3
import threading
import time
from typing import Optional, Callable, Any, List, Dict, Union, Tuple
from dataclasses import dataclass

from modules.db_manager import get_connection, return_connection, ConnectionContext
from modules.data_access import execute_transaction, log_db_operation
from modules.Login import current_user

@dataclass
class PagedResult:
    """Container for paginated query results with consistent attributes"""
    data: List[Dict]
    total_count: int  # Keep for backward compatibility
    current_page: int
    page_size: int
    has_next: bool
    has_prev: bool
    
    @property
    def total_items(self):
        """Alias for total_count for consistency"""
        return self.total_count
    
    @property
    def total_pages(self):
        """Calculate total pages"""
        if self.page_size <= 0:
            return 1
        return (self.total_count + self.page_size - 1) // self.page_size

class BackgroundTaskManager:
    """Manages background database operations to prevent UI freezing"""
    
    def __init__(self):
        self.active_tasks = {}
    
    def run_async(self, task_id: str, operation: Callable, 
                  on_success: Callable, on_error: Callable = None, 
                  *args, **kwargs):
        """
        Run database operation in background thread
        
        Args:
            task_id: Unique identifier for the task
            operation: Function to run in background
            on_success: Callback for successful completion (runs on main thread)
            on_error: Callback for error handling (runs on main thread)
            *args, **kwargs: Arguments to pass to the operation
            
        Returns:
            bool: True if task started, False if task with same ID is already running
        """
        
        def worker():
            try:
                result = operation(*args, **kwargs)
                # Schedule UI update on main thread
                if hasattr(on_success, '__self__'):  # Method with self
                    root = getattr(on_success.__self__, 'root', None)
                    if root:
                        root.after(0, lambda: on_success(result))
                    else:
                        on_success(result)
                else:
                    on_success(result)
            except Exception as e:
                if on_error:
                    if hasattr(on_error, '__self__'):
                        root = getattr(on_error.__self__, 'root', None)
                        if root:
                            root.after(0, lambda: on_error(str(e)))
                        else:
                            on_error(str(e))
                    else:
                        on_error(str(e))
            finally:
                self.active_tasks.pop(task_id, None)
        
        if task_id in self.active_tasks:
            return False  # Task already running
        
        thread = threading.Thread(target=worker, daemon=True)
        self.active_tasks[task_id] = thread
        thread.start()
        return True

class EnhancedDataAccess:
    """Enhanced data access with pagination and performance optimizations"""
    
    def __init__(self):
        self.task_manager = BackgroundTaskManager()
    
    def get_products_paged(self, page: int = 1, page_size: int = 100, 
                          category: str = None, search: str = None) -> PagedResult:
        """
        Get products with pagination
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            category: Optional category filter
            search: Optional search term for name or barcode
            
        Returns:
            PagedResult object with product data and pagination info
        """
        offset = (page - 1) * page_size
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if category:
            where_conditions.append("Category = ?")
            params.append(category)
        
        if search:
            where_conditions.append("(Name LIKE ? OR Barcode LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = f"WHERE {where_clause}"
        
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM Products {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated data
            data_query = f"""
            SELECT ProductID, Name, Category, Stock, SellingPrice as Price, Barcode 
            FROM Products 
            {where_clause}
            ORDER BY Name 
            LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            
            cursor.execute(data_query, params)
            products = cursor.fetchall()
            
            # Convert to dict for easier handling
            product_list = []
            for product in products:
                product_list.append({
                    'ProductID': product['ProductID'],
                    'Name': product['Name'],
                    'Category': product['Category'],
                    'Stock': product['Stock'],
                    'Price': product['Price'],
                    'Barcode': product['Barcode']
                })
        
        return PagedResult(
            data=product_list,
            total_count=total_count,
            current_page=page,
            page_size=page_size,
            has_next=offset + page_size < total_count,
            has_prev=page > 1
        )
    
    def get_invoices_paged(self, page: int = 1, page_size: int = 50, 
                          date_from: str = None, date_to: str = None, 
                          status: str = None) -> PagedResult:
        """
        Get invoices with pagination
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            date_from: Optional start date filter (YYYY-MM-DD)
            date_to: Optional end date filter (YYYY-MM-DD)
            status: Optional status filter
            
        Returns:
            PagedResult object with invoice data and pagination info
        """
        offset = (page - 1) * page_size
        
        where_conditions = []
        params = []
        
        if date_from:
            where_conditions.append("DATE(DateTime) >= ?")
            params.append(date_from)
        
        if date_to:
            where_conditions.append("DATE(DateTime) <= ?")
            params.append(date_to)
            
        if status:
            where_conditions.append("Status = ?")
            params.append(status)
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = f"WHERE {where_clause}"
        
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM Invoices {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated data
            data_query = f"""
            SELECT InvoiceID, DateTime, TotalAmount, PaymentMethod, 
                   ShiftEmployee, Discount
            FROM Invoices 
            {where_clause}
            ORDER BY DateTime DESC 
            LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            
            cursor.execute(data_query, params)
            invoices = cursor.fetchall()
            
            invoice_list = []
            for invoice in invoices:
                invoice_list.append({
                    'InvoiceID': invoice['InvoiceID'],
                    'DateTime': invoice['DateTime'],
                    'TotalAmount': invoice['TotalAmount'],
                    'PaymentMethod': invoice['PaymentMethod'],
                    'ShiftEmployee': invoice['ShiftEmployee'],
                    'Discount': invoice['Discount']
                })
        
        return PagedResult(
            data=invoice_list,
            total_count=total_count,
            current_page=page,            page_size=page_size,
            has_next=offset + page_size < total_count,
            has_prev=page > 1
        )
    
    def get_debits_paged(self, page: int = 1, page_size: int = 50,
                        name_filter: str = None, status_filter: str = None,
                        search_term: str = None, filter_paid: bool = None) -> PagedResult:
        """
        Get debits with pagination
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            name_filter: Optional customer name filter
            status_filter: Optional status filter ('Pending' or 'Paid')
            search_term: Optional search term for general search
            filter_paid: Optional boolean filter (True for paid, False for unpaid, None for all)
            
        Returns:
            PagedResult object with debit data and pagination info
        """
        offset = (page - 1) * page_size
        
        where_conditions = []
        params = []
        
        if name_filter:
            where_conditions.append("Name LIKE ?")
            params.append(f"%{name_filter}%")
        
        if status_filter:
            where_conditions.append("Status = ?")
            params.append(status_filter)
        
        if search_term:
            where_conditions.append("(Name LIKE ? OR Phone LIKE ? OR CAST(InvoiceID AS TEXT) LIKE ?)")
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if filter_paid is not None:
            if filter_paid:
                where_conditions.append("Status = 'Paid'")
            else:
                where_conditions.append("Status = 'Pending'")
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = f"WHERE {where_clause}"
        
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM Debits {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated data
            data_query = f"""
            SELECT DebitID, Name, Phone, InvoiceID, Amount, 
                   AmountPaid, Status, DateTime
            FROM Debits 
            {where_clause}
            ORDER BY DateTime DESC 
            LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            
            cursor.execute(data_query, params)
            debits = cursor.fetchall()
            
            debit_list = []
            for debit in debits:
                debit_list.append({
                    'DebitID': debit['DebitID'],
                    'CustomerName': debit['Name'],  # Use consistent naming
                    'Name': debit['Name'],
                    'Phone': debit['Phone'],
                    'InvoiceID': debit['InvoiceID'],
                    'Amount': debit['Amount'],
                    'AmountPaid': debit['AmountPaid'] or 0,
                    'Status': debit['Status'],
                    'Paid': debit['Status'] == 'Paid',  # Add boolean flag
                    'Date': debit['DateTime'],  # Add Date field for consistency
                    'DateTime': debit['DateTime'],
                    'Notes': ''  # Add empty notes field for consistency
                })
        
        return PagedResult(
            data=debit_list,
            total_count=total_count,
            current_page=page,
            page_size=page_size,
            has_next=offset + page_size < total_count,
            has_prev=page > 1
        )
    
    def search_products_fast(self, search_term: str, limit: int = 20) -> List[Dict]:
        """
        Fast product search optimized for autocomplete
        
        Args:
            search_term: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching products
        """
        if not search_term or len(search_term) < 2:
            return []
            
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT ProductID, Name, Barcode, Stock, SellingPrice as Price
            FROM Products 
            WHERE Name LIKE ? OR Barcode LIKE ? 
            ORDER BY 
                CASE 
                    WHEN Name LIKE ? THEN 1 
                    WHEN Name LIKE ? THEN 2 
                    ELSE 3 
                END,
                Name
            LIMIT ?
            """
            exact_match = f"{search_term}%"
            partial_match = f"%{search_term}%"
            
            cursor.execute(query, [
                partial_match, partial_match, 
                exact_match, partial_match, 
                limit
            ])
            
            results = cursor.fetchall()
            
            return [{
                'ProductID': r['ProductID'], 
                'Name': r['Name'], 
                'Barcode': r['Barcode'], 
                'Stock': r['Stock'], 
                'Price': r['Price']
            } for r in results]
    
    def run_in_background(self, task_id: str, operation: Callable, 
                         on_success: Callable, on_error: Callable = None,
                         *args, **kwargs) -> bool:
        """
        Run operation in background thread
        
        Args:
            task_id: Unique identifier for the task
            operation: Function to run in background
            on_success: Callback for successful completion
            on_error: Callback for error handling
            *args, **kwargs: Arguments to pass to the operation
            
        Returns:
            bool: True if task started, False if already running
        """
        return self.task_manager.run_async(
            task_id, operation, on_success, on_error, *args, **kwargs
        )
    
    def search_debits(self, search_term: str, limit: int = 20) -> PagedResult:
        """
        Fast debit search optimized for autocomplete
        
        Args:
            search_term: Text to search for
            limit: Maximum number of results
            
        Returns:
            PagedResult with matching debits
        """
        if not search_term or len(search_term.strip()) < 2:
            return PagedResult(data=[], total_count=0, current_page=1, page_size=limit, has_next=False, has_prev=False)
            
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT DebitID, Name, Phone, InvoiceID, Amount, 
                   AmountPaid, Status, DateTime
            FROM Debits 
            WHERE Name LIKE ? OR Phone LIKE ? OR CAST(InvoiceID AS TEXT) LIKE ?
            ORDER BY 
                CASE 
                    WHEN Name LIKE ? THEN 1 
                    WHEN Phone LIKE ? THEN 2 
                    ELSE 3 
                END,
                DateTime DESC
            LIMIT ?
            """
            exact_match = f"{search_term}%"
            partial_match = f"%{search_term}%"
            
            cursor.execute(query, [
                partial_match, partial_match, partial_match,
                exact_match, exact_match, 
                limit
            ])
            
            results = cursor.fetchall()
            
            debit_list = []
            for debit in results:
                debit_list.append({
                    'id': debit['DebitID'],
                    'customer_name': debit['Name'],
                    'phone': debit['Phone'],
                    'invoice_id': debit['InvoiceID'],
                    'amount': debit['Amount'],
                    'amount_paid': debit['AmountPaid'] or 0,
                    'paid': debit['Status'] == 'Paid',
                    'status': debit['Status'],
                    'date_time': debit['DateTime']
                })
            
            return PagedResult(
                data=debit_list,
                total_count=len(debit_list),
                current_page=1,
                page_size=limit,
                has_next=False,
                has_prev=False
            )
    
    def get_debit_statistics(self, on_success: Callable, on_error: Callable = None):
        """
        Get debit statistics in background
        
        Args:
            on_success: Callback for successful completion
            on_error: Callback for error handling
        """
        def get_stats():
            try:
                with ConnectionContext() as conn:
                    cursor = conn.cursor()
                    
                    # Get totals
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_count,
                            SUM(Amount) as total_amount,
                            SUM(CASE WHEN Status = 'Pending' THEN Amount ELSE 0 END) as pending_amount,
                            SUM(CASE WHEN Status = 'Paid' THEN Amount ELSE 0 END) as paid_amount
                        FROM Debits
                    """)
                    
                    result = cursor.fetchone()
                    return {
                        'total_debits': float(result['total_amount'] or 0),
                        'pending_debits': float(result['pending_amount'] or 0),
                        'paid_debits': float(result['paid_amount'] or 0),
                        'unpaid_debits': float(result['pending_amount'] or 0),
                        'total_count': int(result['total_count'] or 0)
                    }
            except Exception as e:
                raise e
        
        self.run_in_background(
            "get_debit_statistics",
            get_stats,
            on_success,
            on_error
        )
    
    def add_debit(self, debit_data: dict, on_success: Callable, on_error: Callable = None):
        """
        Add a new debit in background
        
        Args:
            debit_data: Dictionary with debit information
            on_success: Callback for successful completion
            on_error: Callback for error handling
        """
        def add_debit_impl():
            try:
                from modules.data_access import add_debit
                
                # Extract data
                customer_name = debit_data.get('CustomerName')
                phone = debit_data.get('Phone', '')  # Default to empty if not provided
                invoice_id = debit_data.get('InvoiceID', 0)  # Default to 0, will be generated
                amount = debit_data.get('Amount')
                notes = debit_data.get('Notes', '')
                
                # For new debits without invoice ID, we'll create a dummy one
                if not invoice_id:
                    # Generate a unique invoice ID based on timestamp
                    import time
                    invoice_id = int(time.time() * 1000) % 1000000  # Use last 6 digits of timestamp
                
                debit_id = add_debit(
                    name=customer_name,
                    phone=phone,
                    invoice_id=invoice_id,
                    amount=amount,
                    notes=notes
                )
                
                return {'success': True, 'debit_id': debit_id}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        self.run_in_background(
            "add_debit",
            add_debit_impl,
            on_success,
            on_error
        )
    
    def update_debit(self, debit_data: dict, on_success: Callable, on_error: Callable = None):
        """
        Update an existing debit in background
        
        Args:
            debit_data: Dictionary with debit information
            on_success: Callback for successful completion
            on_error: Callback for error handling
        """
        def update_debit_impl():
            try:
                with ConnectionContext() as conn:
                    cursor = conn.cursor()
                    
                    debit_id = debit_data.get('DebitID')
                    customer_name = debit_data.get('CustomerName')
                    amount = debit_data.get('Amount')
                    notes = debit_data.get('Notes', '')
                    paid = debit_data.get('Paid', False)
                    
                    # Update the debit
                    status = 'Paid' if paid else 'Pending'
                    cursor.execute("""
                        UPDATE Debits
                        SET Name = ?, Amount = ?, Status = ?, Notes = ?
                        WHERE DebitID = ?
                    """, (customer_name, amount, status, notes, debit_id))
                    
                    if cursor.rowcount == 0:
                        raise ValueError(f"Debit with ID {debit_id} not found")
                    
                    conn.commit()
                    return {'success': True}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        self.run_in_background(
            "update_debit",
            update_debit_impl,
            on_success,
            on_error
        )
    
    def delete_debit(self, debit_id: int, on_success: Callable, on_error: Callable = None):
        """
        Delete a debit in background
        
        Args:
            debit_id: ID of the debit to delete
            on_success: Callback for successful completion
            on_error: Callback for error handling
        """
        def delete_debit_impl():
            try:
                with ConnectionContext() as conn:
                    cursor = conn.cursor()
                    
                    # Check if debit exists
                    cursor.execute("SELECT COUNT(*) FROM Debits WHERE DebitID = ?", (debit_id,))
                    if cursor.fetchone()[0] == 0:
                        raise ValueError(f"Debit with ID {debit_id} not found")
                    
                    # Delete the debit
                    cursor.execute("DELETE FROM Debits WHERE DebitID = ?", (debit_id,))
                    
                    # Also delete related payments
                    cursor.execute("DELETE FROM Payments WHERE DebitID = ?", (debit_id,))
                    
                    conn.commit()
                    return {'success': True}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        self.run_in_background(
            "delete_debit",
            delete_debit_impl,
            on_success,
            on_error
        )
    
    def mark_debit_as_paid(self, debit_id: int, on_success: Callable, on_error: Callable = None):
        """
        Mark a debit as paid in background
        
        Args:
            debit_id: ID of the debit to mark as paid
            on_success: Callback for successful completion
            on_error: Callback for error handling
        """
        def mark_paid_impl():
            try:
                with ConnectionContext() as conn:
                    cursor = conn.cursor()
                    
                    # Get debit info
                    cursor.execute("SELECT Amount FROM Debits WHERE DebitID = ?", (debit_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        raise ValueError(f"Debit with ID {debit_id} not found")
                    
                    amount = result[0]
                    
                    # Update debit status and amount paid
                    cursor.execute("""
                        UPDATE Debits
                        SET Status = 'Paid', AmountPaid = Amount
                        WHERE DebitID = ?
                    """, (debit_id,))
                    
                    conn.commit()
                    return {'success': True}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        self.run_in_background(
            "mark_debit_as_paid",
            mark_paid_impl,
            on_success,
            on_error
        )

    def get_categories(self):
        """
        Get all product categories
        
        Returns:
            List of category dictionaries
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT Category FROM Products WHERE Category IS NOT NULL ORDER BY Category")
                categories = []
                for row in cursor.fetchall():
                    categories.append({
                        'name': row[0],
                        'id': row[0]  # Use name as ID for simplicity
                    })
                return categories
        except Exception as e:
            return []

    def search_products_fast(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Fast product search for autocomplete
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of product dictionaries
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                # Search in name and barcode
                cursor.execute("""
                    SELECT ProductID, Name, Price, Stock, Category, Barcode
                    FROM Products
                    WHERE Name LIKE ? OR Barcode LIKE ?
                    ORDER BY Name
                    LIMIT ?
                """, (f"%{search_term}%", f"%{search_term}%", limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'ProductID': row[0],
                        'Name': row[1],
                        'Price': row[2],
                        'Stock': row[3],
                        'Category': row[4],
                        'Barcode': row[5]
                    })
                
                return results
        except Exception as e:
            return []

    def search_product_by_barcode(self, barcode: str) -> Optional[Dict]:
        """
        Search for a product by barcode
        
        Args:
            barcode: Product barcode
            
        Returns:
            Product dictionary or None if not found
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ProductID, Name, Price, Stock, Category, Barcode
                    FROM Products
                    WHERE Barcode = ?
                """, (barcode,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'ProductID': row[0],
                        'Name': row[1],
                        'Price': row[2],
                        'Stock': row[3],
                        'Category': row[4],
                        'Barcode': row[5]
                    }
                return None
        except Exception as e:
            return None

    def get_recent_sales(self, limit: int = 50) -> List[Dict]:
        """
        Get recent sales/invoices
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of invoice dictionaries
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT i.InvoiceID, i.Date, i.TotalAmount,
                           COUNT(ii.InvoiceItemID) as ItemCount
                    FROM Invoices i
                    LEFT JOIN InvoiceItems ii ON i.InvoiceID = ii.InvoiceID
                    GROUP BY i.InvoiceID, i.Date, i.TotalAmount
                    ORDER BY i.Date DESC
                    LIMIT ?
                """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'InvoiceID': row[0],
                        'Date': row[1],
                        'TotalAmount': row[2],
                        'ItemCount': row[3]
                    })
                
                return results
        except Exception as e:
            return []

    def get_today_sales_summary(self) -> Dict:
        """
        Get today's sales summary
        
        Returns:
            Dictionary with sales statistics
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                # Get today's date
                today = time.strftime('%Y-%m-%d')
                
                # Get total sales and count
                cursor.execute("""
                    SELECT COUNT(*) as transaction_count, 
                           COALESCE(SUM(TotalAmount), 0) as total_sales
                    FROM Invoices
                    WHERE DATE(Date) = ?
                """, (today,))
                
                row = cursor.fetchone()
                transaction_count = row[0] if row else 0
                total_sales = row[1] if row else 0
                
                # Calculate average
                average_sale = total_sales / transaction_count if transaction_count > 0 else 0
                
                return {
                    'total_sales': total_sales,
                    'transaction_count': transaction_count,
                    'average_sale': average_sale
                }
        except Exception as e:
            return {
                'total_sales': 0,
                'transaction_count': 0,
                'average_sale': 0
            }

    def get_top_products(self, limit: int = 10) -> List[Dict]:
        """
        Get top selling products
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            List of product dictionaries with sales data
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.Name, 
                           COALESCE(SUM(ii.Quantity), 0) as TotalQuantity,
                           COALESCE(SUM(ii.Quantity * ii.Price), 0) as TotalRevenue
                    FROM Products p
                    LEFT JOIN InvoiceItems ii ON p.ProductID = ii.ProductID
                    GROUP BY p.ProductID, p.Name
                    ORDER BY TotalQuantity DESC
                    LIMIT ?
                """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'Name': row[0],
                        'TotalQuantity': row[1],
                        'TotalRevenue': row[2]
                    })
                
                return results
        except Exception as e:
            return []

    def save_quote(self, quote_data: Dict) -> Optional[int]:
        """
        Save a quote to the database
        
        Args:
            quote_data: Quote data dictionary
            
        Returns:
            Quote ID if successful, None otherwise
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                # Create quotes table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Quotes (
                        QuoteID INTEGER PRIMARY KEY AUTOINCREMENT,
                        TotalAmount REAL,
                        Date TEXT,
                        Items TEXT
                    )
                """)
                
                # Insert quote
                cursor.execute("""
                    INSERT INTO Quotes (TotalAmount, Date, Items)
                    VALUES (?, ?, ?)
                """, (quote_data['total'], quote_data['timestamp'], str(quote_data['items'])))
                
                quote_id = cursor.lastrowid
                conn.commit()
                
                return quote_id
        except Exception as e:
            return None

    def get_customers(self) -> List[Dict]:
        """
        Get all customers
        
        Returns:
            List of customer dictionaries
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                # Create customers table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Customers (
                        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        Phone TEXT,
                        Email TEXT,
                        Address TEXT
                    )
                """)
                
                cursor.execute("SELECT CustomerID, Name, Phone, Email, Address FROM Customers")
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'name': row[1],
                        'phone': row[2],
                        'email': row[3],
                        'address': row[4]
                    })
                
                return results
        except Exception as e:
            return []

    def create_debit_sale(self, customer_name: str, cart_items: Dict) -> Optional[int]:
        """
        Create a debit sale for a customer
        
        Args:
            customer_name: Name of the customer
            cart_items: Dictionary of cart items
            
        Returns:
            Debit ID if successful, None otherwise
        """
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                # Calculate total
                total = sum(item['price'] * item['quantity'] for item in cart_items.values())
                
                # Insert debit record
                cursor.execute("""
                    INSERT INTO Debits (CustomerName, Amount, Date, Status, AmountPaid)
                    VALUES (?, ?, ?, 'Unpaid', 0)
                """, (customer_name, total, time.strftime('%Y-%m-%d %H:%M:%S')))
                
                debit_id = cursor.lastrowid
                conn.commit()
                
                return debit_id
        except Exception as e:
            return None
    
    def add_category(self, category_name: str) -> bool:
        """Add a new product category"""
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Categories (Name) VALUES (?)", (category_name,))
                conn.commit()
                return True
        except Exception as e:
            log_db_operation(f'INSERT Categories Error: {str(e)}')
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Products WHERE ID = ?", (product_id,))
                conn.commit()
                return True
        except Exception as e:
            log_db_operation(f'DELETE Products Error: {str(e)}')
            return False
    
    def update_product(self, product_data: dict) -> bool:
        """Update an existing product"""
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Products 
                    SET Name = ?, Category = ?, Stock = ?, SellingPrice = ?, BuyingPrice = ?, Barcode = ?
                    WHERE ProductID = ?
                """, (
                    product_data.get('Name', product_data.get('name', '')),
                    product_data.get('Category', product_data.get('category', '')),
                    product_data.get('Stock', product_data.get('stock', 0)),
                    product_data.get('Price', product_data.get('sell_price', product_data.get('SellingPrice', 0))),
                    product_data.get('BuyPrice', product_data.get('buy_price', product_data.get('BuyingPrice', 0))),
                    product_data.get('Barcode', product_data.get('barcode', '')),
                    product_data.get('ID', product_data.get('id', product_data.get('ProductID', 0)))
                ))
                conn.commit()
                return True
        except Exception as e:
            log_db_operation(f'UPDATE Products Error: {str(e)}')
            return False
    
    def add_product(self, product_data: dict) -> bool:
        """Add a new product"""
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Products (Name, Category, Stock, SellingPrice, BuyingPrice, Barcode)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    product_data.get('Name', product_data.get('name', '')),
                    product_data.get('Category', product_data.get('category', '')),
                    product_data.get('Stock', product_data.get('stock', 0)),
                    product_data.get('Price', product_data.get('sell_price', product_data.get('SellingPrice', 0))),
                    product_data.get('BuyPrice', product_data.get('buy_price', product_data.get('BuyingPrice', 0))),
                    product_data.get('Barcode', product_data.get('barcode', ''))
                ))
                conn.commit()
                return True
        except Exception as e:
            log_db_operation(f'INSERT Products Error: {str(e)}')
            return False
    
    def update_product_stock(self, product_id: int, new_stock: int) -> bool:
        """Update product stock quantity"""
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE Products SET Stock = ? WHERE ProductID = ?", (new_stock, product_id))
                conn.commit()
                return True
        except Exception as e:
            log_db_operation(f'UPDATE Products Stock Error: {str(e)}')
            return False
    
    def get_products(self, limit: int = None) -> List[Dict]:
        """Get all products (compatibility method)"""
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                # Check if Categories table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Categories'")
                categories_table_exists = cursor.fetchone() is not None
                
                if categories_table_exists:
                    query = """
                    SELECT p.*, c.Name as CategoryName 
                    FROM Products p
                    LEFT JOIN Categories c ON p.CategoryID = c.ID
                    ORDER BY p.Name
                    """
                else:
                    # No Categories table, use Category field directly from Products
                    query = """
                    SELECT *, Category as CategoryName 
                    FROM Products 
                    ORDER BY Name
                    """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                raw_products = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Normalize column names for consistency
                normalized_products = []
                for product in raw_products:
                    normalized = {
                        'id': product.get('ProductID', product.get('ID', '')),
                        'name': product.get('Name', ''),
                        'sell_price': product.get('SellingPrice', 0),
                        'buy_price': product.get('BuyingPrice', 0),
                        'stock': product.get('Stock', 0),
                        'category': product.get('Category', product.get('CategoryName', '')),
                        'barcode': product.get('Barcode', ''),
                        'qr_code': product.get('QR_Code', '')
                    }
                    normalized_products.append(normalized)
                
                return normalized_products
        except Exception as e:
            log_db_operation(f'SELECT Products Error: {str(e)}')
            return []
    
    def search_products(self, search_term: str, limit: int = None) -> List[Dict]:
        """Search products by name, barcode, or category"""
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT p.*, c.Name as CategoryName 
                FROM Products p
                LEFT JOIN Categories c ON p.CategoryID = c.ID
                WHERE p.Name LIKE ? OR p.Barcode LIKE ? OR c.Name LIKE ?
                ORDER BY p.Name
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                search_pattern = f"%{search_term}%"
                cursor.execute(query, (search_pattern, search_pattern, search_pattern))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            log_db_operation(f'SELECT Products Search Error: {str(e)}')
            return []

# Create global instance
enhanced_data = EnhancedDataAccess()
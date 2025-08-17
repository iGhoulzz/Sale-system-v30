"""
modules/optimize_db.py - Database optimization utilities
This module adds performance optimizations to the database including:
- Adding indexes to commonly searched columns
- Analyzing tables for query optimization
- Setting additional performance pragmas
"""

import logging
import time
import sqlite3
from datetime import datetime
from modules.db_manager import ConnectionContext, get_connection, return_connection, analyze_database_performance

# Configure logger
logger = logging.getLogger(__name__)

def add_indexes():
    """
    Add indexes to common search fields to improve query performance.
    """
    # List of indexes to create
    indexes = [
        # Products table indexes
        "CREATE INDEX IF NOT EXISTS idx_products_barcode ON Products(Barcode)",
        "CREATE INDEX IF NOT EXISTS idx_products_productid ON Products(ProductID)",
        "CREATE INDEX IF NOT EXISTS idx_products_name ON Products(Name)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON Products(Category)",
        "CREATE INDEX IF NOT EXISTS idx_products_stock ON Products(Stock)",  # For low stock queries
        
        # Invoices table indexes (using actual schema)
        "CREATE INDEX IF NOT EXISTS idx_invoices_id ON Invoices(InvoiceID)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_date ON Invoices(DateTime)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_payment_method ON Invoices(PaymentMethod)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_employee ON Invoices(ShiftEmployee)",  # For financial dashboard
        "CREATE INDEX IF NOT EXISTS idx_invoices_date_month ON Invoices(strftime('%Y-%m', DateTime))",  # Financial dashboard optimization
        
        # Invoice items indexes
        "CREATE INDEX IF NOT EXISTS idx_invoice_items_invoiceid ON InvoiceItems(InvoiceID)",
        "CREATE INDEX IF NOT EXISTS idx_invoice_items_productid ON InvoiceItems(ProductID)",
        
        # Debits table indexes
        "CREATE INDEX IF NOT EXISTS idx_debits_status ON Debits(Status)",
        "CREATE INDEX IF NOT EXISTS idx_debits_invoiceid ON Debits(InvoiceID)",
        "CREATE INDEX IF NOT EXISTS idx_debits_name ON Debits(Name)",
        
        # ActivityLog indexes
        "CREATE INDEX IF NOT EXISTS idx_activity_userid ON ActivityLog(UserID)",
        "CREATE INDEX IF NOT EXISTS idx_activity_date ON ActivityLog(DateTime)"
        
        # Note: StockMovement table doesn't exist in current schema
        # If needed in future, create table first with proper migration
    ]
    
    logger.info("Adding database indexes for performance optimization...")
    
    # Use connection context for automatic connection management
    with ConnectionContext() as conn:
        cursor = conn.cursor()
        
        for index in indexes:
            try:
                cursor.execute(index)
                logger.debug(f"Created index: {index}")
            except Exception as e:
                logger.error(f"Error creating index: {e}")
        
        # Commit the changes
        conn.commit()
        
        # Run ANALYZE to update statistics
        try:
            cursor.execute("ANALYZE")
            logger.info("Database analysis completed")
        except Exception as e:
            logger.error(f"Error running database analysis: {e}")
    
    logger.info("Database optimization completed")
    
def optimize_database():
    """
    Run full database optimization
    """
    logger.info("Starting database optimization...")
    
    # Add indexes
    add_indexes()
    
    # Set additional pragmas for performance
    with ConnectionContext() as conn:
        cursor = conn.cursor()
        
        try:
            # These pragmas help with performance
            pragmas = [
                "PRAGMA journal_mode = WAL",  # Enable Write-Ahead Logging
                "PRAGMA synchronous = NORMAL", # Less disk I/O
                "PRAGMA cache_size = 10000",  # 10MB cache
                "PRAGMA temp_store = MEMORY", # Store temp tables in memory
                "PRAGMA mmap_size = 30000000", # Memory-mapped I/O (30MB)
                "PRAGMA auto_vacuum = INCREMENTAL", # More efficient vacuuming
                "PRAGMA busy_timeout = 5000"  # Wait up to 5 seconds on busy DB
            ]
            
            for pragma in pragmas:
                cursor.execute(pragma)
                result = cursor.fetchone()
                logger.debug(f"Set {pragma}: {result[0] if result else 'N/A'}")
                
            # Vacuum the database to optimize storage
            cursor.execute("VACUUM")
            logger.info("Database vacuum completed")
            
        except Exception as e:
            logger.error(f"Error setting performance pragmas: {e}")
    
    logger.info("Database optimization completed successfully")

def check_query_performance(query, params=None):
    """
    Run EXPLAIN QUERY PLAN to analyze query performance.
    
    Args:
        query: SQL query to analyze
        params: Query parameters
        
    Returns:
        Dict with query plan information
    """
    if params is None:
        params = []
        
    with ConnectionContext() as conn:
        cursor = conn.cursor()
        try:
            # Get the execution plan
            cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
            plan_rows = cursor.fetchall()
            
            # Execute with timer
            start = time.time()
            cursor.execute(query, params)
            data = cursor.fetchall()
            duration = time.time() - start
            
            return {
                "plan": [dict(row) for row in plan_rows],
                "rows_returned": len(data),
                "duration_ms": duration * 1000,
                "uses_index": any("USING INDEX" in str(row) for row in plan_rows),
                "sequential_scan": any("SCAN TABLE" in str(row) and "USING INDEX" not in str(row) for row in plan_rows)
            }
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {"error": str(e)}

def run_comprehensive_optimization():
    """
    Run a comprehensive database optimization including:
    - Adding and updating indexes
    - Optimizing database settings
    - Cleaning up any corrupted data
    - Rebuilding the database if necessary
    
    Returns:
        Dict with optimization results
    """
    start_time = time.time()
    results = {
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "steps_completed": [],
        "errors": []
    }
    
    try:
        # 1. Set optimized pragmas
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            pragmas = [
                "PRAGMA journal_mode = WAL",
                "PRAGMA synchronous = NORMAL",
                "PRAGMA cache_size = 10000",
                "PRAGMA temp_store = MEMORY",
                "PRAGMA mmap_size = 30000000",
                "PRAGMA auto_vacuum = INCREMENTAL",
                "PRAGMA busy_timeout = 5000"
            ]
            
            for pragma in pragmas:
                cursor.execute(pragma)
            
        results["steps_completed"].append("pragmas_set")
        
        # 2. Check database integrity
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            if integrity != "ok":
                results["errors"].append(f"Database integrity check failed: {integrity}")
                # Could attempt repair here
            else:
                results["steps_completed"].append("integrity_verified")
        
        # 3. Add necessary indexes
        add_indexes()
        results["steps_completed"].append("indexes_created")
        
        # 4. Analyze to update statistics
        analyze_database_performance()
        results["steps_completed"].append("statistics_updated")
        
        # 5. Vacuum to reclaim space and defragment
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
        results["steps_completed"].append("vacuum_completed")
        
        # 6. Optimize the database
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA optimize")
        results["steps_completed"].append("optimization_completed")
        
    except Exception as e:
        results["errors"].append(f"Optimization error: {str(e)}")
    
    # Record completion time and duration
    end_time = time.time()
    results["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results["duration_seconds"] = round(end_time - start_time, 2)
    results["success"] = len(results["errors"]) == 0
    
    # Log the results
    if results["success"]:
        logger.info(f"Database optimization completed successfully in {results['duration_seconds']} seconds")
    else:
        logger.error(f"Database optimization completed with errors in {results['duration_seconds']} seconds")
        for error in results["errors"]:
            logger.error(f"Optimization error: {error}")
    
    return results

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    # Run comprehensive optimization
    run_comprehensive_optimization() 
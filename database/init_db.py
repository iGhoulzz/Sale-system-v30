#!/usr/bin/env python3
"""
Database Initialization Script for Sales Management System
=========================================================

This script creates all required database tables and indexes for the sales
management system. It ensures consistent schema across all environments.

Created by: Senior Software Engineer
Date: 2025-08-17
"""

import sqlite3
import os
import logging
import sys
from typing import Optional

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db_manager import get_connection, return_connection, ConnectionContext

logger = logging.getLogger(__name__)

def create_database() -> bool:
    """
    Create all database tables and initial data for the sales management system.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting database initialization...")
        
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create all tables
            _create_users_table(cursor)
            _create_products_table(cursor)
            _create_invoices_table(cursor)
            _create_invoice_items_table(cursor)
            _create_debits_table(cursor)
            _create_activity_log_table(cursor)
            _create_product_losses_table(cursor)
            _create_customers_table(cursor)
            _create_quotes_table(cursor)
            _create_payments_table(cursor)
            _create_categories_table(cursor)
            
            # Create indexes for performance
            _create_indexes(cursor)
            
            # Insert initial data
            _insert_initial_data(cursor)
            
            # Commit all changes
            conn.commit()
            
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False

def _create_users_table(cursor):
    """Create Users table for authentication"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT UNIQUE NOT NULL,
            Password TEXT NOT NULL,
            Role TEXT NOT NULL DEFAULT 'user',
            Created TEXT DEFAULT CURRENT_TIMESTAMP,
            LastLogin TEXT,
            IsActive INTEGER DEFAULT 1
        )
    """)
    logger.info("Created Users table")

def _create_products_table(cursor):
    """Create Products table for inventory management"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Products (
            ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            BuyingPrice REAL NOT NULL DEFAULT 0.0,
            SellingPrice REAL NOT NULL DEFAULT 0.0,
            Stock INTEGER NOT NULL DEFAULT 0,
            Category TEXT,
            Barcode TEXT UNIQUE,
            Created TEXT DEFAULT CURRENT_TIMESTAMP,
            LastModified TEXT DEFAULT CURRENT_TIMESTAMP,
            IsActive INTEGER DEFAULT 1
        )
    """)
    logger.info("Created Products table")

def _create_invoices_table(cursor):
    """Create Invoices table for sales records"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Invoices (
            InvoiceID INTEGER PRIMARY KEY AUTOINCREMENT,
            DateTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PaymentMethod TEXT NOT NULL DEFAULT 'cash',
            TotalAmount REAL NOT NULL DEFAULT 0.0,
            Discount REAL DEFAULT 0.0,
            ShiftEmployee TEXT,
            CustomerName TEXT,
            CustomerPhone TEXT,
            Notes TEXT,
            Status TEXT DEFAULT 'completed'
        )
    """)
    logger.info("Created Invoices table")

def _create_invoice_items_table(cursor):
    """Create InvoiceItems table for detailed sales items"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS InvoiceItems (
            ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
            InvoiceID INTEGER NOT NULL,
            ProductID INTEGER NOT NULL,
            ProductName TEXT NOT NULL,
            Quantity INTEGER NOT NULL,
            UnitPrice REAL NOT NULL,
            Subtotal REAL NOT NULL,
            FOREIGN KEY (InvoiceID) REFERENCES Invoices(InvoiceID) ON DELETE CASCADE,
            FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
        )
    """)
    logger.info("Created InvoiceItems table")

def _create_debits_table(cursor):
    """Create Debits table for credit sales tracking"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Debits (
            DebitID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Phone TEXT,
            InvoiceID INTEGER,
            Amount REAL NOT NULL,
            Status TEXT DEFAULT 'unpaid',
            DateTime TEXT DEFAULT CURRENT_TIMESTAMP,
            Notes TEXT,
            DueDate TEXT,
            PaidDate TEXT,
            FOREIGN KEY (InvoiceID) REFERENCES Invoices(InvoiceID)
        )
    """)
    logger.info("Created Debits table")

def _create_activity_log_table(cursor):
    """Create ActivityLog table for audit trail"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ActivityLog (
            LogID INTEGER PRIMARY KEY AUTOINCREMENT,
            DateTime TEXT DEFAULT CURRENT_TIMESTAMP,
            UserID INTEGER,
            Action TEXT NOT NULL,
            TableName TEXT,
            RecordID INTEGER,
            OldValues TEXT,
            NewValues TEXT,
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        )
    """)
    logger.info("Created ActivityLog table")

def _create_product_losses_table(cursor):
    """Create ProductLosses table for inventory loss tracking"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ProductLosses (
            LossID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProductID INTEGER NOT NULL,
            Quantity INTEGER NOT NULL,
            Reason TEXT,
            DateTime TEXT DEFAULT CURRENT_TIMESTAMP,
            RecordedBy INTEGER,
            FOREIGN KEY (ProductID) REFERENCES Products(ProductID),
            FOREIGN KEY (RecordedBy) REFERENCES Users(UserID)
        )
    """)
    logger.info("Created ProductLosses table")

def _create_customers_table(cursor):
    """Create Customers table for customer management"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Customers (
            CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Phone TEXT,
            Email TEXT,
            Address TEXT,
            Created TEXT DEFAULT CURRENT_TIMESTAMP,
            IsActive INTEGER DEFAULT 1
        )
    """)
    logger.info("Created Customers table")

def _create_quotes_table(cursor):
    """Create Quotes table for quotation management"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Quotes (
            QuoteID INTEGER PRIMARY KEY AUTOINCREMENT,
            TotalAmount REAL NOT NULL,
            Date TEXT DEFAULT CURRENT_TIMESTAMP,
            Items TEXT,
            CustomerName TEXT,
            Status TEXT DEFAULT 'pending'
        )
    """)
    logger.info("Created Quotes table")

def _create_payments_table(cursor):
    """Create Payments table for payment tracking"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Payments (
            PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
            DebitID INTEGER,
            InvoiceID INTEGER,
            Amount REAL NOT NULL,
            PaymentMethod TEXT DEFAULT 'cash',
            DateTime TEXT DEFAULT CURRENT_TIMESTAMP,
            Notes TEXT,
            FOREIGN KEY (DebitID) REFERENCES Debits(DebitID),
            FOREIGN KEY (InvoiceID) REFERENCES Invoices(InvoiceID)
        )
    """)
    logger.info("Created Payments table")

def _create_categories_table(cursor):
    """Create Categories table for product categorization"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT UNIQUE NOT NULL,
            Description TEXT,
            IsActive INTEGER DEFAULT 1
        )
    """)
    logger.info("Created Categories table")

def _create_indexes(cursor):
    """Create database indexes for improved performance"""
    indexes = [
        # Products indexes
        "CREATE INDEX IF NOT EXISTS idx_products_name ON Products(Name)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON Products(Category)",
        "CREATE INDEX IF NOT EXISTS idx_products_barcode ON Products(Barcode)",
        "CREATE INDEX IF NOT EXISTS idx_products_active ON Products(IsActive)",
        
        # Invoices indexes
        "CREATE INDEX IF NOT EXISTS idx_invoices_datetime ON Invoices(DateTime)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_payment_method ON Invoices(PaymentMethod)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_customer ON Invoices(CustomerName)",
        
        # InvoiceItems indexes
        "CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON InvoiceItems(InvoiceID)",
        "CREATE INDEX IF NOT EXISTS idx_invoice_items_product ON InvoiceItems(ProductID)",
        
        # Debits indexes
        "CREATE INDEX IF NOT EXISTS idx_debits_name ON Debits(Name)",
        "CREATE INDEX IF NOT EXISTS idx_debits_status ON Debits(Status)",
        "CREATE INDEX IF NOT EXISTS idx_debits_datetime ON Debits(DateTime)",
        "CREATE INDEX IF NOT EXISTS idx_debits_invoice ON Debits(InvoiceID)",
        
        # ActivityLog indexes
        "CREATE INDEX IF NOT EXISTS idx_activity_log_datetime ON ActivityLog(DateTime)",
        "CREATE INDEX IF NOT EXISTS idx_activity_log_user ON ActivityLog(UserID)",
        "CREATE INDEX IF NOT EXISTS idx_activity_log_action ON ActivityLog(Action)",
        
        # Users indexes
        "CREATE INDEX IF NOT EXISTS idx_users_username ON Users(Username)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON Users(Role)",
        
        # Customers indexes
        "CREATE INDEX IF NOT EXISTS idx_customers_name ON Customers(Name)",
        "CREATE INDEX IF NOT EXISTS idx_customers_phone ON Customers(Phone)"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    logger.info("Created database indexes")

def _insert_initial_data(cursor):
    """Insert initial data required for the system to function"""
    
    # Insert default admin user if not exists
    cursor.execute("SELECT COUNT(*) FROM Users WHERE Username = 'admin'")
    if cursor.fetchone()[0] == 0:
        # Use a simple password for demo - in production, this should be hashed
        import bcrypt
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO Users (Username, Password, Role)
            VALUES (?, ?, 'admin')
        """, ('admin', password_hash))
        logger.info("Created default admin user")
    
    # Insert sample user if not exists
    cursor.execute("SELECT COUNT(*) FROM Users WHERE Username = 'user'")
    if cursor.fetchone()[0] == 0:
        import bcrypt
        password_hash = bcrypt.hashpw('user123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO Users (Username, Password, Role)
            VALUES (?, ?, 'user')
        """, ('user', password_hash))
        logger.info("Created default user account")
    
    # Insert default categories
    default_categories = [
        'Electronics', 'Clothing', 'Food & Beverages', 'Books', 
        'Home & Garden', 'Sports & Outdoors', 'Health & Beauty', 'Other'
    ]
    
    for category in default_categories:
        cursor.execute("SELECT COUNT(*) FROM Categories WHERE Name = ?", (category,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Categories (Name) VALUES (?)", (category,))
    
    logger.info("Inserted default categories")
    
    # Insert sample products for testing
    sample_products = [
        ('Sample Product 1', 10.0, 15.0, 100, 'Electronics', '1234567890123'),
        ('Sample Product 2', 5.0, 8.0, 50, 'Clothing', '1234567890124'),
        ('Sample Product 3', 20.0, 30.0, 25, 'Food & Beverages', '1234567890125'),
    ]
    
    for product in sample_products:
        cursor.execute("SELECT COUNT(*) FROM Products WHERE Name = ?", (product[0],))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO Products (Name, BuyingPrice, SellingPrice, Stock, Category, Barcode)
                VALUES (?, ?, ?, ?, ?, ?)
            """, product)
    
    logger.info("Inserted sample products")

def check_database_integrity() -> bool:
    """
    Check database integrity and report any issues.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Check table existence
            required_tables = [
                'Users', 'Products', 'Invoices', 'InvoiceItems', 'Debits',
                'ActivityLog', 'ProductLosses', 'Customers', 'Quotes', 'Payments', 'Categories'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.error(f"Missing tables: {missing_tables}")
                return False
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result != 'ok':
                logger.error(f"Database integrity check failed: {integrity_result}")
                return False
            
            logger.info("Database integrity check passed")
            return True
            
    except Exception as e:
        logger.error(f"Database integrity check error: {str(e)}")
        return False

def repair_database() -> bool:
    """
    Attempt to repair database issues by recreating missing tables.
    
    Returns:
        bool: True if repair successful, False otherwise
    """
    try:
        logger.info("Attempting database repair...")
        return create_database()
    except Exception as e:
        logger.error(f"Database repair failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Direct execution for testing
    import sys
    
    print("🚀 Sales Management System - Database Initialization")
    print("=" * 60)
    
    success = create_database()
    
    if success:
        print("✅ Database initialization completed successfully!")
        
        # Run integrity check
        if check_database_integrity():
            print("✅ Database integrity verified!")
        else:
            print("❌ Database integrity check failed!")
            sys.exit(1)
    else:
        print("❌ Database initialization failed!")
        sys.exit(1)
    
    print("\n📊 Database Statistics:")
    try:
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Show table counts
            tables = ['Users', 'Products', 'Categories', 'Invoices', 'Debits']
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table}: {count} records")
                except:
                    print(f"  {table}: Error counting records")
                    
    except Exception as e:
        print(f"Error getting statistics: {e}")
    
    print("\n🎉 Database is ready for use!")
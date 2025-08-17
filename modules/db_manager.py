# db_manager.py
import sqlite3
import os
import queue
import threading
import time
import sys
import codecs
from typing import Optional
import logging

# Configure logger
logger = logging.getLogger(__name__)

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

# Define base directory and ensure a "database" directory exists
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

# Set the full database path
DB_PATH = os.path.join(DATABASE_DIR, "store.db")

# Thread-local storage for connections
_thread_local = threading.local()

# Connection pool size and timeout
POOL_SIZE = 15  # Increased from 10 to handle more concurrent operations
CONNECTION_TIMEOUT = 8  # Increased from 5 seconds to allow for complex queries
_connection_pool = None
_pool_lock = threading.RLock()
_connection_stats = {"created": 0, "returned": 0, "active": 0, "peak": 0}  # Track connection stats

class ConnectionPool:
    """
    A simple connection pool for SQLite connections.
    
    This pool maintains a set of pre-initialized connections
    that can be borrowed and returned, improving performance
    by avoiding the overhead of repeatedly creating connections.
    """
    def __init__(self, db_path: str, pool_size: int = POOL_SIZE, timeout: int = CONNECTION_TIMEOUT):
        """
        Initialize the connection pool.
        
        Args:
            db_path: Path to the SQLite database
            pool_size: Maximum number of connections to keep in the pool
            timeout: Timeout in seconds for getting a connection
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.connections = queue.Queue(maxsize=pool_size)
        self._active_connections = 0
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Create initial connections in the pool."""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            if conn:
                self.connections.put(conn)
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new SQLite connection with proper settings."""
        try:
            # Enable foreign keys and set other pragmas
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA cache_size = 10000")  # 10MB cache
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
            conn.execute("PRAGMA busy_timeout = 5000")  # Wait up to 5 seconds on busy DB
            
            # Enable row factory for named access
            conn.row_factory = sqlite3.Row
            
            # Update stats
            global _connection_stats
            _connection_stats["created"] += 1
            
            return conn
        except Exception as e:
            logger.error(f"Error creating database connection: {str(e)}")
            return None
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """
        Get a connection from the pool or wait if none are available.
        
        Returns:
            An SQLite connection
            
        Raises:
            ConnectionError: If unable to get a connection after waiting
        """
        try:
            # Try to get a connection from pool with timeout
            conn = self.connections.get(timeout=self.timeout)
            
            # Update stats
            global _connection_stats
            _connection_stats["active"] += 1
            if _connection_stats["active"] > _connection_stats["peak"]:
                _connection_stats["peak"] = _connection_stats["active"]
            
            # Test if connection is still valid
            try:
                conn.execute("SELECT 1").fetchone()
                return conn
            except sqlite3.Error:
                # Connection is stale, create a new one
                conn = self._create_connection()
                if conn is None:
                    raise ConnectionError("Failed to create a new database connection")
                return conn
                
        except queue.Empty:
            # Pool is empty, wait for a connection rather than creating a new one
            logger.warning("Connection pool exhausted, waiting for a connection to be returned")
            try:
                # Try again with a longer timeout
                conn = self.connections.get(timeout=self.timeout * 2)
                
                # Update stats
                _connection_stats["active"] += 1
                if _connection_stats["active"] > _connection_stats["peak"]:
                    _connection_stats["peak"] = _connection_stats["active"]
                    
                return conn
            except queue.Empty:
                # If still no connection available, raise error
                logger.error("Could not get a database connection after extended wait")
                raise ConnectionError("Connection pool exhausted and timed out waiting for a connection")
        except Exception as e:
            logger.error(f"Error getting connection from pool: {str(e)}")
            raise ConnectionError(f"Error getting connection from pool: {str(e)}")
    
    def return_connection(self, conn: sqlite3.Connection):
        """
        Return a connection to the pool.
        
        Args:
            conn: The connection to return
        """
        if conn is None:
            return
            
        try:
            # Reset connection to clean state (rollback any transactions)
            conn.rollback()
            
            # Update stats
            global _connection_stats
            _connection_stats["active"] -= 1
            _connection_stats["returned"] += 1
            
            # If pool is full, close this connection
            if self.connections.full():
                conn.close()
            else:
                self.connections.put(conn)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {str(e)}")
            try:
                conn.close()
            except:
                pass
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.close()
            except:
                pass

def initialize_connection_pool():
    """Initialize the global connection pool."""
    global _connection_pool
    with _pool_lock:
        if _connection_pool is None:
            _connection_pool = ConnectionPool(DB_PATH)

def get_connection() -> sqlite3.Connection:
    """
    Get a database connection, preferably from the connection pool.
    
    Returns:
        A SQLite connection
        
    Raises:
        ConnectionError: If unable to get a connection from the pool
    """
    # Initialize pool if not already done
    if _connection_pool is None:
        initialize_connection_pool()
    
    # If we're in a transaction-managed context (using connection context manager),
    # return the existing connection for this thread
    if hasattr(_thread_local, 'connection'):
        return _thread_local.connection
        
    # Otherwise get a connection from the pool
    # This will now raise ConnectionError if no connections are available
    return _connection_pool.get_connection()

def return_connection(conn: sqlite3.Connection):
    """Return a connection to the pool."""
    if _connection_pool and conn:
        _connection_pool.return_connection(conn)

# Simple ConnectionContext if the full implementation doesn't exist
if 'ConnectionContext' not in globals():
    class ConnectionContext:
        """
        A simple context manager for database connections.
        
        Ensures connections are properly committed/rolled back and closed.
        """
        def __enter__(self):
            self.conn = get_connection()
            return self.conn
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            return_connection(self.conn)
            return False  # Don't suppress exceptions

def shutdown_pool():
    """Shut down the connection pool."""
    global _connection_pool
    with _pool_lock:
        if _connection_pool:
            _connection_pool.close_all()
            _connection_pool = None

def get_connection_stats():
    """
    Get statistics about database connections.
    
    Returns:
        Dictionary with connection statistics
    """
    global _connection_stats
    return {
        "created": _connection_stats["created"],
        "returned": _connection_stats["returned"],
        "active": _connection_stats["active"],
        "peak": _connection_stats["peak"],
        "pool_size": POOL_SIZE,
        "timeout": CONNECTION_TIMEOUT
    }

def reset_connection_stats():
    """Reset the connection statistics counters."""
    global _connection_stats
    _connection_stats = {"created": 0, "returned": 0, "active": 0, "peak": 0}

def analyze_database_performance():
    """
    Run ANALYZE on the database to update query statistics.
    This helps the SQLite query planner make better decisions.
    """
    try:
        with ConnectionContext() as conn:
            conn.execute("ANALYZE")
            conn.execute("PRAGMA optimize")
            logger.info("Database analysis completed")
    except Exception as e:
        logger.error(f"Failed to analyze database: {str(e)}")
        
    return True

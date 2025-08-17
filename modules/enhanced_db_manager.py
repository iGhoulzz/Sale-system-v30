"""
Enhanced Database Manager with Advanced Features
This module provides enhanced database management with connection pooling,
query caching, performance monitoring, and optimization tools.

Created: July 17, 2025
"""

import sqlite3
import threading
import time
import queue
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from modules.logger import logger
from modules.db_manager import DB_PATH

@dataclass
class ConnectionStats:
    """Database connection statistics"""
    total_connections: int = 0
    active_connections: int = 0
    peak_connections: int = 0
    connections_created: int = 0
    connections_closed: int = 0
    average_connection_time: float = 0.0
    connection_errors: int = 0

@dataclass
class QueryStats:
    """Query execution statistics"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    average_execution_time: float = 0.0
    total_execution_time: float = 0.0
    slow_queries: int = 0
    cached_queries: int = 0
    cache_hit_rate: float = 0.0

class ConnectionPool:
    """Advanced connection pool with monitoring and optimization"""
    
    def __init__(self, database_path: str, pool_size: int = 10, 
                 max_connections: int = 20, timeout: int = 30):
        self.database_path = database_path
        self.pool_size = pool_size
        self.max_connections = max_connections
        self.timeout = timeout
        
        # Connection pool
        self.pool = queue.Queue(maxsize=pool_size)
        self.active_connections = set()
        self.connection_count = 0
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = ConnectionStats()
        self.connection_times = []
        
        # Initialize pool
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            for _ in range(self.pool_size):
                conn = self._create_connection()
                if conn:
                    self.pool.put(conn)
                    
            logger.info(f"Connection pool initialized with {self.pool.qsize()} connections")
            
        except Exception as e:
            logger.error(f"Error initializing connection pool: {e}")
            raise
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection"""
        try:
            start_time = time.time()
            
            conn = sqlite3.connect(
                self.database_path,
                timeout=self.timeout,
                check_same_thread=False
            )
            
            # Configure connection
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            
            # Update statistics
            connection_time = time.time() - start_time
            self.connection_times.append(connection_time)
            
            with self.lock:
                self.connection_count += 1
                self.stats.connections_created += 1
                self.stats.total_connections += 1
                
                if self.stats.total_connections > self.stats.peak_connections:
                    self.stats.peak_connections = self.stats.total_connections
                    
                # Update average connection time
                self.stats.average_connection_time = sum(self.connection_times) / len(self.connection_times)
            
            return conn
            
        except Exception as e:
            logger.error(f"Error creating database connection: {e}")
            with self.lock:
                self.stats.connection_errors += 1
            return None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            # Try to get connection from pool
            try:
                conn = self.pool.get(timeout=5)
            except queue.Empty:
                # Pool empty, create new connection if under limit
                if self.connection_count < self.max_connections:
                    conn = self._create_connection()
                else:
                    raise Exception("Connection pool exhausted")
            
            if conn is None:
                raise Exception("Failed to get database connection")
            
            # Add to active connections
            with self.lock:
                self.active_connections.add(conn)
                self.stats.active_connections = len(self.active_connections)
            
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                # Return connection to pool
                with self.lock:
                    self.active_connections.discard(conn)
                    self.stats.active_connections = len(self.active_connections)
                
                try:
                    # Check if connection is still valid
                    conn.execute("SELECT 1")
                    self.pool.put(conn, timeout=1)
                except (sqlite3.Error, queue.Full):
                    # Connection invalid or pool full, close it
                    self._close_connection(conn)
    
    def _close_connection(self, conn: sqlite3.Connection):
        """Close a database connection"""
        try:
            conn.close()
            with self.lock:
                self.connection_count -= 1
                self.stats.connections_closed += 1
                self.stats.total_connections -= 1
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
    
    def get_stats(self) -> ConnectionStats:
        """Get connection pool statistics"""
        return self.stats
    
    def optimize_pool(self):
        """Optimize the connection pool"""
        try:
            # Close excess connections
            while self.pool.qsize() > self.pool_size:
                try:
                    conn = self.pool.get_nowait()
                    self._close_connection(conn)
                except queue.Empty:
                    break
            
            # Add connections if needed
            while self.pool.qsize() < self.pool_size and self.connection_count < self.max_connections:
                conn = self._create_connection()
                if conn:
                    self.pool.put(conn)
                else:
                    break
            
            logger.info(f"Connection pool optimized: {self.pool.qsize()} connections available")
            
        except Exception as e:
            logger.error(f"Error optimizing connection pool: {e}")
    
    def shutdown(self):
        """Shutdown the connection pool"""
        try:
            # Close all connections in pool
            while not self.pool.empty():
                try:
                    conn = self.pool.get_nowait()
                    self._close_connection(conn)
                except queue.Empty:
                    break
            
            # Close active connections
            for conn in list(self.active_connections):
                self._close_connection(conn)
            
            logger.info("Connection pool shutdown complete")
            
        except Exception as e:
            logger.error(f"Error shutting down connection pool: {e}")

class QueryCache:
    """Intelligent query result caching system"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.cache = {}
        self.access_times = {}
        self.lock = threading.RLock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
    def _generate_key(self, query: str, params: Tuple) -> str:
        """Generate cache key from query and parameters"""
        return f"{hash(query)}_{hash(params) if params else 'none'}"
    
    def get(self, query: str, params: Tuple = None) -> Optional[Any]:
        """Get cached query result"""
        key = self._generate_key(query, params)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                current_time = time.time()
                
                # Check if entry is expired
                if current_time - entry['timestamp'] > self.ttl:
                    del self.cache[key]
                    del self.access_times[key]
                    self.misses += 1
                    return None
                
                # Update access time
                self.access_times[key] = current_time
                self.hits += 1
                return entry['result']
            
            self.misses += 1
            return None
    
    def put(self, query: str, params: Tuple, result: Any):
        """Cache query result"""
        key = self._generate_key(query, params)
        current_time = time.time()
        
        with self.lock:
            # Check if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            self.cache[key] = {
                'result': result,
                'timestamp': current_time
            }
            self.access_times[key] = current_time
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return
        
        # Find LRU entry
        lru_key = min(self.access_times, key=self.access_times.get)
        
        # Remove from cache
        del self.cache[lru_key]
        del self.access_times[lru_key]
        self.evictions += 1
    
    def clear(self):
        """Clear all cached entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'evictions': self.evictions,
                'ttl': self.ttl
            }

class EnhancedDatabaseManager:
    """Enhanced database manager with advanced features"""
    
    def __init__(self, database_path: str = None, 
                 pool_size: int = 10, cache_size: int = 1000):
        self.database_path = database_path or DB_PATH
        
        # Initialize components
        self.connection_pool = ConnectionPool(database_path, pool_size)
        self.query_cache = QueryCache(cache_size)
        
        # Query statistics
        self.query_stats = QueryStats()
        self.slow_queries = []
        self.query_times = []
        
        # Performance monitoring
        self.performance_threshold = 1.0  # 1 second
        self.monitoring_enabled = True
        
        # Background optimization
        self._start_background_optimization()
    
    def execute_query(self, query: str, params: Tuple = None, 
                     use_cache: bool = True) -> List[sqlite3.Row]:
        """Execute query with caching and performance monitoring"""
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cached_result = self.query_cache.get(query, params)
            if cached_result is not None:
                self.query_stats.cached_queries += 1
                return cached_result
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                result = cursor.fetchall()
                
                # Cache result
                if use_cache:
                    self.query_cache.put(query, params, result)
                
                # Update statistics
                execution_time = time.time() - start_time
                self._update_query_stats(query, execution_time, True)
                
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats(query, execution_time, False)
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_write_query(self, query: str, params: Tuple = None) -> int:
        """Execute write query (INSERT, UPDATE, DELETE)"""
        start_time = time.time()
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                
                # Clear related cache entries
                self._invalidate_cache(query)
                
                # Update statistics
                execution_time = time.time() - start_time
                self._update_query_stats(query, execution_time, True)
                
                return cursor.rowcount
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats(query, execution_time, False)
            logger.error(f"Write query execution error: {e}")
            raise
    
    def execute_transaction(self, queries: List[Tuple[str, Tuple]]) -> bool:
        """Execute multiple queries in a transaction"""
        start_time = time.time()
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Begin transaction
                cursor.execute("BEGIN")
                
                try:
                    for query, params in queries:
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)
                    
                    conn.commit()
                    
                    # Clear cache for write operations
                    for query, _ in queries:
                        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                            self._invalidate_cache(query)
                    
                    # Update statistics
                    execution_time = time.time() - start_time
                    self._update_query_stats("TRANSACTION", execution_time, True)
                    
                    return True
                    
                except Exception as e:
                    conn.rollback()
                    raise e
                    
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats("TRANSACTION", execution_time, False)
            logger.error(f"Transaction execution error: {e}")
            raise
    
    def _update_query_stats(self, query: str, execution_time: float, success: bool):
        """Update query execution statistics"""
        self.query_stats.total_queries += 1
        self.query_times.append(execution_time)
        
        if success:
            self.query_stats.successful_queries += 1
        else:
            self.query_stats.failed_queries += 1
        
        self.query_stats.total_execution_time += execution_time
        self.query_stats.average_execution_time = (
            self.query_stats.total_execution_time / self.query_stats.total_queries
        )
        
        # Track slow queries
        if execution_time > self.performance_threshold:
            self.query_stats.slow_queries += 1
            self.slow_queries.append({
                'query': query[:100] + "..." if len(query) > 100 else query,
                'execution_time': execution_time,
                'timestamp': time.time()
            })
            
            # Keep only recent slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-50:]
        
        # Update cache hit rate
        cache_stats = self.query_cache.get_stats()
        self.query_stats.cache_hit_rate = cache_stats['hit_rate']
    
    def _invalidate_cache(self, query: str):
        """Invalidate cache entries based on query"""
        # For write operations, clear entire cache for simplicity
        # In production, you might want more sophisticated cache invalidation
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            self.query_cache.clear()
    
    def optimize_database(self):
        """Optimize database performance"""
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Analyze database
                cursor.execute("ANALYZE")
                
                # Vacuum database
                cursor.execute("VACUUM")
                
                # Update statistics
                cursor.execute("PRAGMA optimize")
                
                conn.commit()
                
                logger.info("Database optimization completed")
                
        except Exception as e:
            logger.error(f"Database optimization error: {e}")
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        connection_stats = self.connection_pool.get_stats()
        cache_stats = self.query_cache.get_stats()
        
        return {
            'connection_stats': {
                'total_connections': connection_stats.total_connections,
                'active_connections': connection_stats.active_connections,
                'peak_connections': connection_stats.peak_connections,
                'connections_created': connection_stats.connections_created,
                'connections_closed': connection_stats.connections_closed,
                'average_connection_time': connection_stats.average_connection_time,
                'connection_errors': connection_stats.connection_errors
            },
            'query_stats': {
                'total_queries': self.query_stats.total_queries,
                'successful_queries': self.query_stats.successful_queries,
                'failed_queries': self.query_stats.failed_queries,
                'average_execution_time': self.query_stats.average_execution_time,
                'slow_queries': self.query_stats.slow_queries,
                'cache_hit_rate': self.query_stats.cache_hit_rate
            },
            'cache_stats': cache_stats,
            'recent_slow_queries': self.slow_queries[-10:] if self.slow_queries else []
        }
    
    def _start_background_optimization(self):
        """Start background optimization tasks"""
        def optimization_worker():
            while self.monitoring_enabled:
                try:
                    # Optimize connection pool every 5 minutes
                    time.sleep(300)
                    self.connection_pool.optimize_pool()
                    
                    # Clear old cache entries
                    if len(self.query_cache.cache) > self.query_cache.max_size * 0.8:
                        # Clear 20% of cache
                        for _ in range(int(self.query_cache.max_size * 0.2)):
                            self.query_cache._evict_lru()
                    
                except Exception as e:
                    logger.warning(f"Background optimization error: {e}")
        
        optimization_thread = threading.Thread(target=optimization_worker, daemon=True)
        optimization_thread.start()
    
    def shutdown(self):
        """Shutdown the database manager"""
        self.monitoring_enabled = False
        self.connection_pool.shutdown()
        self.query_cache.clear()
        logger.info("Enhanced database manager shutdown complete")

# Global instance
enhanced_db_manager = EnhancedDatabaseManager(DB_PATH)

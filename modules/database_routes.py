"""
Database Routes - API Layer for Database Operations
This module provides a clean, organized API layer for all database operations
with proper error handling, caching, and performance tracking.

Created: July 17, 2025
"""

import sqlite3
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from modules.db_manager import get_connection, ConnectionContext
from modules.logger import logger

class DatabaseRoutes:
    """Centralized database routes with caching and performance monitoring"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.performance_stats = {
            'query_count': 0,
            'cache_hits': 0,
            'slow_queries': [],
            'total_execution_time': 0
        }
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available and not expired"""
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if time.time() - cache_data['timestamp'] < self.cache_timeout:
                self.performance_stats['cache_hits'] += 1
                return cache_data['result']
            else:
                # Remove expired cache
                del self.cache[cache_key]
        return None
    
    def _set_cache_result(self, cache_key: str, result: Any):
        """Cache the result with timestamp"""
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def _execute_query(self, query: str, params: Tuple = None, use_cache: bool = True) -> List[Any]:
        """Execute query with performance tracking and caching"""
        start_time = time.time()
        
        # Create cache key
        cache_key = f"{query}_{params}" if use_cache else None
        
        # Check cache first
        if use_cache and cache_key:
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
        
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                result = cursor.fetchall()
                
                # Cache the result
                if use_cache and cache_key:
                    self._set_cache_result(cache_key, result)
                
                # Track performance
                execution_time = time.time() - start_time
                self.performance_stats['query_count'] += 1
                self.performance_stats['total_execution_time'] += execution_time
                
                # Track slow queries
                if execution_time > 1.0:  # 1 second threshold
                    self.performance_stats['slow_queries'].append({
                        'query': query[:100] + "..." if len(query) > 100 else query,
                        'execution_time': execution_time,
                        'timestamp': time.time(),
                        'params': str(params) if params else None
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Database query error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def _execute_write_query(self, query: str, params: Tuple = None) -> int:
        """Execute write query (INSERT, UPDATE, DELETE) and return affected rows"""
        try:
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Database write error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    # ===== PRODUCTS ROUTES =====
    
    def get_products(self, page: int = 1, limit: int = 50, search: str = None, 
                    category: str = None, low_stock_only: bool = False) -> Dict[str, Any]:
        """Get products with pagination and filtering"""
        try:
            offset = (page - 1) * limit
            
            # Build WHERE conditions
            where_conditions = ["1=1"]
            params = []
            
            if search:
                where_conditions.append("(Name LIKE ? OR Barcode LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            if category:
                where_conditions.append("Category = ?")
                params.append(category)
            
            if low_stock_only:
                where_conditions.append("Stock <= 10")  # Low stock threshold
            
            where_clause = " AND ".join(where_conditions)
            
            # Get products
            query = f"""
                SELECT ProductID, Name, SellingPrice, Stock, Category, Barcode, 
                       CASE WHEN Stock <= 10 THEN 'Low Stock' ELSE 'In Stock' END as StockStatus
                FROM Products 
                WHERE {where_clause}
                ORDER BY Name
                LIMIT ? OFFSET ?
            """
            
            products = self._execute_query(query, tuple(params + [limit, offset]))
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM Products WHERE {where_clause}"
            count_result = self._execute_query(count_query, tuple(params))
            total_count = count_result[0][0] if count_result else 0
            
            return {
                'data': products,
                'total_count': total_count,
                'page': page,
                'limit': limit,
                'total_pages': (total_count + limit - 1) // limit if total_count > 0 else 1
            }
            
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return {
                'data': [],
                'total_count': 0,
                'page': page,
                'limit': limit,
                'total_pages': 1
            }
    
    def create_product(self, name: str, price: float, stock: int, category: str, 
                      barcode: str = None) -> int:
        """Create new product"""
        try:
            query = """
                INSERT INTO Products (Name, SellingPrice, Stock, Category, Barcode)
                VALUES (?, ?, ?, ?, ?)
            """
            
            with ConnectionContext() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (name, price, stock, category, barcode))
                conn.commit()
                
                # Clear cache for products
                self._clear_cache_pattern("SELECT * FROM Products")
                
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            raise
    
    def update_product(self, product_id: int, name: str = None, price: float = None, 
                      stock: int = None, category: str = None, barcode: str = None) -> bool:
        """Update existing product"""
        try:
            # Build dynamic UPDATE query
            update_fields = []
            params = []
            
            if name is not None:
                update_fields.append("Name = ?")
                params.append(name)
            
            if price is not None:
                update_fields.append("SellingPrice = ?")
                params.append(price)
            
            if stock is not None:
                update_fields.append("Stock = ?")
                params.append(stock)
            
            if category is not None:
                update_fields.append("Category = ?")
                params.append(category)
            
            if barcode is not None:
                update_fields.append("Barcode = ?")
                params.append(barcode)
            
            if not update_fields:
                return False
            
            params.append(product_id)
            
            query = f"""
                UPDATE Products 
                SET {', '.join(update_fields)}
                WHERE ProductID = ?
            """
            
            rows_affected = self._execute_write_query(query, tuple(params))
            
            # Clear cache for products
            self._clear_cache_pattern("SELECT * FROM Products")
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            raise
    
    def delete_product(self, product_id: int) -> bool:
        """Delete product"""
        try:
            query = "DELETE FROM Products WHERE ProductID = ?"
            rows_affected = self._execute_write_query(query, (product_id,))
            
            # Clear cache for products
            self._clear_cache_pattern("SELECT * FROM Products")
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            raise
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get single product by ID"""
        try:
            query = "SELECT * FROM Products WHERE ProductID = ?"
            result = self._execute_query(query, (product_id,))
            
            if result:
                product = result[0]
                return {
                    'id': product[0],
                    'name': product[1],
                    'selling_price': product[2],
                    'buying_price': product[3],
                    'stock': product[4],
                    'category': product[5],
                    'barcode': product[6] if len(product) > 6 else None,
                    'qr_code': product[7] if len(product) > 7 else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None
    
    def search_products_fast(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fast product search for autocomplete"""
        try:
            query = """
                SELECT ProductID, Name, SellingPrice, Stock, Category, Barcode
                FROM Products 
                WHERE Name LIKE ? OR Barcode LIKE ?
                ORDER BY Name
                LIMIT ?
            """
            
            results = self._execute_query(
                query, 
                (f"%{search_term}%", f"%{search_term}%", limit),
                use_cache=False  # Don't cache fast searches
            )
            
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'price': row[2],
                    'stock': row[3],
                    'category': row[4],
                    'barcode': row[5],
                    'display': f"{row[1]} - {row[5] or 'No barcode'} (Stock: {row[3]})"
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error in fast product search: {e}")
            return []
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Get products with low stock"""
        try:
            query = """
                SELECT ProductID, Name, SellingPrice, Stock, Category, Barcode
                FROM Products 
                WHERE Stock <= ?
                ORDER BY Stock ASC, Name
            """
            
            results = self._execute_query(query, (threshold,))
            
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'price': row[2],
                    'stock': row[3],
                    'category': row[4],
                    'barcode': row[5]
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            return []
    
    def update_stock(self, product_id: int, new_stock: int) -> bool:
        """Update product stock"""
        try:
            query = "UPDATE Products SET Stock = ? WHERE ProductID = ?"
            rows_affected = self._execute_write_query(query, (new_stock, product_id))
            
            # Clear cache for products
            self._clear_cache_pattern("SELECT * FROM Products")
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating stock for product {product_id}: {e}")
            raise
    
    # ===== CATEGORIES ROUTES =====
    
    def get_categories(self) -> List[str]:
        """Get all product categories"""
        try:
            query = "SELECT DISTINCT Category FROM Products WHERE Category IS NOT NULL ORDER BY Category"
            results = self._execute_query(query)
            
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_category_stats(self) -> List[Dict[str, Any]]:
        """Get category statistics"""
        try:
            query = """
                SELECT Category, COUNT(*) as ProductCount, SUM(Stock) as TotalStock
                FROM Products 
                WHERE Category IS NOT NULL
                GROUP BY Category
                ORDER BY ProductCount DESC
            """
            
            results = self._execute_query(query)
            
            return [
                {
                    'category': row[0],
                    'product_count': row[1],
                    'total_stock': row[2]
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting category stats: {e}")
            return []
    
    # ===== UTILITY METHODS =====
    
    def _clear_cache_pattern(self, pattern: str):
        """Clear cache entries matching a pattern"""
        keys_to_remove = [key for key in self.cache.keys() if pattern in key]
        for key in keys_to_remove:
            del self.cache[key]
    
    def clear_cache(self):
        """Clear all cache"""
        self.cache.clear()
        logger.info("Database cache cleared")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_execution_time = (
            self.performance_stats['total_execution_time'] / 
            self.performance_stats['query_count']
        ) if self.performance_stats['query_count'] > 0 else 0
        
        return {
            'query_count': self.performance_stats['query_count'],
            'cache_hits': self.performance_stats['cache_hits'],
            'cache_hit_rate': (
                self.performance_stats['cache_hits'] / 
                self.performance_stats['query_count'] * 100
            ) if self.performance_stats['query_count'] > 0 else 0,
            'slow_queries_count': len(self.performance_stats['slow_queries']),
            'avg_execution_time': avg_execution_time,
            'recent_slow_queries': self.performance_stats['slow_queries'][-10:]  # Last 10
        }
    
    def optimize_performance(self):
        """Optimize database performance"""
        try:
            # Clear old cache entries
            current_time = time.time()
            expired_keys = [
                key for key, data in self.cache.items()
                if current_time - data['timestamp'] > self.cache_timeout
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            # Reset slow queries list if too long
            if len(self.performance_stats['slow_queries']) > 100:
                self.performance_stats['slow_queries'] = self.performance_stats['slow_queries'][-50:]
            
            logger.info(f"Performance optimization completed. Cleared {len(expired_keys)} expired cache entries.")
            
        except Exception as e:
            logger.error(f"Error optimizing performance: {e}")

# Create global instance
db_routes = DatabaseRoutes()

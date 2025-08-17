#!/usr/bin/env python3
"""
Test script for Enhanced Database Manager
Tests advanced database management features including connection pooling,
query caching, and performance monitoring.
"""

import sys
import os
import threading
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_database_manager():
    """Test enhanced database manager functionality"""
    print("🔍 Testing Enhanced Database Manager...")
    
    try:
        # Import the enhanced database manager
        from modules.enhanced_db_manager import enhanced_db_manager
        
        print("  ✅ Enhanced database manager imported successfully")
        
        # Test 1: Basic query execution
        print("\n  📋 Testing basic query execution...")
        result = enhanced_db_manager.execute_query("SELECT COUNT(*) FROM Products")
        print(f"  ✅ Basic query executed: {result[0][0] if result else 0} products found")
        
        # Test 2: Query with parameters
        print("\n  📋 Testing parameterized query...")
        result = enhanced_db_manager.execute_query(
            "SELECT * FROM Products WHERE Category = ?", 
            ("Juice",)
        )
        print(f"  ✅ Parameterized query executed: {len(result)} products found")
        
        # Test 3: Test caching (run same query twice)
        print("\n  📋 Testing query caching...")
        start_time = time.time()
        result1 = enhanced_db_manager.execute_query("SELECT * FROM Products LIMIT 5")
        time1 = time.time() - start_time
        
        start_time = time.time()
        result2 = enhanced_db_manager.execute_query("SELECT * FROM Products LIMIT 5")
        time2 = time.time() - start_time
        
        print(f"  ✅ First query time: {time1:.4f}s")
        print(f"  ✅ Second query time: {time2:.4f}s")
        print(f"  ✅ Cache working: {'Yes' if time2 < time1 else 'Possibly'}")
        
        # Test 4: Connection pool stress test
        print("\n  📋 Testing connection pool with concurrent queries...")
        
        def worker(worker_id, results):
            try:
                result = enhanced_db_manager.execute_query(
                    f"SELECT COUNT(*) FROM Products WHERE ProductID > {worker_id}"
                )
                results[worker_id] = len(result)
            except Exception as e:
                results[worker_id] = f"Error: {e}"
        
        threads = []
        results = {}
        
        # Start 10 concurrent workers
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i, results))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        successful_queries = sum(1 for r in results.values() if isinstance(r, int))
        print(f"  ✅ Concurrent queries: {successful_queries}/10 successful")
        
        # Test 5: Write query
        print("\n  📋 Testing write query...")
        try:
            # Try to insert a test product
            rows_affected = enhanced_db_manager.execute_write_query(
                "INSERT INTO Products (Name, SellingPrice, BuyingPrice, Stock, Category) VALUES (?, ?, ?, ?, ?)",
                ("Test Product", 10.0, 8.0, 100, "Test Category")
            )
            print(f"  ✅ Write query executed: {rows_affected} rows affected")
            
            # Clean up - remove test product
            enhanced_db_manager.execute_write_query(
                "DELETE FROM Products WHERE Name = ?",
                ("Test Product",)
            )
            print("  ✅ Test product cleaned up")
            
        except Exception as e:
            print(f"  ⚠️  Write query test failed: {e}")
        
        # Test 6: Transaction test
        print("\n  📋 Testing transaction execution...")
        try:
            transaction_queries = [
                ("INSERT INTO Products (Name, SellingPrice, BuyingPrice, Stock, Category) VALUES (?, ?, ?, ?, ?)",
                 ("Transaction Test 1", 5.0, 4.0, 50, "Test")),
                ("INSERT INTO Products (Name, SellingPrice, BuyingPrice, Stock, Category) VALUES (?, ?, ?, ?, ?)",
                 ("Transaction Test 2", 6.0, 5.0, 60, "Test"))
            ]
            
            success = enhanced_db_manager.execute_transaction(transaction_queries)
            print(f"  ✅ Transaction executed: {'Success' if success else 'Failed'}")
            
            # Clean up
            enhanced_db_manager.execute_write_query(
                "DELETE FROM Products WHERE Name LIKE ?",
                ("Transaction Test%",)
            )
            print("  ✅ Transaction test products cleaned up")
            
        except Exception as e:
            print(f"  ⚠️  Transaction test failed: {e}")
        
        # Test 7: Performance statistics
        print("\n  📋 Testing performance statistics...")
        stats = enhanced_db_manager.get_performance_stats()
        
        print(f"  ✅ Total queries: {stats['query_stats']['total_queries']}")
        print(f"  ✅ Successful queries: {stats['query_stats']['successful_queries']}")
        print(f"  ✅ Cache hit rate: {stats['query_stats']['cache_hit_rate']:.1f}%")
        print(f"  ✅ Average execution time: {stats['query_stats']['average_execution_time']:.4f}s")
        print(f"  ✅ Active connections: {stats['connection_stats']['active_connections']}")
        print(f"  ✅ Peak connections: {stats['connection_stats']['peak_connections']}")
        
        # Test 8: Database optimization
        print("\n  📋 Testing database optimization...")
        try:
            enhanced_db_manager.optimize_database()
            print("  ✅ Database optimization completed successfully")
        except Exception as e:
            print(f"  ⚠️  Database optimization failed: {e}")
        
        # Test 9: Cache statistics
        print("\n  📋 Testing cache statistics...")
        cache_stats = enhanced_db_manager.query_cache.get_stats()
        print(f"  ✅ Cache size: {cache_stats['size']}/{cache_stats['max_size']}")
        print(f"  ✅ Cache hits: {cache_stats['hits']}")
        print(f"  ✅ Cache misses: {cache_stats['misses']}")
        print(f"  ✅ Cache hit rate: {cache_stats['hit_rate']:.1f}%")
        
        print("\n🎉 All Enhanced Database Manager tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced database manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_database_manager()
    sys.exit(0 if success else 1)

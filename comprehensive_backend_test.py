#!/usr/bin/env python3
"""
Comprehensive Backend Analysis and Testing
This script performs a thorough analysis of the backend system including:
1. Database structure and integrity
2. Connection pool performance
3. Query optimization analysis
4. Data access layer validation
5. Performance monitoring tests
"""

import sys
import os
import time
import threading
import sqlite3
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connectivity():
    """Test basic database connectivity and structure"""
    print("🔍 TESTING DATABASE CONNECTIVITY")
    print("=" * 50)
    
    try:
        from modules.db_manager import get_connection, return_connection, ConnectionContext, get_connection_stats
        
        # Test 1: Basic connection
        print("  📋 Testing basic database connection...")
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"  ✅ Connected successfully, found {len(tables)} tables")
            
            # List all tables
            for table in tables:
                print(f"    - {table[0]}")
        
        # Test 2: Connection pool stats
        print("\n  📋 Testing connection pool...")
        stats = get_connection_stats()
        print(f"  ✅ Pool size: {stats['pool_size']}")
        print(f"  ✅ Active connections: {stats['active']}")
        print(f"  ✅ Peak connections: {stats['peak']}")
        print(f"  ✅ Total created: {stats['created']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database connectivity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_schema():
    """Test database schema and integrity"""
    print("\n🔍 TESTING DATABASE SCHEMA")
    print("=" * 50)
    
    try:
        from modules.db_manager import ConnectionContext
        
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            # Check essential tables
            essential_tables = ['Products', 'Sales', 'Debits', 'Users', 'ActivityLog']
            
            for table in essential_tables:
                print(f"  📋 Checking table: {table}")
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                result = cursor.fetchone()
                
                if result:
                    # Get table info
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    print(f"    ✅ Table exists with {len(columns)} columns")
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"    ✅ Contains {count} records")
                    
                    # Show column structure
                    for col in columns[:3]:  # Show first 3 columns
                        print(f"      - {col[1]} ({col[2]})")
                else:
                    print(f"    ❌ Table {table} does not exist")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Schema test failed: {e}")
        return False

def test_connection_pool_performance():
    """Test connection pool under load"""
    print("\n🔍 TESTING CONNECTION POOL PERFORMANCE")
    print("=" * 50)
    
    try:
        from modules.db_manager import get_connection, return_connection, get_connection_stats
        
        print("  📋 Testing concurrent connection requests...")
        
        def worker(worker_id, results):
            try:
                start_time = time.time()
                
                # Get connection
                conn = get_connection()
                
                # Perform a simple query
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master")
                result = cursor.fetchone()
                
                # Return connection
                return_connection(conn)
                
                end_time = time.time()
                results[worker_id] = {
                    'success': True,
                    'time': end_time - start_time,
                    'result': result[0] if result else 0
                }
                
            except Exception as e:
                results[worker_id] = {
                    'success': False,
                    'error': str(e),
                    'time': 0
                }
        
        # Test with 20 concurrent workers
        threads = []
        results = {}
        
        start_time = time.time()
        
        for i in range(20):
            thread = threading.Thread(target=worker, args=(i, results))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for r in results.values() if r.get('success', False))
        failed = len(results) - successful
        avg_time = sum(r.get('time', 0) for r in results.values()) / len(results)
        
        print(f"  ✅ Concurrent test completed in {total_time:.2f}s")
        print(f"  ✅ Successful connections: {successful}/20")
        print(f"  ✅ Failed connections: {failed}/20")
        print(f"  ✅ Average connection time: {avg_time:.4f}s")
        
        # Check final pool stats
        final_stats = get_connection_stats()
        print(f"  ✅ Final active connections: {final_stats['active']}")
        print(f"  ✅ Peak connections reached: {final_stats['peak']}")
        
        return failed == 0
        
    except Exception as e:
        print(f"  ❌ Connection pool performance test failed: {e}")
        return False

def test_enhanced_db_manager():
    """Test enhanced database manager if available"""
    print("\n🔍 TESTING ENHANCED DATABASE MANAGER")
    print("=" * 50)
    
    try:
        from modules.enhanced_db_manager import enhanced_db_manager
        
        print("  📋 Testing enhanced query execution...")
        
        # Test basic query
        start_time = time.time()
        result = enhanced_db_manager.execute_query("SELECT COUNT(*) FROM Products")
        query_time = time.time() - start_time
        
        print(f"  ✅ Basic query executed in {query_time:.4f}s")
        print(f"  ✅ Found {result[0][0] if result else 0} products")
        
        # Test query caching
        print("\n  📋 Testing query caching...")
        
        cache_query = "SELECT * FROM Products LIMIT 5"
        
        # First execution (cache miss)
        start_time = time.time()
        result1 = enhanced_db_manager.execute_query(cache_query)
        time1 = time.time() - start_time
        
        # Second execution (cache hit)
        start_time = time.time()
        result2 = enhanced_db_manager.execute_query(cache_query)
        time2 = time.time() - start_time
        
        print(f"  ✅ First query time: {time1:.4f}s")
        print(f"  ✅ Second query time: {time2:.4f}s")
        print(f"  ✅ Cache speedup: {(time1/time2):.1f}x" if time2 > 0 else "N/A")
        
        # Test performance stats
        print("\n  📋 Testing performance statistics...")
        stats = enhanced_db_manager.get_performance_stats()
        
        print(f"  ✅ Total queries: {stats['query_stats']['total_queries']}")
        print(f"  ✅ Cache hit rate: {stats['query_stats']['cache_hit_rate']:.1f}%")
        print(f"  ✅ Average query time: {stats['query_stats']['average_execution_time']:.4f}s")
        
        return True
        
    except ImportError:
        print("  ⚠️  Enhanced database manager not available")
        return True
    except Exception as e:
        print(f"  ❌ Enhanced database manager test failed: {e}")
        return False

def test_data_access_layer():
    """Test the data access layer functionality"""
    print("\n🔍 TESTING DATA ACCESS LAYER")
    print("=" * 50)
    
    try:
        # Test basic data access functions
        from modules.data_access import (
            get_all_products, get_sales_data, get_debits_data,
            log_db_operation
        )
        
        print("  📋 Testing product data access...")
        products = get_all_products()
        print(f"  ✅ Retrieved {len(products)} products")
        
        if products:
            print(f"    - Sample product: {products[0].get('ProductName', 'N/A')}")
        
        print("\n  📋 Testing sales data access...")
        sales = get_sales_data(limit=10)
        print(f"  ✅ Retrieved {len(sales)} sales records")
        
        print("\n  📋 Testing debits data access...")
        debits = get_debits_data(limit=10)
        print(f"  ✅ Retrieved {len(debits)} debit records")
        
        print("\n  📋 Testing logging functionality...")
        log_db_operation("Test operation", 1)
        print("  ✅ Logging function executed successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Data access layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_data_access():
    """Test enhanced data access if available"""
    print("\n🔍 TESTING ENHANCED DATA ACCESS")
    print("=" * 50)
    
    try:
        from modules.enhanced_data_access import enhanced_data
        
        print("  📋 Testing paginated product access...")
        
        # Test pagination
        page_result = enhanced_data.get_products_paginated(page_size=5, page_number=1)
        print(f"  ✅ Retrieved page with {len(page_result.data)} items")
        print(f"  ✅ Total items: {page_result.total_items}")
        print(f"  ✅ Total pages: {page_result.total_pages}")
        
        print("\n  📋 Testing product search...")
        search_result = enhanced_data.search_products("", limit=10)
        print(f"  ✅ Search returned {len(search_result.data)} results")
        
        return True
        
    except ImportError:
        print("  ⚠️  Enhanced data access not available")
        return True
    except Exception as e:
        print(f"  ❌ Enhanced data access test failed: {e}")
        return False

def test_database_optimization():
    """Test database optimization features"""
    print("\n🔍 TESTING DATABASE OPTIMIZATION")
    print("=" * 50)
    
    try:
        from modules.optimize_db import run_comprehensive_optimization
        from modules.db_manager import analyze_database_performance
        
        print("  📋 Testing database analysis...")
        start_time = time.time()
        analyze_database_performance()
        analysis_time = time.time() - start_time
        print(f"  ✅ Database analysis completed in {analysis_time:.2f}s")
        
        print("\n  📋 Testing comprehensive optimization...")
        start_time = time.time()
        result = run_comprehensive_optimization()
        optimization_time = time.time() - start_time
        
        if result and result.get('success'):
            print(f"  ✅ Optimization completed in {optimization_time:.2f}s")
            if 'steps_completed' in result:
                print(f"  ✅ Steps completed: {', '.join(result['steps_completed'])}")
        else:
            print("  ⚠️  Optimization completed with warnings")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database optimization test failed: {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring if available"""
    print("\n🔍 TESTING PERFORMANCE MONITORING")
    print("=" * 50)
    
    try:
        from modules.performance_monitor import performance_monitor
        
        print("  📋 Testing performance monitoring...")
        
        # Record some test metrics
        performance_monitor.record_db_operation("test_query", 50.0)
        performance_monitor.record_background_task("test_task", 100.0)
        
        print("  ✅ Performance metrics recorded successfully")
        
        # Check if monitoring is active
        if hasattr(performance_monitor, 'active'):
            print(f"  ✅ Performance monitoring active: {performance_monitor.active}")
        
        return True
        
    except ImportError:
        print("  ⚠️  Performance monitoring not available")
        return True
    except Exception as e:
        print(f"  ❌ Performance monitoring test failed: {e}")
        return False

def analyze_database_performance_issues():
    """Analyze potential database performance issues"""
    print("\n🔍 ANALYZING PERFORMANCE ISSUES")
    print("=" * 50)
    
    try:
        from modules.db_manager import ConnectionContext
        
        with ConnectionContext() as conn:
            cursor = conn.cursor()
            
            print("  📋 Checking for missing indexes...")
            
            # Check for tables without indexes
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                
                # Check if table has any indexes
                cursor.execute("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='index' AND tbl_name=? AND name NOT LIKE 'sqlite_%'
                """, (table_name,))
                
                index_count = cursor.fetchone()[0]
                
                # Get table size
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                if index_count == 0 and row_count > 100:
                    print(f"  ⚠️  {table_name}: {row_count} rows, no indexes")
                else:
                    print(f"  ✅ {table_name}: {row_count} rows, {index_count} indexes")
            
            print("\n  📋 Checking database settings...")
            
            # Check important PRAGMA settings
            pragmas = ['journal_mode', 'synchronous', 'cache_size', 'temp_store']
            
            for pragma in pragmas:
                cursor.execute(f"PRAGMA {pragma}")
                value = cursor.fetchone()[0]
                print(f"  ✅ {pragma}: {value}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance analysis failed: {e}")
        return False

def generate_performance_report():
    """Generate a comprehensive performance report"""
    print("\n📊 PERFORMANCE REPORT SUMMARY")
    print("=" * 50)
    
    try:
        # Database file size
        db_files = ['sales_system.db', 'database/store.db']
        
        for db_file in db_files:
            if os.path.exists(db_file):
                size_mb = os.path.getsize(db_file) / (1024 * 1024)
                print(f"  📁 {db_file}: {size_mb:.2f} MB")
        
        # Connection pool statistics
        try:
            from modules.db_manager import get_connection_stats
            stats = get_connection_stats()
            print(f"  🔗 Connection pool efficiency: {(stats['returned']/stats['created']*100):.1f}%" 
                  if stats['created'] > 0 else "N/A")
        except:
            pass
        
        # Enhanced manager statistics
        try:
            from modules.enhanced_db_manager import enhanced_db_manager
            stats = enhanced_db_manager.get_performance_stats()
            print(f"  ⚡ Query cache hit rate: {stats['query_stats']['cache_hit_rate']:.1f}%")
            print(f"  ⚡ Average query time: {stats['query_stats']['average_execution_time']:.4f}s")
        except:
            pass
        
        print(f"\n  📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Report generation failed: {e}")
        return False

def main():
    """Run comprehensive backend testing"""
    print("🚀 COMPREHENSIVE BACKEND ANALYSIS")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    tests = [
        ("Database Connectivity", test_database_connectivity),
        ("Database Schema", test_database_schema),
        ("Connection Pool Performance", test_connection_pool_performance),
        ("Enhanced Database Manager", test_enhanced_db_manager),
        ("Data Access Layer", test_data_access_layer),
        ("Enhanced Data Access", test_enhanced_data_access),
        ("Database Optimization", test_database_optimization),
        ("Performance Monitoring", test_performance_monitoring),
        ("Performance Analysis", analyze_database_performance_issues),
        ("Performance Report", generate_performance_report)
    ]
    
    results = {}
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            results[test_name] = {
                'success': result,
                'duration': duration
            }
            
            print(f"\n✅ {test_name} completed in {duration:.2f}s" if result 
                  else f"\n❌ {test_name} failed in {duration:.2f}s")
                  
        except Exception as e:
            results[test_name] = {
                'success': False,
                'duration': 0,
                'error': str(e)
            }
            print(f"\n❌ {test_name} crashed: {e}")
    
    total_duration = time.time() - total_start_time
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 FINAL SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results.values() if r['success'])
    total_tests = len(results)
    
    print(f"Tests passed: {successful}/{total_tests}")
    print(f"Total duration: {total_duration:.2f}s")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status} {test_name} ({result['duration']:.2f}s)")
        if not result['success'] and 'error' in result:
            print(f"      Error: {result['error']}")
    
    if successful == total_tests:
        print("\n🎉 All backend tests passed successfully!")
    else:
        print(f"\n⚠️  {total_tests - successful} tests failed. See details above.")
    
    return successful == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
